import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from circuit66_vca_release_probes import OUTPUT, generate_vectors
import circuit66_vca_release_probes as probes


class VcaReleaseProbes(unittest.TestCase):
    def test_voltage_policy_capture_passes_independent_kcl_and_correction_audit(self):
        root = Path(__file__).resolve().parents[1]
        frozen = json.loads((root/"evidence/circuit66_vca_release_voltage_probe_vectors.json").read_text(encoding="utf-8"))
        with patch.object(probes,"INPUT",root/"evidence/circuit66_vca_release_voltage_survey.json"):
            report = generate_vectors()
        self.assertEqual(report,frozen)
        self.assertTrue(report["passed"])
        self.assertEqual(report["failed_probes"],0)
        self.assertEqual(len(report["probes"]),96)

    def test_independent_refinement_regenerates_including_failed_internal_gates(self):
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        report = generate_vectors()
        self.assertEqual(report,frozen)
        self.assertEqual(len(report["probes"]),96)
        # Historical native capture deliberately remains inadmissible. This
        # regression checks the diagnostic, not a future solver's fail count.
        self.assertFalse(report["passed"])
        self.assertEqual(report["failed_probes"],20)
        for p in report["probes"]:
            self.assertLess(p["native_comparison"]["oracle_kcl_a"],1e-11)
            self.assertLess(p["native_comparison"]["oracle_correction_v"],1e-8)
            self.assertLess(p["native_comparison"]["jack_error_v"],1e-6)
            self.assertLess(p["native_comparison"]["capacitor_error_v"],1e-6)


if __name__ == "__main__":
    unittest.main()
