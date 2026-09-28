"""Evidence integrity and the conditional incremental summing relation."""

import math
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vco1_cv_reference import ideal_ic1_delta_v, load_evidence  # noqa: E402


class CvSummerTests(unittest.TestCase):
    def test_designators_and_actual_discrepancy(self) -> None:
        data = load_evidence()
        parts = {part["ref"]: part for part in data["components"]}
        self.assertEqual(parts["R21"]["source_node"], "TUNE")
        self.assertEqual(parts["R21"]["schematic"], parts["R21"]["bom"])
        self.assertEqual(parts["R2"]["role"], "pulse_former")
        self.assertEqual(parts["Q5"]["status"], "conflict")
        self.assertEqual(parts["Q6"]["status"], "conflict")

    def test_one_volt_keyboard_increment_and_superposition(self) -> None:
        keyboard = ideal_ic1_delta_v({"KEYBOARD": 1.0})
        tune = ideal_ic1_delta_v({"TUNE": 1.0})
        both = ideal_ic1_delta_v({"KEYBOARD": 1.0, "TUNE": 1.0})
        self.assertAlmostEqual(keyboard, -1000 / 51100)
        self.assertAlmostEqual(tune, -1000 / 560000)
        self.assertTrue(math.isclose(both, keyboard + tune, abs_tol=1e-15))

    def test_bad_evidence_is_rejected_before_calculation(self) -> None:
        original = load_evidence()
        duplicate = deepcopy(original)
        duplicate["components"].append(deepcopy(duplicate["components"][0]))
        # The loader is path based; this is the same invariant checked there.
        # Test via a temporary manifest to catch accidental duplicate labels.
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "parts.json"
            path.write_text(json.dumps(duplicate), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate designator"):
                load_evidence(path)

    def test_unknown_and_nonfinite_control_voltage_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ideal_ic1_delta_v({"R2": 1.0})
        with self.assertRaises(ValueError):
            ideal_ic1_delta_v({"KEYBOARD": float("nan")})


if __name__ == "__main__":
    unittest.main()
