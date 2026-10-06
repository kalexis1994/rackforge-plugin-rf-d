from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from diagnose_voice_full_note import prefix,OBS

VECTORS=list(OBS)+['v(ramp_c1)']

class PrefixTests(unittest.TestCase):
    def raw(self,end):
        t=np.arange(round(end/1e-5)+1)*1e-5
        a=np.zeros((len(t),len(VECTORS)+1));a[:,0]=t;a[:,-1]=-3+5*np.mod(440*t,1)
        return a
    def test_partial_export_bounds_all_observations(self):
        a=self.raw(.35);b=self.raw(.01594);r=prefix(a,b,VECTORS)
        self.assertLessEqual(r['grid_endpoint_s'],b[-1,0]);self.assertFalse(r['full_horizon_measured'])
        self.assertFalse(r['admission']);self.assertEqual(max(r['voltage_maxima_v'].values()),0)
    def test_future_difference_is_not_extrapolated_into_prefix(self):
        a=self.raw(.35);b=self.raw(.01594);a[a[:,0]>.02,1]=100
        self.assertEqual(max(prefix(a,b,VECTORS)['voltage_maxima_v'].values()),0)
    def test_no_phase_alignment_hides_reset_delay(self):
        a=self.raw(.02);b=a.copy();selected=b[:,0]>=.001
        b[selected,-1]=-3+5*np.mod(440*(b[selected,0]-1e-6),1)
        r=prefix(a,b,VECTORS);self.assertFalse(r['phase_alignment'])
        self.assertGreater(r['max_reset_time_difference_s'],.9e-6)
    def test_duplicate_clock_rejected(self):
        a=self.raw(.02);a[10,0]=a[9,0]
        with self.assertRaises(ValueError):prefix(a,a,VECTORS)
    def test_complete_observation_still_does_not_admit(self):
        a=self.raw(.35);r=prefix(a,a,VECTORS)
        self.assertTrue(r['full_horizon_measured']);self.assertFalse(r['admission'])

if __name__=='__main__':unittest.main()
