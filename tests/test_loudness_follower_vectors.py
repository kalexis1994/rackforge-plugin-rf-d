import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from loudness_follower_vectors import OUTPUT, generate, solve
from loudness_contour_reference import Network, Semiconductors


class LoudnessFollower(unittest.TestCase):
    def test_regenerate_sixty_independent_roots_and_tangents(self):
        self.assertEqual(generate(), json.loads(OUTPUT.read_text(encoding="utf-8")))

    def test_follower_matches_full_contour_equilibrium_under_same_boundaries(self):
        full, _ = Network().initial_state()
        boundary = dict(c2_v=full.node_v["TIMING_C2"], reset_base_v=full.node_v["RESET_BASE"],
                        supply_v=9.3, load_conductance_s=0.0, load_reference_v=0.0)
        x, current, _ = solve(boundary)
        from loudness_follower_vectors import NODES
        for name, voltage in zip(NODES, x):
            self.assertLess(abs(voltage-full.node_v[name]), 1e-6)
        self.assertGreater(current[0], 0)
        self.assertLess(x[3], 0)  # The conditioned off circuit is not a hard mute at 0 V.

    def test_output_loading_changes_input_current_and_voltage(self):
        boundary = dict(c2_v=6.0, reset_base_v=.7, supply_v=9.3,
                        load_conductance_s=0.0, load_reference_v=.7)
        unloaded, iu, _ = solve(boundary)
        loaded, il, _ = solve(dict(boundary, load_conductance_s=1/68000))
        self.assertLess(loaded[3], unloaded[3])
        self.assertGreater(il[0], iu[0])
        self.assertLess(il[2], 0)  # Port convention: current enters follower from load reference.


if __name__ == "__main__":
    unittest.main()
