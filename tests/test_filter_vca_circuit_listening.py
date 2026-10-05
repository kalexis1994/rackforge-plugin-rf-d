import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import render_filter_vca_circuit as render
import filter_vca_circuit_reference as f


class FilterVcaListeningTests(unittest.TestCase):
    def trace(self,drift=0):
        t=np.linspace(0,.08,16001)
        raw=np.zeros((len(t),len(f.VECTORS)+1));raw[:,0]=t
        raw[:,f.VECTORS.index('v(f4_main_output)')+1]=2+np.sin(2*np.pi*1000*t)+drift*t
        return raw

    def test_observed_cycle_keeps_dc_and_measured_amplitude(self):
        c,difference=render.output_cycle(self.trace(),1000)
        self.assertLess(difference,1e-12)
        self.assertAlmostEqual(c[0].real,2,places=10)
        self.assertLess(abs(c[1]+.5j),.0001)

    def test_nonstationary_output_cannot_be_repeated_as_stationary(self):
        with self.assertRaises(ValueError):render.output_cycle(self.trace(drift=10),1000)


if __name__=='__main__': unittest.main()
