from dataclasses import replace
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import loudness_board4_circuit as c
import loudness_board4_probes as p
import voice_current_tolerance as tol
import voice_jfet_charge_ports as charge
import voice_circuit_reference as voice


class LoudnessBoard4Tests(unittest.TestCase):
    def test_contour_port_is_loaded_without_voltage_boundary(self):
        text,meta=c.netlist(c.Scenario(),c.ROOT/'references-local/contour-test.txt')
        self.assertNotIn('VF4_contour ',text)
        self.assertIn('RF4_R59 F4_LOUDNESS_CONTOUR F4_Q18_BASE 68000',text)
        self.assertIn('QE2_Q2 E2_FOLLOWER_SUPPLY E2_FOLLOWER_MID F4_LOUDNESS_CONTOUR LAB_NPN',text)
        self.assertIn('RE2_R36 E2_TRIGGER_COLLECTOR E2_RESET_DIODE_A 10000',text)
        self.assertIn('QE2_Q18 E2_DECAY_OUT E2_DECAY_SWITCH_BASE E2_SUSTAIN_DRIVER_EMITTER LAB_NPN',text)
        self.assertEqual(sum(l.startswith('Q') for l in text.splitlines()),35)
        self.assertNotIn('.ic ',text);self.assertNotIn('ADSR',text)
        self.assertIn('v(f4_loudness_contour)',c.Scenario().vectors)

    def test_charge_balance_retains_fast_decay_current(self):
        s=replace(c.Scenario(),controls=replace(c.Scenario().controls,final_decay=False))
        t=np.array([0,.1,.2,.35]);raw=np.zeros((4,len(s.vectors)+1));raw[:,0]=t
        col={n:i+1 for i,n in enumerate(s.vectors)}
        raw[:,col['v(e2_timing_c2)']]=t
        raw[:,col['v(e2_attack_panel_in)']]=t+.15
        raw[:,col['v(e2_decay_out)']]=t
        raw[:,col['v(e2_follower_base)']]=t
        raw[:,col['@de2_cr4[id]']]=5e-6
        self.assertLess(c.measure(raw,s)['timing_balance_max_c'],1e-18)
        raw[:,col['@de2_cr4[id]']]=0
        self.assertGreater(c.measure(raw,s)['timing_balance_max_c'],p.GATES['charge_c'])

    def test_voltage_trace_gate_rejects_wrong_control_and_nan(self):
        s=c.Scenario();raw=np.zeros((2,len(s.vectors)+1));raw[:,0]=[0,.35]
        self.assertEqual(max(p.contrast(raw,raw,s,s)['max_trace_difference_v'].values()),0)
        bad=raw.copy();bad[:,s.vectors.index('v(f4_loudness_contour)')+1]=.0051
        with self.assertRaises(ValueError):p.contrast(raw,bad,s,s)
        bad[:]=np.nan
        with self.assertRaises(ValueError):p.contrast(raw,bad,s,s)

    def test_trigger_and_pot_domains_reject_invalid_events(self):
        for s in (replace(c.Scenario(),trigger_on_s=.2),replace(c.Scenario(),trigger_transition_s=0),
                  replace(c.Scenario(),contour_supply_v=float('nan')),
                  replace(c.Scenario(),controls=replace(c.Scenario().controls,external_s_short=True))):
            with self.assertRaises(ValueError):s.validate()
        s=replace(c.Scenario(),controls=replace(c.Scenario().controls,attack_ohm=0))
        text,_=c.netlist(s,c.ROOT/'references-local/contour-test.txt')
        self.assertIn('VE2_PANEL_R13 E2_ATTACK_PANEL_IN E2_TIMING_C2 0',text)

    def test_current_tolerance_does_not_change_physical_branches(self):
        s=voice.Scenario();path=voice.ROOT/'references-local/current-test.txt'
        text,_=voice.netlist(s,path,linear_solver='klu')
        for value in tol.CANDIDATES:
            candidate,_=tol.factory(value)(s,path)
            self.assertEqual(text,candidate.replace(f'abstol={value:.17g}','abstol=1e-13'))
        with self.assertRaises(ValueError):tol.factory(1e-9)

    def test_charge_law_continuity_and_derivative(self):
        for c0 in (3.3e-12,5.4990908339470075e-12):
            self.assertEqual(charge.charge(0,c0),0)
            q0=charge.charge(.5,c0)
            self.assertAlmostEqual(q0,2*c0*(1-np.sqrt(.5)),delta=1e-27)
            for v in (-9,-1,.499,.5,.501,.7):
                h=1e-6;numeric=(charge.charge(v+h,c0)-charge.charge(v-h,c0))/(2*h)
                expected=c0/np.sqrt(1-v) if v<.5 else c0/np.sqrt(.5)+c0/(2*.5**1.5)*(v-.5)
                self.assertAlmostEqual(numeric,expected,delta=1e-19)


if __name__=='__main__':unittest.main()
