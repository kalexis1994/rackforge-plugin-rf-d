import json
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_port_relaxation as p


class PortTests(unittest.TestCase):
    def test_approximation_preserves_fast_reset_and_endpoints(self):
        t=np.r_[np.linspace(0,.001,101),.001000001,.001000002,np.linspace(.001001,.004,100)]
        x=np.where(t<=.001,t*1000,np.where(t<=.001000002,(.001000002-t)/2e-9,0))
        tt,xx,m=p.simplify(t,x)
        self.assertEqual((tt[0],tt[-1]),(t[0],t[-1]))
        self.assertLessEqual(np.max(np.abs(x-np.interp(t,tt,xx))),p.GATES['pwl_v'])
        self.assertIn(.001000002,tt)
        self.assertLess(m['retained_knots'],len(t))

    def test_approximation_checks_all_polyline_vertices(self):
        rng=np.random.default_rng(204)
        t=np.r_[0,np.cumsum(rng.uniform(1e-9,1e-6,1000))];x=rng.normal(size=len(t))
        tt,xx,_=p.simplify(t,x,1e-3)
        union=np.union1d(t,tt)
        self.assertLessEqual(np.max(np.abs(np.interp(union,t,x)-np.interp(union,tt,xx))),1e-3)

    def test_invalid_histories_reject(self):
        for t,x in (([0,0],[1,2]),([1,2],[1,2]),([0,1],[1,np.nan]),([0,1],[1]),([0],[1])):
            with self.assertRaises(ValueError):p.simplify(t,x)
        for tol in (0,-1,np.nan,np.inf):
            with self.assertRaises(ValueError):p.simplify([0,1],[0,1],tol)

    def test_split_keeps_physical_resistor_and_removes_fixture(self):
        s=p.coupled.Scenario()
        for side in ('vco','board'):
            fn,_=p.factory(s,side,[0,.04],[.7,.8],False);deck,meta=fn(s,p.ROOT/'artifacts/test.txt')
            self.assertEqual(deck.count('R45_PANEL '),1)
            self.assertIn(' 33000',deck)
            self.assertNotIn('Vfixture ',deck);self.assertNotIn('Rfixture ',deck)
            self.assertTrue(meta['iteration_boundary']);self.assertFalse(meta['port_closed'])
            self.assertEqual(json.dumps(meta,sort_keys=True),json.dumps(json.loads(json.dumps(meta)),sort_keys=True))

    def test_contour_retains_loaded_node_and_capacitors(self):
        s=p.coupled.Scenario();fn,_=p.factory(s,'board',[0,.04],[0,0],True)
        deck,_=fn(s,p.ROOT/'artifacts/test.txt')
        self.assertNotIn('VF4_contour ',deck)
        self.assertIn('CE2_C2 E2_TIMING_C2 0 1.0000000000000001e-05',deck)
        self.assertIn('F4_LOUDNESS_CONTOUR',deck);self.assertIn('QF4_Q18 ',deck)
        self.assertIn('QE2_Q25 ',deck);self.assertIn('QE2_Q15 ',deck)

    def pair(self):
        vt=np.array([0,.001,.04]);bt=np.array([0,.002,.04])
        v=np.zeros((3,len(p.VCO_VECTORS)+1));b=np.zeros((3,len(p.BOARD_VECTORS)+1))
        v[:,0]=vt;b[:,0]=bt
        v[:,p.VCO_VECTORS.index('v(r6_wiper)')+1]=1
        v[:,p.VCO_VECTORS.index('v(mix_bus_board4_pin4)')+1]=.5
        b[:,1]=.5
        v[:,-1]=.5/33000;b[:,-1]=-.5/33000
        return v,b

    def test_opposite_current_signs_close_different_clocks(self):
        v,b=self.pair();m=p.closure(v,b,p.BOARD_VECTORS)
        self.assertTrue(m['passed']);self.assertEqual(m['union_knots'],4)

    def test_voltage_current_and_resistor_defects_reject_independently(self):
        for column,delta,side in ((1,20e-6,'b'),(-1,2e-9,'b'),(-1,2e-9,'v')):
            v,b=self.pair();(b if side=='b' else v)[1,column]+=delta
            self.assertFalse(p.closure(v,b,p.BOARD_VECTORS)['passed'])

    def test_closure_rejects_nonfinite_or_truncated_history(self):
        v,b=self.pair();b[-1,0]=.039
        with self.assertRaises(ValueError):p.closure(v,b,p.BOARD_VECTORS)

    def test_export_endpoint_rounding_keeps_common_domain(self):
        v,b=self.pair();b[-1,0]=np.nextafter(.04,0)
        self.assertTrue(p.closure(v,b,p.BOARD_VECTORS)['passed'])
        s=p.coupled.Scenario();fn,_=p.factory(s,'vco',b[:,0],b[:,1],False)
        _,meta=fn(s,p.ROOT/'artifacts/test.txt')
        self.assertEqual(meta['terminal_rounding_s'],.04-b[-1,0])
        with self.assertRaises(ValueError):p.factory(s,'vco',[0,.039],[0,0],False)
        v,b=self.pair();b[1,2]=np.nan
        with self.assertRaises(ValueError):p.closure(v,b,p.BOARD_VECTORS)


if __name__=='__main__':unittest.main()
