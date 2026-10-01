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
from loudness_latch_bdf_time import trial
from loudness_latch_increment_time import Policy
from loudness_latch_time_reference import frozen_rate
from loudness_latch_bdf_survey import state_hash,trace,comparison,POLICIES


class BdfSurvey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encoded=(ROOT/"evidence/loudness_latch_bdf_survey.json.gz").read_bytes()
        cls.canonical=gzip.decompress(cls.encoded);cls.report=json.loads(cls.canonical)
        cls.summary=json.loads((ROOT/"evidence/loudness_latch_bdf_survey_summary.json").read_text())
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_every_published_interval_obeys_direct_two_history_kcl_and_lineage(self):
        n=self.network
        for case in self.report["cases"]:
            old=unpack(n,case["initial"]);published=0
            self.assertTrue(case["accepted"])
            for row in case["accepted"]:
                self.assertEqual(state_hash(old),row["previous_history_sha256"])
                for step in row["steps"]:
                    new=unpack(n,step["history"]);d=step["diagnostics"];h=d["actual_dt_s"]
                    self.assertEqual(new.previous,old.current)
                    self.assertEqual(new.previous_dt_s,h)
                    self.assertEqual(new.time_s,old.time_s+h)
                    if old.previous is None:
                        virtual,dt=old.current,h
                    else:
                        virtual,c=n.effective_history(old,h);dt=c["effective_dt_s"]
                        self.assertLessEqual(c["ratio"],2.)
                    delta=np.array(d["increment_v"])
                    r,_=n.network.increment_evaluator(10.,virtual,dt)(delta,False)
                    self.assertLess(np.max(np.abs(r)),1e-11)
                    self.assertEqual(n.network.publish(delta,10.,virtual,dt),new.current)
                    self.assertEqual(n.network.latch.prepare(new.current.joint.node_v),new.current.latch)
                    check=publication_check(n,old,new,h,d)
                    self.assertEqual(check,step["publication"])
                    self.assertLess(check["max_published_kcl_a"],1e-11)
                    self.assertLess(check["max_branch_equation_error_v"],1e-14)
                    self.assertTrue(check["round_trip_exact"])
                    published+=1;old=new
            self.assertEqual(published,case["published_intervals"])
            self.assertEqual(json.loads(json.dumps(pack(old))),case["final"])

    def test_local_predictor_and_mode_decisions_replay_at_minimum_and_endpoints(self):
        n=self.network
        for case in self.report["cases"]:
            accepted=case["accepted"];p=Policy(**case["policy"])
            indices=sorted({0,len(accepted)//2,len(accepted)-1,min(range(len(accepted)),key=lambda k:accepted[k]["dt_s"])})
            for k in indices:
                old=unpack(n,case["initial"] if k==0 else accepted[k-1]["steps"][-1]["history"])
                snapshot=copy.deepcopy(old);row=accepted[k]
                rate=frozen_rate(n.network,old.current,old.key_v)
                result,diag,_=trial(n,old,10.,row["dt_s"],p,rate)
                self.assertIsNotNone(result);self.assertEqual(snapshot,old)
                for (candidate,d),stored in zip(result,row["steps"]):
                    self.assertEqual(candidate,unpack(n,stored["history"]))
                    self.assertEqual(d,stored["diagnostics"])
                for name in ("voltage_error_ratio","junction_voltage_error_ratio","junction_increment_v","positive_mode_step_product"):
                    self.assertAlmostEqual(diag[name],row["diagnostics"][name],places=12)

    def test_rejections_keep_both_states_and_never_restart_or_choose_an_alternative(self):
        n=self.network
        for case in self.report["cases"]:
            states={0.:state_hash(unpack(n,case["initial"]))}
            for row in case["accepted"]:
                h=unpack(n,row["steps"][-1]["history"]);states[h.time_s]=state_hash(h)
            for row in case["rejected"]:
                self.assertEqual(row["previous_history_sha256"],states[row["time_s"]])
            self.assertEqual(case["history_reset_count"],0);self.assertIsNone(case["selected_alternative"])

    def test_coverage_local_acceptance_and_global_refinement_remain_separate(self):
        for p,case in zip(POLICIES,self.report["cases"]):
            self.assertEqual(Policy(**case["policy"]),p)
            self.assertEqual(case["complete"],case["final_time_s"]>=self.report["end_s"])
            self.assertEqual(case["attempts"],len(case["accepted"])+len(case["rejected"]))
            for row in case["accepted"]:
                d=row["diagnostics"]
                self.assertLessEqual(max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"]),1.)
                self.assertLessEqual(d["junction_increment_v"],p.junction_increment_v)
                self.assertLessEqual(d["positive_mode_step_product"],p.positive_mode_step_product)
        comparison_result=comparison(*(trace(c) for c in self.report["cases"]),all(c["complete"] for c in self.report["cases"]))
        self.assertEqual(comparison_result,self.report["refinement"])
        self.assertEqual(self.report["temporal_refinement_admitted"],comparison_result["passed"])

    def test_storage_sources_and_shared_model_scope(self):
        s=self.summary;r=self.report
        self.assertEqual(hashlib.sha256(self.encoded).hexdigest(),s["compressed_sha256"])
        self.assertEqual(hashlib.sha256(self.canonical).hexdigest(),s["canonical_json_sha256"])
        self.assertEqual(s["refinement"],r["refinement"])
        self.assertEqual(s["observations"],r["observations"])
        for path,h in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        for flag in ("previous_euler_reports_modified","independent_spatial_oracle","temporal_error_bound_admitted",
                     "physical_charge_identified","physical_switching_admitted","audio_admitted"):
            self.assertFalse(r[flag])
        self.assertTrue(r["observations"]["diagnostic_only"])
        self.assertFalse(r["observations"]["trajectory_retimed"])


if __name__=="__main__":unittest.main()
