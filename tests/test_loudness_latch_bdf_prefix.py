import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_latch_bdf_prefix_audit import prefix_comparison,generate
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack,publication_check
from loudness_latch_bdf_survey import state_hash
from bjt_charge_ngspice_probes import model_parameters


class PrefixSensitivity(unittest.TestCase):
    def test_union_interpolation_preserves_a_known_voltage_offset(self):
        ta=np.array([0.,1e-4,.001,.0023,.003])
        tb=np.array([0.,.5e-4,.0005,.0015,.0023,.003])
        va=np.tile((100*ta)[:,None],(1,94));vb=np.tile((100*tb+.0005)[:,None],(1,94))
        r=prefix_comparison((ta,va),(tb,vb),92)
        self.assertAlmostEqual(r["maximum_node_difference_v"],.0005,places=14)
        self.assertAlmostEqual(r["maximum_timing_c2_difference_v"],.0005,places=14)
        self.assertTrue(r["prefix_passed"])
        r=prefix_comparison((ta,va),(tb,vb+.002),92)
        self.assertFalse(r["prefix_passed"])

    def test_reproducible_observations_keep_prefix_and_full_admission_distinct(self):
        r=json.loads((ROOT/"evidence/loudness_latch_bdf_prefix_audit.json").read_text())
        self.assertEqual(json.loads(json.dumps(generate())),r)
        for group in r["groups"]:
            p=group["prefix"]
            self.assertEqual(p["prefix_passed"],p["end_s"]>=r["prefix_end_s"] and p["maximum_node_difference_v"]<p["maximum_difference_gate_v"])
            for event in group["events"]:
                for name in ("policy_a","policy_b"):
                    if event[name]:self.assertLess(p["end_s"],event[name][0]["left_s"])
        for path,h in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        for flag in ("independent_exact_solution","temporal_refinement_admitted","physical_switching_admitted","audio_admitted","trajectory_modified"):
            self.assertFalse(r[flag])
        self.assertTrue(r["diagnostic_only"])

    def test_same_time_queries_preserve_histories_and_close_direct_charge_kcl(self):
        r=json.loads((ROOT/"evidence/loudness_latch_bdf_prefix_audit.json").read_text())
        n=BdfNetwork(200,model_parameters(1,"finite_transit"))
        for name,gate in (("bdf_same_time_query","original_prefix_gate_retained"),
                          ("bdf_transition_time_query","original_full_gate_retained")):
            shadow=r[name]
            self.assertTrue(shadow[gate]);self.assertFalse(shadow["published_shadow"])
            for q in shadow["queries"]:
                old,new=unpack(n,q["previous"]),unpack(n,q["candidate"])
                before=state_hash(old)
                self.assertEqual(before,q["previous_history_sha256"])
                check=publication_check(n,old,new,q["diagnostics"]["actual_dt_s"],q["diagnostics"])
                self.assertEqual(check,q["publication"])
                self.assertLess(check["max_published_kcl_a"],1e-11)
                self.assertFalse(q["published"])
                if q["query_method"].startswith("unpublished"):
                    reproduced,d=n.advance(old,10.,shadow["time_s"]-old.time_s)
                    self.assertEqual(reproduced,new)
                    independent,d=n.advance(old,10.,shadow["time_s"]-old.time_s,use_fd=True)
                    self.assertLess(np.max(np.abs(np.array(independent.current.joint.node_v)-new.current.joint.node_v)),1e-8)
                self.assertEqual(state_hash(old),before)


if __name__=="__main__":unittest.main()
