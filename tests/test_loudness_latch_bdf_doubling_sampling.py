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
from loudness_latch_bdf_survey import trace,state_hash
from loudness_latch_bdf_observation_domain import DomainPath
from loudness_latch_bdf_sampling import FIXED_TIMES_S,metrics
from loudness_latch_bdf_common_sampling import fd_observation
from loudness_latch_bdf_doubling_survey import OUTPUTS,canonical
from loudness_latch_bdf_doubling_sampling import OUTPUT,SUMMARY,node_peaks


class DoublingSampling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=gzip.decompress(OUTPUT.read_bytes());cls.r=json.loads(cls.raw)
        cls.s=json.loads(SUMMARY.read_text())
        cls.n=BdfNetwork(200,model_parameters(1,"finite_transit"))
        cls.cases=[json.loads(gzip.decompress(p.read_bytes()))["case"] for p in OUTPUTS]
        cls.paths=[DomainPath(cls.n,c) for c in cls.cases]

    def test_all_node_peaks_fixed_grid_and_stratified_midpoints_are_observed(self):
        r=self.r
        self.assertEqual(node_peaks(*(trace(c) for c in self.cases)),r["node_peaks"])
        self.assertEqual({p["node_index"] for p in r["node_peaks"]},set(range(94)))
        fixed=[t for t in FIXED_TIMES_S if r["start_s"]<=t<=r["end_s"]]
        mids=[p.midpoints(r["start_s"],r["end_s"]) for p in self.paths]
        self.assertEqual(fixed,r["fixed_grid_times_s"]);self.assertEqual(mids,r["midpoint_times_s"])
        expected=sorted(set(fixed+sum(mids,[])+[p["time_s"] for p in r["node_peaks"]]+list(r["landmarks"].values())))
        self.assertEqual(expected,[row["time_s"] for row in r["rows"]])

    def test_every_valid_query_preserves_requested_clock_and_real_charge(self):
        n=self.n
        for row in self.r["rows"]:
            for path,q in zip(self.paths,row["queries"]):
                old=path.previous(q["position"]);snapshot=state_hash(old)
                self.assertEqual(snapshot,q["previous_history_sha256"])
                self.assertFalse(q["published"])
                if not q["query_valid"]:
                    self.assertIn("error",q);continue
                steps=q["path_steps"] or [dict(candidate=q["candidate"],diagnostics=q["diagnostics"],publication=q["publication"])]
                for step in steps:
                    candidate=unpack(n,step["candidate"]);d=step["diagnostics"]
                    self.assertGreaterEqual(d["actual_dt_s"],1e-12)
                    self.assertEqual(candidate.previous,old.current)
                    check=publication_check(n,old,candidate,d["actual_dt_s"],d)
                    self.assertEqual(check,step["publication"])
                    self.assertTrue(check["round_trip_exact"])
                    self.assertLess(check["max_published_kcl_a"],1e-11)
                    self.assertLess(check["max_branch_equation_error_v"],1e-14)
                    old=candidate
                self.assertEqual(old.time_s,row["time_s"])
                self.assertEqual(old,unpack(n,q["candidate"]))
                self.assertEqual(state_hash(path.previous(q["position"])),snapshot)
            if row["valid_both"]:
                a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in row["queries"]]
                self.assertEqual(float(np.max(np.abs(a-b))),row["maximum_node_difference_v"])

    def test_FD_at_interpolated_and_sampled_peaks_replays_without_retiming(self):
        names={"D4":0,"E4":1}
        for saved in self.r["fd_observations"]:
            index=names[saved["policy"]];path=self.paths[index]
            row=next(row for row in self.r["rows"] if row["time_s"]==saved["time_s"])
            replay=fd_observation(self.n,path,row["queries"][index])
            self.assertEqual(canonical(replay),canonical({k:v for k,v in saved.items() if k not in ("policy","landmark")}))
            self.assertTrue(replay["passed"])

    def test_finite_sample_gates_and_original_scope_remain_separate(self):
        r=self.r
        self.assertEqual(metrics(r["rows"],r["end_s"]),r["sampled_comparison"])
        self.assertEqual(metrics(r["rows"],.0023),r["sampled_prefix_comparison"])
        self.assertEqual(r["sampled_comparison"]["maximum_difference_gate_v"],1e-3)
        self.assertFalse(r["sampled_comparison"]["continuous_bound"])
        self.assertTrue(r["diagnostic_only"])
        for key in ("trajectory_retimed","previous_reports_modified","temporal_refinement_admitted",
                    "temporal_error_bound_admitted","physical_switching_admitted","audio_admitted"):
            self.assertFalse(r[key])

    def test_byte_storage_sources_and_complete_query_counts(self):
        r=self.r;s=self.s;storage=s["storage"]
        self.assertEqual(canonical(r),self.raw)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),storage["canonical_json_sha256"])
        self.assertEqual(hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),storage["compressed_sha256"])
        self.assertEqual(s["queries"],2*len(r["rows"]))
        self.assertEqual(s["invalid_queries"],sum(not q["query_valid"] for row in r["rows"] for q in row["queries"]))
        for source,h in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),h)


if __name__=="__main__":unittest.main()
