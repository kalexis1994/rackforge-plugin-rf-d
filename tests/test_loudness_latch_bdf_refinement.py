import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_survey import state_hash,trace,comparison
from loudness_latch_bdf_time import trial
from loudness_latch_bdf_refinement import POLICY,OUTPUT,SUMMARY,PREVIOUS
from loudness_latch_time_reference import frozen_rate


class BdfRefinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encoded=OUTPUT.read_bytes();cls.canonical=gzip.decompress(cls.encoded)
        cls.report=json.loads(cls.canonical);cls.case=cls.report["case"]
        cls.summary=json.loads(SUMMARY.read_text())
        cls.previous=json.loads(gzip.decompress(PREVIOUS.read_bytes()))
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_all_published_charges_close_kcl_and_preserve_both_histories(self):
        n=self.network;case=self.case;old=unpack(n,case["initial"]);count=0
        for row in case["accepted"]:
            self.assertEqual(row["previous_history_sha256"],state_hash(old))
            self.assertEqual(row["start_s"],old.time_s)
            d=row["diagnostics"]
            self.assertLessEqual(max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"]),1.)
            self.assertLessEqual(d["junction_increment_v"],POLICY.junction_increment_v)
            self.assertLessEqual(d["positive_mode_step_product"],POLICY.positive_mode_step_product)
            for s in row["steps"]:
                new=unpack(n,s["history"]);diag=s["diagnostics"];h=diag["actual_dt_s"]
                self.assertEqual(new.previous,old.current)
                self.assertEqual(new.previous_dt_s,h);self.assertEqual(new.time_s,old.time_s+h)
                if old.previous is None:virtual,dt=old.current,h
                else:
                    virtual,c=n.effective_history(old,h);dt=c["effective_dt_s"]
                    self.assertLessEqual(c["ratio"],2.)
                delta=np.array(diag["increment_v"])
                residual,_=n.network.increment_evaluator(10.,virtual,dt)(delta,False)
                self.assertLess(np.max(np.abs(residual)),1e-11)
                self.assertEqual(n.network.publish(delta,10.,virtual,dt),new.current)
                check=publication_check(n,old,new,h,diag)
                self.assertEqual(check,s["publication"])
                self.assertLess(check["max_published_kcl_a"],1e-11)
                self.assertLess(check["max_branch_equation_error_v"],1e-14)
                self.assertTrue(check["round_trip_exact"])
                count+=1;old=new
        self.assertEqual(count,case["published_intervals"])
        self.assertEqual(json.loads(json.dumps(pack(old))),case["final"])

    def test_local_decisions_replay_at_start_middle_minimum_and_end(self):
        n=self.network;rows=self.case["accepted"]
        selected={0,len(rows)//2,len(rows)-1,min(range(len(rows)),key=lambda k:rows[k]["dt_s"])}
        for k in selected:
            old=unpack(n,self.case["initial"] if k==0 else rows[k-1]["steps"][-1]["history"])
            incoming=copy.deepcopy(old);r=rows[k]
            rate=frozen_rate(n.network,old.current,old.key_v)
            result,diag,_=trial(n,old,10.,r["dt_s"],POLICY,rate)
            self.assertIsNotNone(result);self.assertEqual(incoming,old)
            for (candidate,d),s in zip(result,r["steps"]):
                self.assertEqual(candidate,unpack(n,s["history"]))
                self.assertEqual(d,s["diagnostics"])
            for field in ("voltage_error_ratio","junction_voltage_error_ratio","junction_increment_v","positive_mode_step_product"):
                self.assertAlmostEqual(diag[field],r["diagnostics"][field],places=12)

    def test_rejected_trials_keep_memory_and_budget_does_not_select_a_root(self):
        n=self.network;c=self.case
        states={0.:state_hash(unpack(n,c["initial"]))}
        for row in c["accepted"]:
            h=unpack(n,row["steps"][-1]["history"]);states[h.time_s]=state_hash(h)
        for row in c["rejected"]:
            self.assertEqual(row["previous_history_sha256"],states[row["time_s"]])
        self.assertEqual(c["history_reset_count"],0);self.assertIsNone(c["selected_alternative"])
        self.assertEqual(c["attempts"],len(c["accepted"])+len(c["rejected"]))
        self.assertLessEqual(c["attempts"],POLICY.maximum_attempts)
        self.assertEqual(c["complete"],c["final_time_s"]>=self.report["end_s"])

    def test_refinement_is_recomputed_and_never_replaces_previous_evidence(self):
        r=self.report;c=self.case;p=self.previous["cases"][1]
        self.assertEqual(c["policy"],vars(POLICY))
        for name in ("voltage_abs_v","voltage_relative","junction_abs_v","junction_relative"):
            self.assertEqual(c["policy"][name],p["policy"][name]/4)
        result=comparison(trace(p),trace(c),c["complete"] and p["complete"])
        self.assertEqual(result,r["refinement"])
        self.assertEqual(r["temporal_refinement_admitted"],result["passed"])
        self.assertEqual(result,self.summary["refinement"])
        self.assertEqual(result["maximum_difference_gate_v"],1e-3)

    def test_storage_source_revisions_and_claims(self):
        self.assertEqual(hashlib.sha256(self.encoded).hexdigest(),self.summary["compressed_sha256"])
        self.assertEqual(hashlib.sha256(self.canonical).hexdigest(),self.summary["canonical_json_sha256"])
        self.assertEqual(self.report["source_sha256"],self.summary["source_sha256"])
        for path,digest in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
        for flag in ("previous_reports_modified","independent_spatial_oracle","temporal_error_bound_admitted",
                     "physical_charge_identified","physical_switching_admitted","audio_admitted"):
            self.assertFalse(self.report[flag])


if __name__=="__main__":unittest.main()
