from decimal import Decimal as D
from fractions import Fraction as F
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from circuit66_static_binary import prepare,evaluate,MODES
from loudness_latch_bdf_static_precision_binary import OUTPUT,SUMMARY,SOURCE
from loudness_latch_bdf_static_precision import derivative_metrics
from loudness_latch_bdf_fd_sensitivity import map_metrics
from loudness_latch_bdf_rational_solve import solve
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_doubling_survey import canonical


class BinaryStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.source=json.loads(gzip.decompress(SOURCE.read_bytes()))

    def test_prepared_reciprocals_preserve_graph_and_exact_remainders(self):
        before=canonical(self.source["graph"])
        for prepared,mode in zip(self.report["prepared_graphs"],MODES):
            self.assertEqual(canonical(prepare(self.source["graph"],mode)),canonical(prepared))
            for row in prepared["resistors"]:
                reciprocal=1/F.from_float(float(row["ohm"]));high=float(reciprocal)
                self.assertEqual(row["conductance_terms_s"][0],high)
                if mode==MODES[1]:self.assertEqual(row["conductance_terms_s"][1],float(reciprocal-F.from_float(high)))
                remaining=reciprocal-sum((F.from_float(v) for v in row["conductance_terms_s"]),F(0))
                self.assertEqual(float(remaining),row["remaining_reciprocal_error_s"])
            self.assertEqual(len(prepared["resistors"]),55)
        self.assertEqual(before,canonical(self.source["graph"]))
        with self.assertRaisesRegex(ValueError,"declared reciprocal"):prepare(self.source["graph"],"unknown")
        with self.assertRaisesRegex(ValueError,"finite static node"):evaluate(self.report["prepared_graphs"][0],[0.]*65)

    def test_all_eight_static_and_exact_maps_keep_ordinary_reset_failure(self):
        count=0;map_passes=0
        for case,base in zip(self.report["cases"],self.source["cases"]):
            self.assertEqual(case["window"],base["window"])
            self.assertEqual(case["node_candidate_v"],base["node_candidate_v"])
            ax=np.array(base["analytic"]["node_map"]);b=np.array(base["memory_rhs_s"])
            analytic=[[D(v) for v in line] for line in base["decimal80_audio_static_jacobian_s"]]
            for row,g in zip(case["rows"],self.report["prepared_graphs"]):
                count+=1;map_passes+=row["map_gate_passed"]
                self.assertEqual(row["mode"],g["reciprocal_mode"])
                r,j=evaluate(g,case["node_candidate_v"][:66])
                np.testing.assert_array_equal(r,row["audio_residual_a"])
                np.testing.assert_array_equal(j,row["audio_jacobian_s"])
                self.assertTrue(row["static_residual_gate_passed"])
                self.assertTrue(row["derivative_comparison"]["passed"])
                self.assertEqual(derivative_metrics(analytic,[[D.from_float(float(v)) for v in line] for line in j]),row["derivative_comparison"])
                solved=row["solve"];self.assertTrue(solved["passed"])
                matrix=np.array(solved["jacobian_s"]);x=np.array(solved["node_map"])
                exact,audit=solve(matrix,b);np.testing.assert_array_equal(exact,x)
                self.assertEqual(audit,solved["exact_solve"])
                _,errors=backward_errors(matrix,b,x);self.assertEqual(errors,solved["backward_errors"])
                self.assertLess(max(errors.values()),1e-10)
                metrics=map_metrics(ax,x);self.assertEqual(metrics,row["map_comparison"])
                self.assertEqual(row["map_gate_passed"],metrics["node_map_max_scaled_difference"]<1e-8)
                if case["window"]=="reset" and row["mode"]==MODES[0]:
                    self.assertFalse(row["map_gate_passed"])
                    self.assertGreater(metrics["node_map_max_scaled_difference"],1e-8)
                if row["mode"]==MODES[1]:self.assertTrue(row["map_gate_passed"])
        self.assertEqual(count,8);self.assertEqual(map_passes,7)

    def test_forty_eight_predictions_reuse_original_nonlinear_data_only(self):
        count=0
        for case,source in zip(self.report["cases"],self.source["cases"]):
            for row in case["rows"]:
                x=np.array(row["solve"]["node_map"])
                for comparison,direction in zip(row["reused_direction_comparisons"],source["directions"]):
                    count+=1
                    self.assertEqual(comparison["memory"],direction["memory"])
                    self.assertEqual(comparison["amplitude_v"],direction["amplitude_v"])
                    np.testing.assert_array_equal(comparison["central_v"],direction["comparisons"]["decimal-analytic"]["central_v"])
                    kick=np.zeros(25);kick[direction["memory"]]=direction["amplitude_v"]
                    predicted=x@((1+case["coefficients"]["gamma"])*kick)
                    np.testing.assert_array_equal(predicted,comparison["predicted_v"])
                    scaled=abs(np.array(comparison["central_v"])-predicted)/(1e-8+1e-3*abs(predicted))
                    self.assertEqual(float(np.max(scaled)),comparison["maximum_scaled_error"])
                    self.assertTrue(comparison["passed"])
        self.assertEqual(count,48)
        self.assertEqual(self.report["nonlinear_steps_new"],0)
        self.assertEqual(self.report["reused_nonlinear_steps"],48)
        self.assertEqual(self.report["reused_central_comparisons"],24)

    def test_canonical_storage_frozen_sources_and_no_integrator_promotion(self):
        raw=OUTPUT.read_bytes();s=json.loads(SUMMARY.read_text(encoding="utf-8"))["storage"]
        self.assertEqual(s["bytes"],len(raw));self.assertEqual(s["compressed_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(s["canonical_json_sha256"],hashlib.sha256(canonical(self.report)).hexdigest())
        self.assertEqual(gzip.decompress(raw),canonical(self.report))
        for name,expected in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)
        self.assertEqual(self.report["modes"],list(MODES))
        self.assertTrue(self.report["diagnostic_only"])
        for key in ("original_solver_modified","original_reset_fd_gate_closed","previous_reports_modified",
                    "physical_switching_admitted","temporal_error_bound_admitted","temporal_refinement_admitted",
                    "audio_admitted","deadline_admitted"):
            self.assertFalse(self.report[key])


if __name__=="__main__":unittest.main()
