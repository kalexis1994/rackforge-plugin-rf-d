import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from cutoff_native_vectors import OUTPUT,generate_vectors
from cutoff_ebers_moll_reference import solve_dc
from filter_cutoff_coupled_dc_reference import conditional_coupled_cutoff_dc

class CutoffNativeVectors(unittest.TestCase):
    def test_vectors_regenerate_and_include_bc_forward_bias(self):
        data = generate_vectors()
        self.assertEqual(json.loads(OUTPUT.read_text(encoding="utf-8")),data)
        self.assertTrue(any(row["devices"]["Q28"]["v_bc_v"]>0
            for case in data["cases"] for row in case["rows"]))

    def test_nominal_point_matches_active_limit(self):
        panel = dict(cutoff_fraction_from_neg10=0.5,scale_active_ohm=250,contour_pin16_v=0)
        device = dict(is_a=1e-14,beta_forward=100,beta_reverse=5,temperature_k=298.15)
        full = solve_dc(panel=panel,range_fraction=0.1,tail_v=2,q26=device,q28=device)
        old = conditional_coupled_cutoff_dc(panel_inputs=panel,
            range_fraction_from_ground=0.1,is26_a=1e-14,is28_a=1e-14,
            beta26=100,beta28=100,temperature_k=298.15,tail_v=2)
        self.assertAlmostEqual(full["current_a"],old["q28_collector_current_a_candidate"],delta=1e-11)

if __name__=="__main__":unittest.main()
