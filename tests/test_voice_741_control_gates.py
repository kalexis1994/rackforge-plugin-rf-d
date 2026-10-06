"""Control failures must remain failures; incomplete clocks cannot be admitted."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from voice_741_row_compare import compare


class ControlTests(unittest.TestCase):
    def trace(self):
        t=np.linspace(0,.04,16001);r=-2+np.sin(2*np.pi*220*t)
        return np.column_stack((t,r,np.zeros((len(t),5))))

    def test_complete_identical_trace_passes(self):
        a=self.trace();self.assertTrue(compare(a,a)['passed'])

    def test_voltage_gate_independent_of_frequency(self):
        a=self.trace();b=a.copy();b[:,3]=.006
        m=compare(b,a);self.assertFalse(m['passed']);self.assertFalse(m['gates']['grid_voltage'])
        self.assertTrue(m['gates']['frequency'])

    def test_dc_gate_not_hidden_by_grid_tolerance(self):
        a=self.trace();b=a.copy();b[:,4]=2e-6
        m=compare(b,a);self.assertFalse(m['gates']['dc_voltage']);self.assertTrue(m['gates']['grid_voltage'])

    def test_partial_clock_rejected(self):
        a=self.trace()
        with self.assertRaises(ValueError):compare(a[:-1],a)


if __name__=='__main__':unittest.main()
