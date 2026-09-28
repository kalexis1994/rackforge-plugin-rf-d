"""Catch package/designator confusion before a transistor netlist uses it."""

import json
import unittest
from pathlib import Path


PINMAP = Path(__file__).resolve().parents[1] / "evidence" / "vco1_ic2_pinmap.json"


class Ca3046PinMapTests(unittest.TestCase):
    def test_pinmap_keeps_board_and_array_names_distinct(self) -> None:
        data = json.loads(PINMAP.read_text(encoding="utf-8"))
        self.assertEqual(data["package_designator"], "IC2")
        roles = {device["board_name"]: device for device in data["transistors"]}
        self.assertEqual(set(roles), {"Qa", "Qb", "Qc"})
        self.assertEqual((roles["Qa"]["collector"], roles["Qa"]["base"], roles["Qa"]["emitter"]), (5, 4, 3))
        self.assertEqual((roles["Qb"]["collector"], roles["Qb"]["base"], roles["Qb"]["emitter"]), (1, 2, 3))
        self.assertEqual((roles["Qc"]["collector"], roles["Qc"]["base"], roles["Qc"]["emitter"]), (14, 12, 13))
        self.assertEqual(data["substrate_pin"], roles["Qc"]["emitter"])

    def test_only_documented_pair_shares_an_emitter(self) -> None:
        data = json.loads(PINMAP.read_text(encoding="utf-8"))
        roles = data["transistors"]
        self.assertEqual([device["emitter"] for device in roles], [3, 3, 13])
        pins = [device[terminal] for device in roles for terminal in ("collector", "base", "emitter")]
        self.assertEqual(len(pins) - len(set(pins)), 1)
        self.assertEqual(data["verified_board_ties"][0]["pins"], [3, 14])


if __name__ == "__main__":
    unittest.main()
