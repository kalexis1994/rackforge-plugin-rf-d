import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_union_refine_metrics as metrics
import voice_union_refine_runner as runner

VECTORS=['v(ramp_c1)','v(output)','@q[ic]']

def fixture():
    t=np.linspace(0,.04,80001)
    return np.column_stack((t,-3+5*np.mod(440*t,1),.1*np.sin(2*np.pi*440*t),np.full(len(t),.001)))

class UnionRefineTests(unittest.TestCase):
    def test_all_clock_vectors_exact(self):
        a=fixture();self.assertTrue(metrics.exact(a,a,VECTORS)['passed'])
        b=a.copy();b[100,3]+=1e-12;self.assertFalse(metrics.exact(a,b,VECTORS)['passed'])
    def test_complete_nominal_control(self):
        a=fixture();r=metrics.control(a,a,VECTORS)
        self.assertTrue(r['passed']);self.assertFalse(r['phase_alignment']);self.assertEqual(r['grid_points'],8001)
    def test_voltage_gate(self):
        a=fixture();b=a.copy();b[100:,2]+=.006
        self.assertFalse(metrics.control(b,a,VECTORS)['gates']['grid_voltage'])
    def test_dc_gate_separate(self):
        a=fixture();b=a.copy();b[0,2]+=2e-6
        r=metrics.control(b,a,VECTORS);self.assertFalse(r['gates']['dc_voltage']);self.assertTrue(r['gates']['grid_voltage'])
    def test_incomplete_control_cannot_interpolate_full_horizon(self):
        a=fixture()
        with self.assertRaises(ValueError):metrics.control(a[:-1],a,VECTORS)
    def test_duplicate_clock_and_nonfinite_rejected(self):
        a=fixture();b=a.copy();b[10,0]=b[9,0]
        with self.assertRaises(ValueError):runner.clock_info(b,VECTORS,.04,.5e-6)
        b=a.copy();b[10,2]=np.nan
        with self.assertRaises(ValueError):runner.clock_info(b,VECTORS,.04,.5e-6)
    def test_column_loss_rejected(self):
        with self.assertRaises(ValueError):runner.clock_info(fixture()[:,:-1],VECTORS,.04,.5e-6)
    def test_step_gate_separate_from_endpoint(self):
        a=fixture()[::2];r=runner.clock_info(a,VECTORS,.04,.5e-6)
        self.assertTrue(r['endpoint_complete']);self.assertFalse(r['max_step_passed'])
    def test_settled_frequency_is_required(self):
        a=fixture();a[:,1]=0
        with self.assertRaises(ValueError):metrics.control(a,a,VECTORS)
    def test_pitch_shift_rejected(self):
        a=fixture();b=a.copy();b[:,1]=-3+5*np.mod(445*b[:,0],1)
        self.assertFalse(metrics.control(b,a,VECTORS)['gates']['frequency'])
    def test_lost_reset_cannot_pass_by_matching_remaining_periods(self):
        a=fixture();b=a.copy();b[b[:,0]>=.038,1]=-3
        r=metrics.control(b,a,VECTORS)
        self.assertTrue(r['gates']['frequency']);self.assertFalse(r['gates']['reset_count'])
        self.assertIsNone(r['max_reset_time_difference_s'])
    def test_reset_delay_rejected_with_same_pitch_and_count(self):
        a=fixture();b=a.copy();select=b[:,0]>=.001
        b[select,1]=-3+5*np.mod(440*(b[select,0]-20e-9),1)
        r=metrics.control(b,a,VECTORS)
        self.assertTrue(r['gates']['frequency']);self.assertTrue(r['gates']['reset_count'])
        self.assertFalse(r['gates']['reset_timing'])
    def test_canonical_restore(self):
        self.assertEqual(runner.canonical({'clock':(1,2)}),runner.canonical({'clock':[1,2]}))

if __name__=='__main__':unittest.main()
