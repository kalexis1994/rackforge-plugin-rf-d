import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_latch_bdf_static_precision_continuation import OUTPUT,SUMMARY,AUDIT,WINDOWS,candidate
from loudness_latch_bdf_static_precision_integrator import CompensatedBdfNetwork,CompensatedIncrementNetwork,VERSION
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_increment_reference import IncrementNetwork
from loudness_latch_bdf_probes import unpack,pack,publication_check
from loudness_latch_bdf_memory_transfer import node_difference,memory_difference
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling_survey import canonical
from bjt_charge_ngspice_probes import model_parameters


class CompensatedContinuation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.source=json.loads(gzip.decompress(WINDOWS.read_bytes()))
        cls.audit=json.loads(gzip.decompress(AUDIT.read_bytes()))
        params=model_parameters(1,"finite_transit")
        cls.original=BdfNetwork(200,params);cls.variant=CompensatedBdfNetwork(200,params)

    def test_all_320_residual_pairs_64_matrices_and_four_fd_paths(self):
        pairs=0;matrices=0;fd=0
        for w,base,static in zip(self.report["windows"],self.source["windows"],self.audit["windows"]):
            self.assertTrue(w["preflight_passed"])
            old=unpack(self.original,w["initial"])
            for row,step,stamp in zip(w["preflight"],base["reference"],static["rows"]):
                self.assertEqual(row["previous_history_sha256"],state_hash(old))
                virtual,c,_=candidate(old,step,self.original)
                a=self.original.network.increment_evaluator(10.,virtual,c["effective_dt_s"])
                b=self.variant.network.increment_evaluator(10.,virtual,c["effective_dt_s"])
                delta=np.array(step["diagnostics"]["increment_v"])
                for p in row["pairs"]:
                    d=delta.copy()
                    if p["node"] is not None:d[p["node"]]+=p["shift_v"]
                    ar,_=a(d,False);br,_=b(d,False)
                    np.testing.assert_array_equal(ar,p["original_residual_a"])
                    np.testing.assert_array_equal(br,p["candidate_residual_a"])
                    self.assertEqual(ar.tobytes(),br.tobytes());self.assertTrue(p["bits_equal"]);pairs+=1
                _,j=b(delta)
                self.assertEqual(j.tobytes(),np.array(stamp["binary"][1]["solve"]["jacobian_s"]).tobytes())
                self.assertTrue(row["jacobian_equal_to_compensated_audit"]);matrices+=1
                if "full_residual_fd_bits_equal" in row:
                    _,aj=a(delta,use_fd=True);_,bj=b(delta,use_fd=True)
                    self.assertEqual(aj.tobytes(),bj.tobytes());self.assertTrue(row["full_residual_fd_bits_equal"]);fd+=1
                old=unpack(self.original,step["history"])
        self.assertEqual((pairs,matrices,fd),(320,64,4))

    def test_saved_publications_clock_history_and_reference_comparisons(self):
        attempts=0
        for w,base in zip(self.report["windows"],self.source["windows"]):
            old=unpack(self.variant,w["initial"]);attempts+=w["attempted_intervals"]
            self.assertEqual(canonical(w["initial"]),canonical(base["initial"]))
            for r,step in zip(w["rows"],base["reference"]):
                self.assertEqual(state_hash(old),r["previous_history_sha256"])
                new=unpack(self.variant,r["history"]);reference=unpack(self.variant,step["history"])
                h=step["diagnostics"]["actual_dt_s"]
                pub=publication_check(self.variant,old,new,h,r["diagnostics"])
                self.assertEqual(canonical(pub),canonical(r["publication"]))
                passed=pub["round_trip_exact"] and pub["max_published_kcl_a"]<1e-11 and pub["max_branch_equation_error_v"]<1e-14
                self.assertEqual(passed,r["publication_passed"])
                self.assertLess(r["diagnostics"]["max_kcl_a"],1e-11)
                self.assertLess(r["diagnostics"]["correction_v"],1e-8)
                self.assertEqual(new.previous,old.current)
                self.assertEqual(new.time_s,reference.time_s);self.assertTrue(r["reference_time_equal"])
                nodes=node_difference(new.current,reference.current);memory=memory_difference(new.current,reference.current)
                np.testing.assert_array_equal(nodes,r["node_difference_v"])
                np.testing.assert_array_equal(memory,r["memory_difference_v"])
                self.assertEqual(float(np.max(abs(nodes))),r["max_node_difference_v"])
                self.assertEqual(float(np.max(abs(memory))),r["max_memory_coordinate_difference_v"])
                self.assertEqual(bool(np.max(abs(nodes))<1e-8),r["node_gate_passed"])
                self.assertEqual(bool(np.max(abs(memory))<1e-8),r["memory_gate_passed"])
                self.assertFalse(r["published"])
                if not passed:break
                old=new
            self.assertEqual(canonical(pack(old)),canonical(w["final"]))
            self.assertEqual(w["complete"],len(w["rows"])==16 and w["stop"] is None)
            if not w["complete"]:self.assertIsNotNone(w["stop"])
        self.assertGreater(attempts,0);self.assertLessEqual(attempts,64)

    def test_fresh_saved_step_replays_and_inherited_solver_contract(self):
        self.assertIs(CompensatedIncrementNetwork.step,IncrementNetwork.step)
        self.assertIs(CompensatedIncrementNetwork.publish,IncrementNetwork.publish)
        self.assertIs(CompensatedIncrementNetwork.linear,IncrementNetwork.linear)
        self.assertIs(CompensatedIncrementNetwork.validate,IncrementNetwork.validate)
        self.assertIs(CompensatedBdfNetwork.advance,BdfNetwork.advance)
        self.assertIs(CompensatedBdfNetwork.effective_history,BdfNetwork.effective_history)
        count=0
        for w in self.report["windows"]:
            if not w["rows"]:continue
            for index in sorted({0,len(w["rows"])-1}):
                r=w["rows"][index]
                incoming=w["initial"] if index==0 else w["rows"][index-1]["history"]
                old=unpack(self.variant,incoming);before=state_hash(old)
                new,d=self.variant.advance(old,10.,r["diagnostics"]["actual_dt_s"])
                self.assertEqual(canonical(pack(new)),canonical(r["history"]))
                self.assertEqual(canonical(d),canonical(r["diagnostics"]))
                self.assertEqual(before,state_hash(old));count+=1
            old=unpack(self.variant,w["initial"])
            with self.assertRaisesRegex(ValueError,"positive integer offline budgets"):
                self.variant.advance(old,10.,w["rows"][0]["diagnostics"]["actual_dt_s"],iterations=0)
        self.assertGreaterEqual(count,4)

    def test_canonical_sources_fixed_gates_and_no_global_promotion(self):
        raw=OUTPUT.read_bytes();s=json.loads(SUMMARY.read_text(encoding="utf-8"))["storage"]
        self.assertEqual(s["bytes"],len(raw));self.assertEqual(s["compressed_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(gzip.decompress(raw),canonical(self.report))
        self.assertEqual(s["canonical_json_sha256"],hashlib.sha256(canonical(self.report)).hexdigest())
        for name,expected in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        self.assertEqual(self.report["candidate_version"],VERSION)
        self.assertEqual(self.report["planned_intervals"],64);self.assertEqual(self.report["planned_residual_pairs"],320)
        self.assertEqual(self.report["history_reset_count"],0);self.assertTrue(self.report["diagnostic_only"])
        for k,v in dict(node_comparison_gate_v=1e-8,memory_coordinate_gate_v=1e-8,fixed_kcl_gate_a=1e-11,
                        fixed_correction_gate_v=1e-8,branch_equation_gate_v=1e-14).items():self.assertEqual(self.report[k],v)
        for k in ("trajectory_retimed","adaptive_controller_applied","original_solver_modified",
                  "original_reset_fd_gate_closed","previous_reports_modified","physical_switching_admitted",
                  "temporal_error_bound_admitted","temporal_refinement_admitted","full_dc_trajectory_admitted",
                  "audio_admitted","deadline_admitted"):self.assertFalse(self.report[k])


if __name__=="__main__":unittest.main()
