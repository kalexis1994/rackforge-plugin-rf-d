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
from loudness_latch_bdf_survey import trace
from loudness_latch_bdf_observation_domain import DomainPath
from loudness_latch_bdf_sampling import FIXED_TIMES_S,metrics
from loudness_latch_bdf_common_sampling import fd_observation
from loudness_latch_bdf_doubling_sampling import node_peaks
from loudness_latch_bdf_doubling_survey import OUTPUTS,canonical
from loudness_latch_bdf_growth_dc import OUTPUT as GROWTH
from loudness_latch_bdf_growth_dc_sampling import OUTPUT,SUMMARY


class GrowthSampling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.case=json.loads(gzip.decompress(GROWTH.read_bytes()))["case"]
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_selection_includes_all_94_peaks_fixed_grid_and_stratified_midpoints(self):
        for path,c in zip(OUTPUTS,self.payload["contrasts"]):
            reference=json.loads(gzip.decompress(path.read_bytes()))["case"]
            paths=[DomainPath(self.network,x) for x in (reference,self.case)]
            start=max(float(p.times[1]) for p in paths);end=min(float(p.times[-1]) for p in paths)
            self.assertEqual(c["node_peaks"],node_peaks(trace(reference),trace(self.case)))
            fixed=[t for t in FIXED_TIMES_S if start<=t<=end]
            mids=[p.midpoints(start,end) for p in paths]
            self.assertEqual(c["fixed_grid_times_s"],fixed);self.assertEqual(c["midpoint_times_s"],mids)
            self.assertEqual(len(c["node_peaks"]),94)
            expected=sorted(set(fixed+sum(mids,[])+[p["time_s"] for p in c["node_peaks"]]+list(c["landmarks"].values())))
            self.assertEqual([r["time_s"] for r in c["rows"]],expected)
            self.assertEqual(c["start_s"],start);self.assertEqual(c["end_s"],end)

    def test_every_stored_query_conserves_charge_at_the_requested_time(self):
        for path,c in zip(OUTPUTS,self.payload["contrasts"]):
            reference=json.loads(gzip.decompress(path.read_bytes()))["case"]
            paths=[DomainPath(self.network,x) for x in (reference,self.case)]
            for row in c["rows"]:
                self.assertTrue(row["valid_both"])
                for index,q in enumerate(row["queries"]):
                    self.assertTrue(q["query_valid"]);self.assertFalse(q["published"])
                    self.assertEqual(q["candidate"]["time_s"],row["time_s"])
                    old=paths[index].previous(q["position"])
                    self.assertEqual(state_hash(old),q["previous_history_sha256"])
                    steps=q["path_steps"] or [q]
                    for s in steps:
                        new=unpack(self.network,s["candidate"]);d=s["diagnostics"];h=d["actual_dt_s"]
                        self.assertGreaterEqual(h,1e-12)
                        self.assertEqual(new.previous,old.current);self.assertEqual(new.previous_dt_s,h)
                        self.assertEqual(new.time_s,old.time_s+h)
                        self.assertEqual(publication_check(self.network,old,new,h,d),s["publication"])
                        old=new
                    self.assertEqual(old,unpack(self.network,q["candidate"]))
                    self.assertLess(q["publication"]["max_published_kcl_a"],1e-11)
                    self.assertLess(q["publication"]["max_branch_equation_error_v"],1e-14)
                    self.assertTrue(q["publication"]["round_trip_exact"])
                    for s in q["path_steps"]:
                        self.assertFalse(s["published"])
                        self.assertGreaterEqual(s["diagnostics"]["actual_dt_s"],1e-12)
                        self.assertLess(s["publication"]["max_published_kcl_a"],1e-11)
                a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in row["queries"]]
                delta=np.abs(a-b)
                self.assertEqual(row["maximum_node_difference_v"],float(np.max(delta)))
                self.assertEqual(row["maximum_difference_node"],int(np.argmax(delta)))
            self.assertEqual(c["sampled_comparison"],metrics(c["rows"],c["end_s"]))
            self.assertEqual(c["sampled_prefix_comparison"],metrics(c["rows"],.0023))
            self.assertFalse(c["continuous_bound"])

    def test_peak_and_earlier_anchor_queries_and_fd_replay_canonically(self):
        for path,c in zip(OUTPUTS,self.payload["contrasts"]):
            reference=json.loads(gzip.decompress(path.read_bytes()))["case"]
            paths=[DomainPath(self.network,x) for x in (reference,self.case)]
            selected={c["sampled_comparison"]["maximum_difference_time_s"],c["landmarks"]["interpolated_peak"]}
            for row in c["rows"]:
                for index,q in enumerate(row["queries"]):
                    if row["time_s"] in selected or q["path_steps"]:
                        self.assertEqual(canonical(paths[index].query(row["time_s"])),canonical(q))
            for d in c["fd_observations"]:
                index=c["policies"].index(d["policy"])
                row=next(r for r in c["rows"] if r["time_s"]==d["time_s"])
                actual=fd_observation(self.network,paths[index],row["queries"][index])
                self.assertEqual(canonical(actual),canonical({k:v for k,v in d.items() if k not in ("landmark","policy")}))
                self.assertTrue(d["passed"])

    def test_storage_inputs_counts_and_fixed_tolerance_scope(self):
        p=self.payload;s=self.summary;raw=gzip.decompress(OUTPUT.read_bytes())
        self.assertEqual(canonical(p),raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),s["storage"]["canonical_json_sha256"])
        self.assertEqual(hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),s["storage"]["compressed_sha256"])
        self.assertEqual(p["source_sha256"],s["source_sha256"])
        for source,h in p["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),h)
        for c,summary in zip(p["contrasts"],s["contrasts"]):
            queries=[q for row in c["rows"] for q in row["queries"]]
            self.assertEqual(summary["queries"],len(queries))
            self.assertEqual(summary["invalid_queries"],sum(not q["query_valid"] for q in queries))
            self.assertEqual(summary["fd_distinct_cases"],len({(d["policy"],d["time_s"]) for d in c["fd_observations"]}))
            self.assertEqual(c["sampled_comparison"]["maximum_difference_gate_v"],1e-3)
        for key in ("trajectory_retimed","previous_reports_modified","temporal_refinement_admitted",
                    "temporal_error_bound_admitted","independent_spatial_oracle","physical_switching_admitted","audio_admitted"):
            self.assertFalse(p[key]);self.assertFalse(s[key])


if __name__=="__main__":unittest.main()
