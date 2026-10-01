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
from loudness_latch_bdf_probes import unpack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_sampling import metrics
from loudness_latch_bdf_common_history import reference_case,continuation_trace,ContinuationPath
from loudness_latch_bdf_common_sampling import OUTPUT,SUMMARY,COMMON,STRICT,GRID,node_peaks,fd_observation


class CommonSampling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encoded=OUTPUT.read_bytes();cls.canonical=gzip.decompress(cls.encoded)
        cls.report=json.loads(cls.canonical);cls.summary=json.loads(SUMMARY.read_text())
        cls.common=json.loads(gzip.decompress(COMMON.read_bytes()))
        strict=json.loads(gzip.decompress(STRICT.read_bytes()))
        cls.cases=[cls.common["case"],reference_case(strict,cls.common["anchor_C3_accepted_index"])]
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))
        cls.paths=[ContinuationPath(cls.network,c) for c in cls.cases]

    def test_every_node_peak_and_retained_grid_time_is_observed_without_selection(self):
        r=self.report
        peaks=node_peaks(*(continuation_trace(c) for c in self.cases))
        self.assertEqual(peaks,r["node_peaks"]);self.assertEqual(len(peaks),94)
        self.assertEqual([p["node_index"] for p in peaks],list(range(94)))
        grid=json.loads(gzip.decompress(GRID.read_bytes()))
        retained=[row["time_s"] for row in grid["rows"] if r["start_s"]<=row["time_s"]<=r["end_s"]]
        self.assertEqual(retained,r["retained_grid_times_s"])
        times=sorted(set(retained+[p["time_s"] for p in peaks if r["start_s"]<=p["time_s"]<=r["end_s"]]+list(r["landmarks"].values())))
        self.assertEqual(times,[row["time_s"] for row in r["rows"]])

    def test_every_query_obeys_charge_kcl_and_retains_accepted_and_provisional_memory(self):
        n=self.network
        for row in self.report["rows"]:
            self.assertTrue(row["valid_both"])
            values=[]
            for p,q in zip(self.paths,row["queries"]):
                old=p.previous(q["position"]);snapshot=state_hash(old)
                self.assertEqual(snapshot,q["previous_history_sha256"]);self.assertFalse(q["published"])
                steps=q["path_steps"] or [dict(candidate=q["candidate"],diagnostics=q["diagnostics"],publication=q["publication"])]
                for s in steps:
                    new=unpack(n,s["candidate"]);d=s["diagnostics"];h=d["actual_dt_s"]
                    self.assertGreaterEqual(h,1e-12);self.assertEqual(new.previous,old.current)
                    self.assertEqual(new.time_s,old.time_s+h)
                    virtual,c=n.effective_history(old,h);delta=np.array(d["increment_v"])
                    residual,_=n.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(delta,False)
                    self.assertLess(np.max(np.abs(residual)),1e-11)
                    self.assertEqual(n.network.publish(delta,10.,virtual,c["effective_dt_s"]),new.current)
                    check=publication_check(n,old,new,h,d)
                    self.assertEqual(check,s["publication"]);self.assertLess(check["max_published_kcl_a"],1e-11)
                    self.assertLess(check["max_branch_equation_error_v"],1e-14)
                    old=new
                self.assertEqual(old,unpack(n,q["candidate"]));self.assertEqual(old.time_s,row["time_s"])
                self.assertEqual(state_hash(p.previous(q["position"])),snapshot)
                values.append(np.array(old.current.joint.node_v))
            delta=np.abs(values[0]-values[1])
            self.assertEqual(float(np.max(delta)),row["maximum_node_difference_v"])
            self.assertEqual(int(np.argmax(delta)),row["maximum_difference_node"])

    def test_fd_at_interpolated_and_sampled_peaks_replays_without_changing_clock(self):
        r=self.report;n=self.network
        self.assertEqual(len(r["fd_observations"]),4)
        for stored in r["fd_observations"]:
            row=next(row for row in r["rows"] if row["time_s"]==stored["time_s"])
            k=("B3-common","C3-inherited").index(stored["policy"])
            fd=fd_observation(n,self.paths[k],row["queries"][k])
            self.assertTrue(fd["passed"]);self.assertEqual(fd["max_node_difference_v"],stored["max_node_difference_v"])
            self.assertEqual(fd["previous_history_sha256"],stored["previous_history_sha256"])
            for actual,saved in zip(fd["steps"],stored["steps"]):
                self.assertEqual(unpack(n,actual["candidate"]),unpack(n,saved["candidate"]))
                self.assertEqual(actual["publication"],saved["publication"])

    def test_interpolation_peak_is_distinct_from_sampled_peak_and_global_admission(self):
        r=self.report
        self.assertEqual(metrics(r["rows"],r["end_s"]),r["sampled_comparison"])
        self.assertEqual(r["original_interpolated_common_comparison"],self.common["conditional_comparison"])
        self.assertEqual(r["original_DC_comparison"],self.common["original_full_comparison"])
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["sampled_comparison"]["continuous_bound"])
        self.assertNotEqual(r["sampled_comparison"]["maximum_difference_time_s"],r["landmarks"]["interpolated_common_peak"])
        for flag in ("trajectory_retimed","previous_reports_modified","temporal_refinement_admitted",
                     "temporal_error_bound_admitted","physical_switching_admitted","audio_admitted"):
            self.assertFalse(r[flag])

    def test_lossless_sources_and_complete_query_coverage(self):
        r=self.report;s=self.summary
        self.assertEqual(hashlib.sha256(self.encoded).hexdigest(),s["compressed_sha256"])
        self.assertEqual(hashlib.sha256(self.canonical).hexdigest(),s["canonical_json_sha256"])
        for path,h in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        self.assertEqual(s["queries"],2*len(r["rows"]));self.assertEqual(s["invalid_queries"],0)
        self.assertEqual(s["sampled_comparison"]["valid_points"],s["observation_times"])


if __name__=="__main__":unittest.main()
