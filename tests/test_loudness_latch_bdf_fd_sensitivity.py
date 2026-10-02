import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_bdf_fd_sensitivity import OUTPUT, SUMMARY, FD_SOURCE, STEPS_V, MODES, matrices, map_metrics
from loudness_latch_bdf_transfer_solve import backward_errors
from loudness_latch_bdf_rational_solve import solve


class FdSensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(gzip.decompress(OUTPUT.read_bytes()))
        cls.frozen = json.loads(gzip.decompress(FD_SOURCE.read_bytes()))
        cls.network = BdfNetwork(200, model_parameters(1, "finite_transit"))

    def test_original_four_matrices_and_reset_failure_replay_exactly(self):
        for case, frozen in zip(self.report["cases"], self.frozen["rows"]):
            self.assertEqual(case["window"], frozen["window"])
            old = unpack(self.network, case["initial"])
            step = case["reference_step"]; new = unpack(self.network, step["history"])
            fd = matrices(self.network, old, new, step["diagnostics"], 1e-6)
            row = next(r for r in case["rows"] if r["step_v"] == 1e-6 and r["mode"] == MODES[0])
            np.testing.assert_array_equal(fd["full"], frozen["fd_jacobian_s"])
            np.testing.assert_array_equal(row["jacobian_s"], frozen["fd_jacobian_s"])
            np.testing.assert_array_equal(row["node_map"], frozen["node_map"])
            self.assertTrue(row["original_j_and_x_reproduced_exactly"])
            self.assertEqual(row["passed"], frozen["passed"])
        reset = next(c for c in self.report["cases"] if c["window"] == "reset")
        self.assertFalse(reset["original_fd_passed"])
        self.assertGreater(reset["original_fd_scaled_difference"], 1e-8)

    def test_all_forty_gates_and_exact_reset_eliminations(self):
        count = 0; passed = 0
        for case in self.report["cases"]:
            b = np.array(case["memory_rhs_s"]); mixed = np.array(case["mixed_node_map"])
            self.assertEqual([(r["step_v"], r["mode"]) for r in case["rows"]],
                [(h, mode) for h in STEPS_V for mode in MODES])
            for row in case["rows"]:
                count += 1; passed += row["passed"]
                self.assertNotIn("error", row)
                j = np.array(row["jacobian_s"]); x = np.array(row["node_map"])
                _, errors = backward_errors(j, b, x)
                self.assertLess(max(errors.values()), 1e-10)
                self.assertEqual(errors, row["backward_errors"])
                self.assertTrue(row["exact_solve"]["exact_rational_residual_zero"])
                metrics = map_metrics(mixed, x)
                for key, value in metrics.items():
                    self.assertEqual(row[key], value)
                self.assertEqual(row["passed"], metrics["node_map_max_scaled_difference"] < 1e-8)
                coords = row["coordinate_errors"]
                self.assertEqual([r["column"] for r in coords], list(range(94)))
                self.assertTrue(all(np.isfinite(v) and v >= 0 for r in coords for k, v in r.items() if k != "column"))
                if case["window"] == "reset":
                    self.assertFalse(row["passed"])
                    exact, audit = solve(j, b)
                    np.testing.assert_array_equal(exact, x)
                    self.assertEqual(audit, row["exact_solve"])
        self.assertEqual(count, 40)
        self.assertEqual(passed, 6)

    def test_storage_input_identities_and_declared_scope(self):
        summary = json.loads(SUMMARY.read_text(encoding="utf-8")); storage = summary["storage"]
        raw = OUTPUT.read_bytes()
        self.assertEqual(storage["bytes"], len(raw))
        self.assertEqual(storage["compressed_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(storage["canonical_json_sha256"], hashlib.sha256(canonical(self.report)).hexdigest())
        self.assertEqual(gzip.decompress(raw), canonical(self.report))
        for name, sha in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), sha, name)
        self.assertEqual(self.report["steps_v"], list(STEPS_V))
        self.assertEqual(self.report["modes"], list(MODES))
        self.assertEqual(self.report["hypothetical_nonlinear_steps"], 0)
        self.assertTrue(self.report["diagnostic_only"])
        self.assertEqual(self.report["scaled_map_gate"], 1e-8)
        self.assertEqual(self.report["binary_and_decimal_backward_gate"], 1e-10)
        for key in ("new_step_selected", "previous_reports_modified", "original_reset_map_gate_closed",
                    "temporal_error_bound_admitted", "temporal_refinement_admitted", "physical_switching_admitted", "audio_admitted"):
            self.assertFalse(self.report[key])


if __name__ == "__main__":
    unittest.main()
