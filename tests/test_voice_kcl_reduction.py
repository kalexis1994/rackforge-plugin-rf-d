"""Independent roots and row orientations for the exact scalar reduction."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_kcl_reduction as reduction


class ReductionTests(unittest.TestCase):
    def pair(self):
        return dict(solve=dict(new_98_v=1.,new_17_v=2.,new_16_v=3.,new_3_v=-1.,new_49_v=0.,new_current_a=.5),
                    inductor=dict(load=dict(req_ohm=1000.,veq_v=-10.)),conductance_s=.125,transconductance_s=.25)

    def test_known_root_with_all_rows_zero(self):
        p=self.pair();p['solve'].update(new_current_a=.25,new_17_v=-239.,new_16_v=-241.)
        m=reduction.evaluate(p)
        self.assertTrue(m['rational_identity_exact'])
        for key,value in m.items():
            if key!='rational_identity_exact':self.assertEqual(value,0)

    def test_signed_terms_sum_to_independent_root_gap(self):
        m=reduction.evaluate(self.pair())
        self.assertEqual(m['fixed_control_voltage_gap_16_v'],244.)
        self.assertEqual(m['current_constraint_amplified_v'],-252.)
        self.assertEqual(m['inductor_row_term_v'],491.)
        self.assertEqual(m['kcl17_term_v'],5.)


if __name__=='__main__':unittest.main()
