import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_latch_transition_observations import sampled_crossings,aligned_difference,generate


class TransitionObservations(unittest.TestCase):
    def test_known_shift_changes_clock_time_without_changing_aligned_shape(self):
        t=np.array([0.,1.,2.]);v=np.tile(np.array([8.,4.,0.])[:,None],(1,94))
        a=sampled_crossings(t,v,0,4.)[0]
        b=sampled_crossings(t+.1,v,0,4.)[0]
        self.assertEqual(a["interpolated_time_s"],1.)
        self.assertAlmostEqual(b["interpolated_time_s"]-a["interpolated_time_s"],.1)
        result=aligned_difference(t,v,t+.1,v,a["interpolated_time_s"],b["interpolated_time_s"],2.)
        self.assertLess(result["maximum_node_difference_v"],1e-12)
        self.assertTrue(result["diagnostic_only"])
        self.assertFalse(result["published_trajectory_retimed"])
        rising=sampled_crossings(t,8.-v,0,4.,"rising")
        self.assertEqual(rising[0]["interpolated_time_s"],1.)
        self.assertGreater(rising[0]["sampled_slope_v_per_s"],0.)
        with self.assertRaises(ValueError):sampled_crossings(t,v,0,4.,"ambiguous")

    def test_multiple_crossings_are_reported_without_selecting_an_event(self):
        t=np.arange(5,dtype=float);v=np.array([[8.],[2.],[8.],[2.],[0.]])
        rows=sampled_crossings(t,v,0,4.)
        self.assertEqual(len(rows),2)
        for row in rows:
            self.assertLessEqual(row["left_s"],row["interpolated_time_s"])
            self.assertLessEqual(row["interpolated_time_s"],row["right_s"])
            self.assertLess(row["sampled_slope_v_per_s"],0.)

    def test_saved_observations_reproduce_and_preserve_original_failed_comparison(self):
        report=json.loads((ROOT/"evidence/loudness_latch_transition_observations.json").read_text())
        self.assertEqual(generate(),report)
        for path,h in report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        for flag in ("trajectory_modified","temporal_refinement_admitted","physical_switching_admitted","audio_admitted"):
            self.assertFalse(report[flag])
        for row in report["crossings"]+report["attack_out_crossings"]+report["fast_collector_crossings"]:
            for name in ("policy_a2","policy_b2"):
                for event in row[name]:
                    self.assertLessEqual(event["left_s"],event["interpolated_time_s"])
                    self.assertLessEqual(event["interpolated_time_s"],event["right_s"])


if __name__=="__main__":unittest.main()
