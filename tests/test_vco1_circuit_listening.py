"""Check nonuniform cycle integration and explicit audio-rate band limits."""
import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from render_vco1_circuit import coefficients,synthesize


class ListeningTests(unittest.TestCase):
    def test_constant_on_nonuniform_grid_has_only_dc(self):
        phase=np.array([0,1e-10,.12,.63,1.])
        c=coefficients(phase,np.full(5,2.7),10)
        self.assertAlmostEqual(c[0].real,2.7)
        self.assertLess(np.max(np.abs(c[1:])),1e-12)

    def test_piecewise_triangle_matches_analytic_fourier_coefficients(self):
        c=coefficients([0,.25,.75,1],[0,1,-1,0],9)
        self.assertLess(abs(c[0]),1e-15)
        for n in range(1,10):
            expected=-4j*np.sin(n*np.pi/2)/(np.pi*n)**2 if n%2 else 0
            self.assertLess(abs(c[n]-expected),1e-12)

    def test_linear_ramp_integral_preserves_harmonic_sign_and_level(self):
        c=coefficients([0,.03,.57,1],[-1,-.94,.14,1],8)
        self.assertLess(abs(c[0]),1e-15)
        np.testing.assert_allclose(c[1:],1j/(np.pi*np.arange(1,9)),rtol=0,atol=1e-12)

    def test_dc_is_removed_and_out_of_band_or_clipping_is_rejected(self):
        a=synthesize([100,.1],400)
        b=synthesize([-100,.1],400)
        np.testing.assert_array_equal(a,b)
        self.assertEqual(a[0],0)
        with self.assertRaises(ValueError): synthesize([0,1],24000)
        with self.assertRaises(ValueError): synthesize([0,100],400)
        with self.assertRaises(ValueError): coefficients([0,.5,.4,1],[0,1,0,0],4)


if __name__=="__main__": unittest.main()
