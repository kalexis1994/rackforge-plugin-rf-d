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
from loudness_latch_bdf_sampling import SavedPath,metrics,FIXED_TIMES_S,OUTPUT,SUMMARY,PREVIOUS,STRICT


class BdfSampling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encoded=OUTPUT.read_bytes();cls.canonical=gzip.decompress(cls.encoded)
        cls.report=json.loads(cls.canonical);cls.summary=json.loads(SUMMARY.read_text())
        cls.previous=json.loads(gzip.decompress(PREVIOUS.read_bytes()))
        cls.strict=json.loads(gzip.decompress(STRICT.read_bytes()))
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))
        cls.paths=[SavedPath(cls.network,c) for c in (cls.previous["cases"][1],cls.strict["case"])]

    def test_all_queries_close_charge_kcl_without_publishing_or_retiming(self):
        n=self.network
        for row in self.report["rows"]:
            self.assertEqual(row["valid_both"],all(q["query_valid"] for q in row["queries"]))
            for p,q in zip(self.paths,row["queries"]):
                old=p.previous(q["position"]);snapshot=state_hash(old)
                self.assertEqual(snapshot,q["previous_history_sha256"]);self.assertFalse(q["published"])
                if not q["query_valid"]:
                    self.assertTrue("error" in q or "publication" in q);continue
                new=unpack(n,q["candidate"]);d=q["diagnostics"];h=d["actual_dt_s"]
                self.assertEqual(new.time_s,row["time_s"]);self.assertEqual(new.previous,old.current)
                self.assertEqual(new.time_s,old.time_s+h)
                if q["query_method"].startswith("unpublished-"):
                    self.assertEqual(h,row["time_s"]-old.time_s)
                if old.previous is None:virtual,dt=old.current,h
                else:virtual,c=n.effective_history(old,h);dt=c["effective_dt_s"]
                delta=np.array(d["increment_v"])
                residual,_=n.network.increment_evaluator(10.,virtual,dt)(delta,False)
                self.assertLess(np.max(np.abs(residual)),1e-11)
                self.assertEqual(n.network.publish(delta,10.,virtual,dt),new.current)
                check=publication_check(n,old,new,h,d)
                self.assertEqual(check,q["publication"]);self.assertLess(check["max_published_kcl_a"],1e-11)
                self.assertLess(check["max_branch_equation_error_v"],1e-14);self.assertTrue(check["round_trip_exact"])
                interpolated=np.array([np.interp(row["time_s"],p.times,p.volts[:,k]) for k in range(94)])
                difference=interpolated-np.array(new.current.joint.node_v)
                self.assertEqual(list(difference),q["interpolation_difference_v"])
                self.assertEqual(float(np.max(np.abs(difference))),q["max_interpolation_difference_v"])
                self.assertEqual(snapshot,state_hash(old))

    def test_fixed_grid_midpoints_and_peak_times_are_all_retained(self):
        r=self.report
        fixed=[t for t in FIXED_TIMES_S if r["start_s"]<=t<=r["end_s"]]
        self.assertEqual(fixed,r["fixed_grid_times_s"])
        mids=[p.midpoints(r["start_s"],r["end_s"]) for p in self.paths]
        self.assertEqual(mids,r["midpoint_times_s"])
        times=sorted(set(fixed+sum(mids,[])+list(r["landmarks"].values())))
        self.assertEqual(times,[q["time_s"] for q in r["rows"]])
        for p in self.paths:
            with self.assertRaises(ValueError):p.query(0.)
            with self.assertRaises(ValueError):p.query(p.times[-1]+1e-6)
            time=np.float64(p.midpoints(r["start_s"],r["end_s"])[0])
            query=p.query(time)
            self.assertIs(type(query["time_s"]),float)
            self.assertIs(type(query["query_valid"]),bool)
            self.assertEqual(json.loads(json.dumps(query))["time_s"],float(time))
        for row in r["rows"]:
            if row["valid_both"]:
                a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in row["queries"]]
                delta=np.abs(a-b)
                self.assertEqual(float(np.max(delta)),row["maximum_node_difference_v"])
                self.assertEqual(int(np.argmax(delta)),row["maximum_difference_node"])

    def test_fd_landmarks_close_and_their_histories_replay(self):
        n=self.network;r=self.report
        for fd in r["fd_landmarks"]:
            row=next(row for row in r["rows"] if row["time_s"]==fd["time_s"])
            k=("B3","C3").index(fd["policy"]);q=row["queries"][k]
            old=self.paths[k].previous(q["position"]);snapshot=state_hash(old)
            new,diag=n.advance(old,10.,fd["time_s"]-old.time_s,use_fd=True)
            self.assertEqual(new,unpack(n,fd["candidate"]));self.assertEqual(diag,fd["diagnostics"])
            self.assertEqual(publication_check(n,old,new,diag["actual_dt_s"],diag),fd["publication"])
            other=unpack(n,q["candidate"])
            difference=float(np.max(np.abs(np.array(new.current.joint.node_v)-other.current.joint.node_v)))
            self.assertEqual(difference,fd["max_node_difference_v"])
            self.assertLess(difference,1e-8);self.assertTrue(fd["passed"])
            self.assertEqual(snapshot,state_hash(old))

    def test_sampled_gate_does_not_change_original_global_gate_or_claim_a_bound(self):
        r=self.report
        self.assertEqual(metrics(r["rows"],r["end_s"]),r["sampled_full_comparison"])
        self.assertEqual(metrics(r["rows"],.0023),r["sampled_prefix_comparison"])
        self.assertEqual(r["original_full_comparison"],self.strict["refinement"])
        self.assertTrue(r["diagnostic_only"])
        for flag in ("previous_reports_modified","trajectory_modified","temporal_error_bound_admitted",
                     "temporal_refinement_admitted","physical_switching_admitted","audio_admitted"):
            self.assertFalse(r[flag])
        self.assertFalse(r["sampled_full_comparison"]["continuous_bound"])

    def test_lossless_storage_sources_and_failures_are_counted(self):
        r=self.report;s=self.summary
        self.assertEqual(hashlib.sha256(self.encoded).hexdigest(),s["compressed_sha256"])
        self.assertEqual(hashlib.sha256(self.canonical).hexdigest(),s["canonical_json_sha256"])
        for path,digest in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
        self.assertEqual(s["queries"],2*len(r["rows"]))
        self.assertEqual(s["invalid_queries"],sum(not q["query_valid"] for row in r["rows"] for q in row["queries"]))


if __name__=="__main__":unittest.main()
