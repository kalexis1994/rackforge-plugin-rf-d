import copy
from dataclasses import replace
from decimal import Decimal,localcontext
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from bjt_charge_reference import History as DeviceHistory
from loudness_latch_charge_reference import History
from loudness_latch_increment_reference import IncrementNetwork,pair
from loudness_latch_increment_probes import unpack,publication_check,state_hash
from loudness_latch_increment_time import Policy,trial,nodes,junctions,error


class IncrementCoordinates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/"evidence/loudness_latch_increment_probes.json").read_text())
        cls.network=IncrementNetwork(200,model_parameters(1,"finite_transit"))

    def test_recorded_failure_closes_with_both_jacobians_without_gate_relaxation(self):
        n=self.network
        for row in self.report["repaired_interval"]:
            old=unpack(n,row["old"],10.);before=copy.deepcopy(old)
            new,d=n.step(old,10.,row["dt_s"],use_fd=row["use_fd"])
            self.assertEqual(new,unpack(n,row["new"],10.))
            self.assertLess(d["max_kcl_a"],1e-11);self.assertLess(d["correction_v"],1e-8)
            self.assertNotEqual(new.node_low_v[92],0.)
            self.assertEqual(new.capacitor_pairs_v[18],(new.joint.node_v[92],new.node_low_v[92]))
            self.assertEqual(old,before)
            delta=np.array(d["increment_v"])
            _,j=n.increment_evaluator(10.,old,row["dt_s"])(delta)
            _,fd=n.increment_evaluator(10.,old,row["dt_s"])(delta,use_fd=True)
            self.assertLess(np.max(np.abs(j-fd)/(1+np.abs(j))),1e-8)

    def test_all_published_linear_charge_and_series_branch_equations(self):
        n=self.network
        rows=self.report["repaired_interval"]+self.report["continuation"]+[self.report["ordinary_interval"]]
        for row in rows:
            old=unpack(n,row["old"],0. if row is self.report["ordinary_interval"] else 10.)
            new=unpack(n,row["new"],10.)
            check=publication_check(n,old,new,10.,row["dt_s"],row["diagnostics"])
            self.assertEqual(check,row["publication"])
            self.assertTrue(check["round_trip_exact"])
            self.assertLess(check["max_published_kcl_a"],1e-11)
            self.assertLess(check["max_serialized_replay_kcl_a"],1e-11)
            self.assertLess(check["max_current_difference_a"],1e-15)
            self.assertLess(check["max_branch_equation_error_v"],1e-14)
        self.assertLess(self.report["ordinary_interval"]["max_legacy_node_difference_v"],1e-8)

    def test_discarding_timing_tail_breaks_the_recorded_publication_gate(self):
        row=self.report["repaired_interval"][0];n=self.network
        old=unpack(n,row["old"],10.);new=unpack(n,row["new"],10.)
        d=row["diagnostics"]["increment_v"].copy()
        d[92]=new.joint.node_v[92]-old.joint.node_v[92]
        r,_=n.increment_evaluator(10.,old,row["dt_s"])(d,False)
        self.assertGreater(abs(r[92]),1e-11)
        with localcontext() as ctx:
            ctx.prec=80
            exact=Decimal.from_float(old.joint.node_v[92])+Decimal.from_float(row["diagnostics"]["increment_v"][92])
            stored=sum(map(Decimal.from_float,new.capacitor_pairs_v[18]))
            self.assertLess(abs(exact-stored),Decimal("1e-30"))

    def test_continuation_preserves_complete_memory_and_snapshot(self):
        n=self.network
        for row in self.report["continuation"]:
            old=unpack(n,row["old"],10.);before=state_hash(old)
            new,d=n.step(old,10.,row["dt_s"])
            self.assertEqual(new,unpack(n,row["new"],10.))
            self.assertEqual(state_hash(old),before)
            self.assertLess(d["max_kcl_a"],1e-11)

    def test_wrong_or_truncated_history_and_old_coordinate_entry_are_rejected(self):
        n=self.network;old=unpack(n,self.report["repaired_interval"][0]["old"],10.)
        for bad in (replace(old,node_low_v=()),replace(old,capacitor_pairs_v=old.capacitor_pairs_v[:-1]),
                    replace(old,circuit_signature=()),replace(old,node_low_v=(float("nan"),)*94)):
            with self.assertRaises(ValueError):n.step(bad,10.,1e-10)
        with self.assertRaises(ValueError):n.evaluator(10.,old,1e-10)
        with self.assertRaises(ValueError):n.step(old,10.,0.)

    def test_v2_metric_is_independent_of_arbitrary_common_charge_origin(self):
        n=self.network;a=unpack(n,self.report["repaired_interval"][0]["new"],10.)
        b=unpack(n,self.report["continuation"][0]["new"],10.)
        ratios=(error(nodes(a),nodes(b),1e-4,1e-4),error(junctions(n,a),junctions(n,b),1e-4,1e-4))
        for offset in (-1e-9,0.,1e-9):
            def shift(s):
                return replace(s,latch=History(s.latch.layout,tuple(DeviceHistory(d.parameters,d.be_c+offset,d.bc_c+offset) for d in s.latch.devices)))
            x,y=shift(a),shift(b)
            self.assertEqual((error(nodes(x),nodes(y),1e-4,1e-4),error(junctions(n,x),junctions(n,y),1e-4,1e-4)),ratios)
        p=Policy(1e-4,1e-4,1e-4,1e-4,.05,.1,1e-4,1e-12,2000)
        previous=state_hash(a)
        result,diag,_=trial(n,a,10.,1e-10,p,1e7)
        self.assertIsNotNone(result);self.assertEqual(state_hash(a),previous)
        self.assertEqual(diag["error_metric_version"],"node-and-junction-voltage/v2")
        with self.assertRaises(ValueError):replace(p,junction_abs_v=0.)

    def test_pinned_sources_and_historical_rejection_remain_distinct(self):
        for path,h in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        self.assertTrue(self.report["original_rejection_retained"])
        self.assertEqual(self.report["history_reset_count"],0)
        for flag in ("physical_switching_admitted","temporal_refinement_admitted","audio_admitted"):
            self.assertFalse(self.report[flag])


if __name__=="__main__":unittest.main()
