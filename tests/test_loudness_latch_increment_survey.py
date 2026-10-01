import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_increment_reference import IncrementNetwork
from loudness_latch_increment_probes import unpack,pack,state_hash,publication_check
from loudness_latch_increment_time import Policy,trial
from loudness_latch_time_reference import frozen_rate
from loudness_latch_increment_survey import compare,POLICIES


def record(state):
    return json.loads(json.dumps(pack(state)))


class CompensatedSurvey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/"evidence/loudness_latch_increment_survey.json").read_text())
        cls.network=IncrementNetwork(200,model_parameters(1,"finite_transit"))

    def test_every_half_interval_preserves_all_histories_and_publication_kcl(self):
        n=self.network
        for case in self.report["cases"]:
            old=unpack(n,case["initial"],0.)
            self.assertTrue(case["accepted"])
            for row in case["accepted"]:
                for name,k in (("half",0),("fine",1)):
                    diag=row["diagnostics"][name];h=row["dt_s"]/2
                    new=unpack(n,row[name],10.)
                    delta=np.array(diag["increment_v"])
                    r,_=n.increment_evaluator(10.,old,h)(delta,False)
                    self.assertLess(np.max(np.abs(r)),1e-11)
                    self.assertEqual(n.publish(delta,10.,old,h),new)
                    self.assertEqual(n.latch.prepare(new.joint.node_v),new.latch)
                    check=publication_check(n,old,new,10.,h,diag)
                    self.assertEqual(check,row["publication"][k])
                    self.assertLess(check["max_published_kcl_a"],1e-11)
                    self.assertLess(check["max_serialized_replay_kcl_a"],1e-11)
                    old=new
            self.assertEqual(record(old),case["final"])

    def test_error_and_frozen_mode_decisions_replay_at_transition_and_endpoints(self):
        n=self.network
        for case in self.report["cases"]:
            p=Policy(**case["policy"]);a=case["accepted"]
            indices=sorted({0,len(a)//2,len(a)-1,min(range(len(a)),key=lambda k:a[k]["dt_s"])})
            for k in indices:
                row=a[k];old=unpack(n,case["initial"] if k==0 else a[k-1]["fine"],0. if k==0 else 10.)
                rate=frozen_rate(n,old,0. if k==0 else 10.)
                result,diag,_=trial(n,old,10.,row["dt_s"],p,rate)
                self.assertIsNotNone(result)
                self.assertEqual(record(result[0]),row["half"])
                self.assertEqual(record(result[1]),row["fine"])
                for name in ("voltage_error_ratio","junction_voltage_error_ratio","junction_increment_v","positive_mode_step_product"):
                    self.assertAlmostEqual(diag[name],row["diagnostics"][name],places=12)

    def test_rejected_attempts_keep_the_previous_complete_accepted_state(self):
        n=self.network
        for case in self.report["cases"]:
            states={0.:state_hash(unpack(n,case["initial"],0.))}
            for row in case["accepted"]:
                states[row["start_s"]+row["dt_s"]]=state_hash(unpack(n,row["fine"],10.))
            for row in case["rejected"]:
                self.assertEqual(row["previous_state_sha256"],states[row["time_s"]])
            self.assertEqual(case["history_reset_count"],0)
            self.assertIsNone(case["selected_alternative"])

    def test_original_policy_gates_coverage_and_refinement_are_separate(self):
        for p,case in zip(POLICIES,self.report["cases"]):
            self.assertEqual(Policy(**case["policy"]),p)
            self.assertEqual(case["accepted_backward_euler_steps"],2*len(case["accepted"]))
            self.assertEqual(case["attempts"],len(case["accepted"])+len(case["rejected"]))
            self.assertEqual(case["complete"],case["final_time_s"]>=self.report["end_s"])
            for row in case["accepted"]:
                d=row["diagnostics"]
                self.assertLessEqual(max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"]),1.)
                self.assertLessEqual(d["junction_increment_v"],p.junction_increment_v)
                self.assertLessEqual(d["positive_mode_step_product"],p.positive_mode_step_product)
        self.assertEqual(compare(self.report["cases"]),self.report["refinement"])
        self.assertEqual(self.report["temporal_refinement_admitted"],self.report["refinement"]["passed"])

    def test_sources_and_scope_cannot_be_promoted_to_physical_or_audio_claims(self):
        for path,h in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        for flag in ("original_v1_modified","independent_trajectory_oracle","temporal_error_bound_admitted",
                     "physical_charge_identified","physical_switching_admitted","audio_admitted"):
            self.assertFalse(self.report[flag])
        self.assertIsNone(self.report["selected"])


if __name__=="__main__":unittest.main()
