"""Two real trim tracks and reserved pitches in the archived circuit solve."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from vco1_circuit_calibration import validate,bounded_update


class CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=ROOT/"evidence/vco1_circuit_calibration_v1.json.gz"
        info=json.loads((ROOT/"evidence/vco1_circuit_calibration_storage.json").read_text(encoding="utf-8"))
        data=p.read_bytes();raw=gzip.decompress(data)
        if hashlib.sha256(data).hexdigest()!=info["compressed_sha256"] or hashlib.sha256(raw).hexdigest()!=info["uncompressed_sha256"]:
            raise ValueError("calibration archive changed")
        cls.report=json.loads(raw)

    def test_four_final_notes_follow_same_two_trims(self):
        validate(self.report)
        self.assertTrue(self.report["passed"])
        self.assertEqual(len(self.report["trials"]),14)
        self.assertEqual(self.report["source_sha256"],self.report["source_sha256_after"])
        # Final intermediate points were excluded from the ten search runs.
        for t in self.report["trials"][:10]:
            self.assertIn(t["receipt"]["scenario"]["keyboard_v"],[-3.1,-.1])
        for t in self.report["trials"]:
            self.assertEqual(t["receipt"]["source_sha256"],t["receipt"]["source_sha256_after"])
            self.assertEqual(t["receipt"]["exit_code"],0)
        self.assertGreater(self.report["verification"]["middle1"]["error_cents"],3)
        self.assertGreater(self.report["verification"]["middle2"]["error_cents"],4)

    def test_calibration_never_clamps_a_trim_to_hide_an_invalid_update(self):
        np.testing.assert_allclose(bounded_update([.5,.3],[.1,-.1]),[.6,.2])
        for delta in ([1,0],[0,-1],[float("nan"),0]):
            with self.assertRaises(ValueError): bounded_update([.5,.3],delta)

    def test_wrong_reserved_pitch_or_scene_fails(self):
        for change in ("pitch","trim","step"):
            r=copy.deepcopy(self.report)
            if change=="pitch": r["verification"]["middle1"]["measurements"]["frequency_hz"]=450
            if change=="trim": r["verification"]["middle1"]["receipt"]["scenario"]["r8_fraction"]=.5
            if change=="step": r["verification"]["middle1"]["receipt"]["scenario"]["max_step_s"]=1e-6
            with self.assertRaises(ValueError): validate(r)


if __name__=="__main__": unittest.main()
