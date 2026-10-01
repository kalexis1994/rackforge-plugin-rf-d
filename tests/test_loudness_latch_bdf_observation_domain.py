import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_latch_bdf_observation_domain import DomainPath,MINIMUM_STEP_S,OUTPUT,SUMMARY,ORIGINAL,PREVIOUS,STRICT
from loudness_latch_bdf_sampling import metrics
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack,publication_check
from loudness_latch_bdf_survey import state_hash
from bjt_charge_ngspice_probes import model_parameters


class ObservationDomain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encoded=OUTPUT.read_bytes();cls.canonical=gzip.decompress(cls.encoded)
        cls.report=json.loads(cls.canonical);cls.summary=json.loads(SUMMARY.read_text())
        cls.original=json.loads(gzip.decompress(ORIGINAL.read_bytes()))
        previous=json.loads(gzip.decompress(PREVIOUS.read_bytes()))
        strict=json.loads(gzip.decompress(STRICT.read_bytes()))
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))
        cls.paths=[DomainPath(cls.network,c) for c in (previous["cases"][1],strict["case"])]

    def test_every_provisional_step_closes_kcl_and_conserves_intermediate_memory(self):
        n=self.network
        for row in self.report["rows"]:
            for p,q in zip(self.paths,row["queries"]):
                self.assertFalse(q["published"])
                old=p.previous(q["position"]);snapshot=state_hash(old)
                self.assertEqual(snapshot,q["previous_history_sha256"])
                for s in q["path_steps"]:
                    self.assertEqual(state_hash(old),s["previous_history_sha256"])
                    new=unpack(n,s["candidate"]);d=s["diagnostics"];h=d["actual_dt_s"]
                    self.assertGreaterEqual(h,MINIMUM_STEP_S);self.assertLessEqual(d["coefficients"]["ratio"],2.)
                    self.assertEqual(new.previous,old.current);self.assertEqual(new.time_s,old.time_s+h)
                    virtual,c=n.effective_history(old,h);delta=np.array(d["increment_v"])
                    residual,_=n.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(delta,False)
                    self.assertLess(np.max(np.abs(residual)),1e-11)
                    self.assertEqual(n.network.publish(delta,10.,virtual,c["effective_dt_s"]),new.current)
                    check=publication_check(n,old,new,h,d)
                    self.assertEqual(check,s["publication"]);self.assertLess(check["max_published_kcl_a"],1e-11)
                    self.assertLess(check["max_branch_equation_error_v"],1e-14);self.assertTrue(check["round_trip_exact"])
                    self.assertFalse(s["published"]);old=new
                self.assertEqual(state_hash(p.previous(q["position"])),snapshot)
                if q["query_valid"]:
                    candidate=unpack(n,q["candidate"])
                    self.assertEqual(candidate.time_s,row["time_s"])
                    self.assertGreaterEqual(q["diagnostics"]["actual_dt_s"],MINIMUM_STEP_S)
                    if q["path_steps"]:self.assertEqual(old,candidate)

    def test_only_sub_domain_remainders_use_an_earlier_anchor_and_times_never_move(self):
        r=self.report;o=self.original
        self.assertEqual([row["time_s"] for row in r["rows"]],[row["time_s"] for row in o["rows"]])
        for row,source in zip(r["rows"],o["rows"]):
            self.assertEqual(row["tags"],source["tags"])
            for p,q,original in zip(self.paths,row["queries"],source["queries"]):
                self.assertEqual(q["time_s"],original["time_s"])
                self.assertEqual(q["nearest_position"],original["position"])
                nearest=p.previous(original["position"]);gap=row["time_s"]-nearest.time_s
                self.assertEqual(q["requested_remainder_s"],gap)
                if q["source_query_reused"]:
                    self.assertEqual(q["candidate"],original["candidate"])
                    self.assertEqual(q["publication"],original["publication"])
                    self.assertEqual(q["position"],original["position"])
                    self.assertFalse(q["path_steps"])
                else:
                    self.assertLess(gap,MINIMUM_STEP_S)
                    self.assertEqual(q["position"],original["position"]-1)
                    self.assertEqual(len(q["path_steps"]),2)

    def test_first_middle_last_short_remainder_queries_replay_from_accepted_histories(self):
        for k,p in enumerate(self.paths):
            rows=[row for row in self.report["rows"] if not row["queries"][k]["source_query_reused"]]
            for index in sorted({0,len(rows)//2,len(rows)-1}):
                row=rows[index];stored=row["queries"][k]
                query=p.query(row["time_s"])
                self.assertEqual(unpack(self.network,query["candidate"]),unpack(self.network,stored["candidate"]))
                self.assertEqual(query["previous_history_sha256"],stored["previous_history_sha256"])
                self.assertEqual(query["publication"],stored["publication"])
                self.assertEqual(json.loads(json.dumps(query))["time_s"],row["time_s"])
                old=p.previous(stored["position"])
                for step in stored["path_steps"]:
                    h=step["diagnostics"]["actual_dt_s"]
                    candidate,diag=self.network.advance(old,10.,h,use_fd=True)
                    other=unpack(self.network,step["candidate"])
                    self.assertLess(np.max(np.abs(np.array(candidate.current.joint.node_v)-other.current.joint.node_v)),1e-8)
                    check=publication_check(self.network,old,candidate,h,diag)
                    self.assertLess(check["max_published_kcl_a"],1e-11)
                    old=candidate
            with self.assertRaises(ValueError):p.query(0.)

    def test_sampled_metrics_and_original_failed_admission_remain_separate(self):
        r=self.report;o=self.original
        self.assertEqual(r["sampled_full_comparison"],metrics(r["rows"],.003))
        self.assertEqual(r["sampled_prefix_comparison"],metrics(r["rows"],.0023))
        self.assertEqual(r["original_full_comparison"],o["original_full_comparison"])
        self.assertEqual(r["original_sampling_comparison"],o["sampled_full_comparison"])
        self.assertFalse(r["original_full_comparison"]["passed"])
        self.assertTrue(r["diagnostic_only"])
        for row in r["rows"]:
            if row["valid_both"]:
                a,b=[np.array(q["candidate"]["current"]["legacy"]["node_v"]) for q in row["queries"]]
                delta=np.abs(a-b)
                self.assertEqual(float(np.max(delta)),row["maximum_node_difference_v"])
                self.assertEqual(int(np.argmax(delta)),row["maximum_difference_node"])
        for flag in ("requested_times_modified","previous_reports_modified","trajectory_modified",
                     "temporal_refinement_admitted","temporal_error_bound_admitted","physical_switching_admitted","audio_admitted"):
            self.assertFalse(r[flag])

    def test_sources_storage_and_coverage_counts(self):
        r=self.report;s=self.summary
        self.assertEqual(hashlib.sha256(self.encoded).hexdigest(),s["compressed_sha256"])
        self.assertEqual(hashlib.sha256(self.canonical).hexdigest(),s["canonical_json_sha256"])
        for path,h in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        queries=[q for row in r["rows"] for q in row["queries"]]
        self.assertEqual(s["invalid_queries"],sum(not q["query_valid"] for q in queries))
        self.assertEqual(s["queries"],len(queries));self.assertEqual(s["observation_times"],len(r["rows"]))
        self.assertEqual(s["reused_queries"],sum(q["source_query_reused"] for q in queries))
        self.assertEqual(s["provisional_intervals"],sum(len(q["path_steps"]) for q in queries))
        self.assertEqual(s["invalid_queries"],0)
        self.assertTrue(r["sampled_prefix_comparison"]["passed"])


if __name__=="__main__":unittest.main()
