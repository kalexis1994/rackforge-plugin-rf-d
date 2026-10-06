from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import loudness_voice_circuit as c


class CoupledContourTests(unittest.TestCase):
    def test_physical_join_has_no_wave_or_envelope_source(self):
        s=c.Scenario();deck,meta=c.netlist(s,c.ROOT/'artifacts/test.txt')
        self.assertNotIn('Vmixer ',deck);self.assertNotIn('VF4_contour ',deck)
        self.assertNotIn('Vfixture ',deck)
        self.assertEqual(deck.count('R45_PANEL '),1)
        self.assertEqual(deck.count('CE2_C2 '),1)
        self.assertEqual(deck.count('CF4_C2 '),1)
        self.assertIn('QE2_Q2 ',deck);self.assertIn('QF4_Q18 ',deck)
        self.assertEqual(json.dumps(meta['scenario'],sort_keys=True),json.dumps(json.loads(json.dumps(meta['scenario'])),sort_keys=True))

    def test_event_domain_requires_complete_note_window(self):
        base=c.Scenario()
        for kw in ({'trigger_on_s':0},{'trigger_off_s':.04},{'trigger_transition_s':.03},
                   {'contour_supply_v':10},{'controls':replace(base.controls,attack_ohm=0)}):
            with self.assertRaises(ValueError):replace(base,**kw).validate()

    def test_accumulated_charge_uses_entire_nonuniform_history(self):
        s=c.Scenario();t=np.r_[0,np.geomspace(1e-8,.04,10000)]
        raw=np.zeros((len(t),len(s.vectors)+1));raw[:,0]=t
        def put(name,x):raw[:,s.vectors.index(name)+1]=x
        # Independent linear C2 fixture: I=C*dV/dt, both 10 uF capacitors.
        slope=3.;timing=slope*t
        put('v(e2_timing_c2)',timing)
        put('v(e2_attack_panel_in)',timing+10000*10e-6*slope)
        put('v(e2_decay_out)',timing);put('v(e2_follower_base)',timing)
        put('v(f4_q17_collector)',slope*t)
        put('v(f4_main_output)',np.full(len(t),-1000*10e-6*slope))
        put('v(ramp_c1)',-4+4*np.mod(440*t,1))
        m=c.measurement(raw,s)
        self.assertLess(m['timing_balance_max_c'],1e-18)
        self.assertLess(m['output_balance_max_c'],1e-18)
        self.assertAlmostEqual(m['frequency_hz'],440,delta=1e-9)
        # A wrong early history cannot be hidden by a final-cycle observation.
        raw[1:20,s.vectors.index('v(e2_attack_panel_in)')+1]+=100
        self.assertGreater(c.measurement(raw,s)['timing_balance_max_c'],1e-12)


if __name__=='__main__':unittest.main()
