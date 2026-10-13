import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from render_conditioned_recipe import filtered,quantize,VOLTS_PER_FS

class FiniteTransientAdapter(unittest.TestCase):
    def test_constant_signal_preserves_voltage_at_both_edges_and_inside(self):
        t=np.array([0.,.000001,.00009,.0017,.003004]);v=np.full(len(t),.003)
        for order in [8,16]:
            actual=filtered(t,v,np.array([0.,.000001,.0003,.0015,.003004]),order)
            self.assertLess(float(np.max(abs(actual-.003))),1e-12)
    def test_invalid_clocks_and_clipping_reject_before_pcm(self):
        for t in [[0.,0.,.003],[0.,.003,.002],[0.,np.nan,.003]]:
            with self.assertRaises(ValueError):filtered(t,[0.,.001,0.],[.001])
        with self.assertRaises(ValueError):filtered([0.,.001,.003],[0.,.001,0.],[.004])
        for value in [VOLTS_PER_FS,-VOLTS_PER_FS,np.nan]:
            with self.assertRaises(ValueError):quantize(np.array([value]))
if __name__=='__main__':unittest.main()
