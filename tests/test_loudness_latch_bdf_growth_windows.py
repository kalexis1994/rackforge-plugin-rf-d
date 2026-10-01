import gzip
import copy
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
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_common_history import continuation_trace,compare,ContinuationPath
from loudness_latch_bdf_doubling_survey import OUTPUTS,canonical
from loudness_latch_bdf_growth_windows import OUTPUT,SUMMARY,WINDOWS,THRESHOLDS,POLICY,MAXIMUM_ATTEMPTS


class GrowthWindows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=gzip.decompress(OUTPUT.read_bytes());cls.r=json.loads(cls.raw)
        cls.s=json.loads(SUMMARY.read_text())
        cls.e4=json.loads(gzip.decompress(OUTPUTS[1].read_bytes()))["case"]
        cls.n=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_declared_windows_share_exactly_both_E4_histories_and_first_proposal(self):
        self.assertEqual(len(self.r["windows"]),len(WINDOWS))
        self.assertEqual(self.r["thresholds"],list(THRESHOLDS))
        for spec,w in zip(WINDOWS,self.r["windows"]):
            name,limit,span=spec;index=w["E4_accepted_anchor_index"]
            row=self.e4["accepted"][index];initial=row["steps"][-1]["history"]
            self.assertEqual(w["name"],name);self.assertEqual(w["initial"],initial)
            self.assertLessEqual(initial["time_s"],limit)
            self.assertGreater(self.e4["accepted"][index+1]["steps"][-1]["history"]["time_s"],limit)
            self.assertEqual(w["end_s"],initial["time_s"]+span)
            self.assertIsNotNone(initial["previous"])
            for threshold,c in zip(THRESHOLDS,w["cases"]):
                self.assertEqual(c["initial"],initial);self.assertEqual(c["growth_error_threshold"],threshold)
                self.assertEqual(c["first_proposal_s"],self.e4["accepted"][index+1]["dt_s"])
                self.assertEqual(c["policy"],vars(POLICY));self.assertEqual(c["history_reset_count"],0)
                self.assertLessEqual(c["attempts"],MAXIMUM_ATTEMPTS)
                self.assertEqual(c["complete"],c["final_time_s"]==w["end_s"])

    def test_every_full_and_provisional_interval_has_real_charge_and_atomic_lineage(self):
        n=self.n
        for w in self.r["windows"]:
            for c in w["cases"]:
                old=unpack(n,c["initial"]);states={old.time_s:state_hash(old)}
                for row in c["accepted"]:
                    self.assertEqual(row["previous_history_sha256"],state_hash(old))
                    self.assertEqual(row["start_s"],old.time_s);self.assertEqual(len(row["steps"]),1)
                    new=self.check_interval(old,row["steps"][0])
                    shadow=old
                    for s in row["diagnostics"]["shadow_half_steps"]:
                        self.assertFalse(s["published"]);shadow=self.check_interval(shadow,s)
                    self.assertEqual(new.time_s,shadow.time_s)
                    old=new;states[old.time_s]=state_hash(old)
                self.assertEqual(canonical(pack(old)),canonical(c["final"]))
                for row in c["rejected"]:
                    self.assertEqual(row["previous_history_sha256"],states[row["time_s"]])

    def check_interval(self,old,s):
        new=unpack(self.n,s["history"]);d=s["diagnostics"];h=d["actual_dt_s"]
        self.assertEqual(d["method"],"variable-bdf2-charge/v1")
        self.assertGreaterEqual(h,POLICY.minimum_step_s)
        self.assertEqual(new.previous,old.current);self.assertEqual(new.time_s,old.time_s+h)
        check=publication_check(self.n,old,new,h,d)
        self.assertEqual(check,s["publication"]);self.assertTrue(check["round_trip_exact"])
        self.assertLess(check["max_published_kcl_a"],1e-11)
        self.assertLess(check["max_branch_equation_error_v"],1e-14)
        return new

    def test_both_growth_rules_and_every_halving_reconstruct_recorded_proposals(self):
        for w in self.r["windows"]:
            for c in w["cases"]:
                old=unpack(self.n,c["initial"]);h=c["first_proposal_s"]
                rejects=iter(c["rejected"]);pending=next(rejects,None)
                for row in c["accepted"]:
                    h=min(h,c["end_s"]-old.time_s,POLICY.maximum_step_s,2*old.previous_dt_s)
                    while pending is not None and pending["time_s"]==old.time_s:
                        self.assertEqual(h,pending["dt_s"]);h/=2;pending=next(rejects,None)
                    self.assertEqual(h,row["dt_s"])
                    d=row["diagnostics"]
                    self.assertLessEqual(max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"]),1.)
                    self.assertLessEqual(d["junction_increment_v"],POLICY.junction_increment_v)
                    self.assertLessEqual(d["positive_mode_step_product"],POLICY.positive_mode_step_product)
                    old=unpack(self.n,row["steps"][-1]["history"])
                    if (max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"])<c["growth_error_threshold"]
                            and d["junction_increment_v"]<POLICY.junction_increment_v/2
                            and d["positive_mode_step_product"]<POLICY.positive_mode_step_product/2):
                        h=min(2*h,POLICY.maximum_step_s,2*old.previous_dt_s)
                self.assertIsNone(pending)

    def test_conditional_comparisons_and_queries_do_not_replace_DC_gate(self):
        for w in self.r["windows"]:
            complete=all(c["complete"] for c in w["cases"])
            self.assertEqual(compare(*(continuation_trace(c) for c in w["cases"]),complete),w["conditional_comparison"])
            peak=w["same_time_interpolated_peak"]
            if not peak["queries"]:
                self.assertEqual(w["conditional_comparison"]["maximum_node_difference_v"],0.)
                self.assertEqual(peak["time_s"],w["initial"]["time_s"])
                continue
            for c,q in zip(w["cases"],peak["queries"]):
                replay=ContinuationPath(self.n,c).query(peak["time_s"])
                self.assertEqual(canonical(replay),canonical(q))
            if peak["valid_both"]:
                a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in peak["queries"]]
                self.assertEqual(float(np.max(np.abs(a-b))),peak["maximum_node_difference_v"])
        for key in ("previous_reports_modified","trajectory_retimed","temporal_refinement_admitted",
                    "temporal_error_bound_admitted","physical_switching_admitted","audio_admitted"):
            self.assertFalse(self.r[key])

    def test_storage_and_source_revisions(self):
        self.assertEqual(canonical(self.r),self.raw)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),self.s["storage"]["canonical_json_sha256"])
        self.assertEqual(hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),self.s["storage"]["compressed_sha256"])
        for path,h in self.r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)

    def test_failed_summary_attempt_preserves_identical_numerical_windows(self):
        attempt=json.loads((ROOT/"evidence/loudness_latch_bdf_growth_attempts.json").read_text())
        original_path=ROOT/attempt["archive_path"]
        self.assertEqual(hashlib.sha256(original_path.read_bytes()).hexdigest(),attempt["archive_sha256"])
        self.assertEqual(hashlib.sha256(attempt["producer_source_utf8"].encode()).hexdigest(),attempt["producer_source_sha256"])
        original=json.loads(gzip.decompress(original_path.read_bytes()))
        windows=copy.deepcopy(original["windows"])
        for w in windows:
            for c in w["cases"]:
                for row in c["accepted"]+c["rejected"]:
                    row["diagnostics"]["startup"]=False
        self.assertEqual(canonical(windows),canonical(self.r["windows"]))


if __name__=="__main__":unittest.main()
