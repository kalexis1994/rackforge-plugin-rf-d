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
from loudness_latch_bdf_probes import pack,unpack,publication_check
from loudness_latch_bdf_survey import state_hash,trace as dc_trace
from loudness_latch_bdf_time import trial
from loudness_latch_increment_time import Policy
from loudness_latch_time_reference import frozen_rate
from loudness_latch_bdf_common_history import (OUTPUT,SUMMARY,PREVIOUS,STRICT,ANCHOR_LIMIT_S,
    POLICY,reference_case,continuation_trace,compare,inherited_audit,ContinuationPath)


class CommonHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encoded=OUTPUT.read_bytes();cls.canonical=gzip.decompress(cls.encoded)
        cls.report=json.loads(cls.canonical);cls.summary=json.loads(SUMMARY.read_text())
        cls.strict=json.loads(gzip.decompress(STRICT.read_bytes()))
        cls.previous=json.loads(gzip.decompress(PREVIOUS.read_bytes()))
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))
        cls.fine=reference_case(cls.strict,cls.report["anchor_C3_accepted_index"])

    def test_common_anchor_contains_exactly_both_accepted_histories_and_the_original_clock(self):
        r=self.report;index=r["anchor_C3_accepted_index"];source=self.strict["case"]["accepted"]
        original=source[index]["steps"][-1]["history"]
        self.assertEqual(r["anchor"],original);self.assertEqual(self.fine["initial"],original)
        self.assertEqual(r["case"]["initial"],original)
        self.assertIsNotNone(original["previous"]);self.assertEqual(original["key_v"],10.)
        self.assertLessEqual(original["time_s"],ANCHOR_LIMIT_S)
        self.assertGreater(source[index+1]["steps"][-1]["history"]["time_s"],ANCHOR_LIMIT_S)
        self.assertEqual(r["initial_proposal_s"],source[index+1]["dt_s"])
        self.assertEqual(r["common_history_sha256"],state_hash(unpack(self.network,original)))
        self.assertEqual(continuation_trace(r["case"])[0][0],original["time_s"])
        self.assertEqual(r["case"]["policy"],vars(POLICY))

    def test_all_new_intervals_close_kcl_keep_both_states_and_never_bootstrap(self):
        n=self.network;c=self.report["case"];old=unpack(n,c["initial"]);count=0
        for row in c["accepted"]:
            self.assertEqual(row["start_s"],old.time_s)
            self.assertEqual(row["previous_history_sha256"],state_hash(old))
            self.assertEqual(len(row["steps"]),1)
            for s in row["steps"]:
                new=unpack(n,s["history"]);d=s["diagnostics"];h=d["actual_dt_s"]
                self.assertEqual(d["method"],"variable-bdf2-charge/v1")
                self.assertEqual(new.previous,old.current);self.assertEqual(new.previous_dt_s,h)
                self.assertEqual(new.time_s,old.time_s+h)
                virtual,coefficients=n.effective_history(old,h)
                self.assertLessEqual(coefficients["ratio"],2.)
                delta=np.array(d["increment_v"])
                residual,_=n.network.increment_evaluator(10.,virtual,coefficients["effective_dt_s"])(delta,False)
                self.assertLess(np.max(np.abs(residual)),1e-11)
                self.assertEqual(n.network.publish(delta,10.,virtual,coefficients["effective_dt_s"]),new.current)
                check=publication_check(n,old,new,h,d)
                self.assertEqual(check,s["publication"]);self.assertLess(check["max_published_kcl_a"],1e-11)
                self.assertLess(check["max_branch_equation_error_v"],1e-14);self.assertTrue(check["round_trip_exact"])
                old=new;count+=1
        self.assertEqual(count,c["published_intervals"])
        self.assertEqual(json.loads(json.dumps(pack(old))),c["final"])
        self.assertEqual(c["history_reset_count"],0);self.assertIsNone(c["selected_alternative"])

    def test_inherited_suffix_is_verified_without_counting_new_C3_integration(self):
        r=self.report
        self.assertEqual(inherited_audit(self.network,self.fine),r["inherited_C3_audit"])
        self.assertEqual(r["inherited_C3_audit"]["new_C3_intervals_generated"],0)
        self.assertEqual(self.fine["final"],self.strict["case"]["final"])
        self.assertEqual(self.fine["accepted"],self.strict["case"]["accepted"][r["anchor_C3_accepted_index"]+1:])

    def test_local_decisions_and_rejection_memory_replay_for_both_suffixes(self):
        n=self.network
        for c in (self.report["case"],self.fine):
            rows=c["accepted"];p=Policy(**c["policy"])
            states={c["initial"]["time_s"]:state_hash(unpack(n,c["initial"]))}
            for row in rows:
                history=unpack(n,row["steps"][-1]["history"]);states[history.time_s]=state_hash(history)
                d=row["diagnostics"]
                self.assertLessEqual(max(d["voltage_error_ratio"],d["junction_voltage_error_ratio"]),1.)
                self.assertLessEqual(d["junction_increment_v"],p.junction_increment_v)
                self.assertLessEqual(d["positive_mode_step_product"],p.positive_mode_step_product)
            for row in c["rejected"]:
                self.assertEqual(states[row["time_s"]],row["previous_history_sha256"])
            indices={0,len(rows)//2,len(rows)-1,min(range(len(rows)),key=lambda k:rows[k]["dt_s"])}
            for k in indices:
                old=unpack(n,c["initial"] if k==0 else rows[k-1]["steps"][-1]["history"])
                incoming=copy.deepcopy(old);rate=frozen_rate(n.network,old.current,10.)
                result,diag,_=trial(n,old,10.,rows[k]["dt_s"],p,rate)
                self.assertIsNotNone(result);self.assertEqual(old,incoming)
                for (candidate,d),s in zip(result,rows[k]["steps"]):
                    self.assertEqual(candidate,unpack(n,s["history"]));self.assertEqual(d,s["diagnostics"])
                for field in ("voltage_error_ratio","junction_voltage_error_ratio","junction_increment_v","positive_mode_step_product"):
                    self.assertAlmostEqual(diag[field],rows[k]["diagnostics"][field],places=12)

    def test_comparisons_and_same_time_peak_do_not_retime_or_replace_original_failed_gate(self):
        r=self.report;n=self.network;c=r["case"];fine=self.fine
        complete=c["complete"] and fine["complete"]
        bt,ct=continuation_trace(c),continuation_trace(fine)
        result=compare(bt,ct,complete)
        self.assertEqual(result,r["conditional_comparison"])
        self.assertEqual(result["start_s"],r["anchor_time_s"])
        self.assertEqual(result["maximum_difference_gate_v"],1e-3)
        self.assertEqual(result["passed"],r["conditional_refinement_passed"])
        self.assertEqual(compare(dc_trace(self.previous["cases"][1]),ct,complete,start_s=r["anchor_time_s"]),r["original_window_comparison"])
        self.assertEqual(r["original_full_comparison"],self.strict["refinement"])
        self.assertFalse(r["original_full_comparison"]["passed"])
        q=r["same_time_conditional_peak"];values=[]
        for p,saved in zip((ContinuationPath(n,c),ContinuationPath(n,fine)),q["queries"]):
            replay=p.query(q["time_s"])
            self.assertEqual(replay["query_valid"],saved["query_valid"])
            if saved["query_valid"]:
                candidate=unpack(n,saved["candidate"])
                self.assertEqual(candidate,unpack(n,replay["candidate"]))
                self.assertEqual(candidate.time_s,q["time_s"])
                values.append(np.array(candidate.current.joint.node_v))
        if q["valid_both"]:
            self.assertEqual(float(np.max(np.abs(values[0]-values[1]))),q["maximum_node_difference_v"])

    def test_storage_revisions_and_conditional_scope(self):
        r=self.report;s=self.summary
        self.assertEqual(hashlib.sha256(self.encoded).hexdigest(),s["compressed_sha256"])
        self.assertEqual(hashlib.sha256(self.canonical).hexdigest(),s["canonical_json_sha256"])
        for path,h in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        self.assertEqual(r["conditional_comparison"],s["conditional_comparison"])
        self.assertTrue(r["diagnostic_only"])
        for flag in ("previous_reports_modified","trajectory_retimed","temporal_refinement_admitted",
                     "temporal_error_bound_admitted","physical_switching_admitted","audio_admitted"):
            self.assertFalse(r[flag])


if __name__=="__main__":unittest.main()
