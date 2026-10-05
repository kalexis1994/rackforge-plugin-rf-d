import copy
from dataclasses import asdict
from pathlib import Path
import sys
import unittest

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_circuit_reference as voice
import voice_circuit_probes as probes
import validate_voice_circuit_bank as audit
import voice_reset_isolation as isolate
import voice_capacitor_coordinates as coordinates
import voice_capacitor_regularization as regularize
import render_voice_circuit as render


class VoiceBankTests(unittest.TestCase):
    def nominal_fixture(self):
        cases={}
        for label in ('nominal500','nominal250','nominal125','nominal-trap125'):
            windows={n:dict(min=-1,max=1) for n in ('v(mix_bus_board4_pin4)','v(f4_recover_collector)','v(f4_main_output)')}
            cases[label]=dict(measurements=dict(frequency_hz=440,output_ac_rms_v=.1,windows=windows))
        return dict(gates=probes.GATES.copy(),cases=cases,passed=False)

    def test_scoped_acceptance_does_not_accept_incomplete_full_bank(self):
        bank=self.nominal_fixture()
        self.assertEqual(len(audit.nominal_contrasts(bank)),3)
        self.assertFalse(bank['passed'])
        with self.assertRaises(ValueError):probes.validate(bank)

    def test_nominal_limits_cannot_be_bypassed(self):
        for mutate in ('extrema','frequency','rms','error','gate'):
            bank=self.nominal_fixture();m=bank['cases']['nominal250']['measurements']
            if mutate=='extrema':m['windows']['v(f4_main_output)']['max']=1.0051
            elif mutate=='frequency':m['frequency_hz']=441
            elif mutate=='rms':m['output_ac_rms_v']=.12
            elif mutate=='error':bank['cases']['nominal125']['error']='incomplete trajectory'
            else:bank['gates']['extrema_v']=.01
            with self.assertRaises(ValueError):audit.nominal_contrasts(bank)

    def test_backend_change_keeps_electrical_branches_identical(self):
        s=voice.Scenario();path=voice.ROOT/'references-local/voice-test.txt'
        sparse,_=voice.netlist(s,path,linear_solver='sparse')
        klu,meta=voice.netlist(s,path,linear_solver='klu')
        self.assertEqual(sparse.replace('.options sparse ','.options '),klu.replace('.options klu ','.options '))
        self.assertEqual(meta['linear_solver'],'klu')
        self.assertNotIn('REPS_',klu);self.assertNotIn('Ecoord_',klu)
        for ref in ('C9','C24','C15','C4','C27','C10','C2'):
            self.assertIn('CF4_'+ref+' ',klu)
        with self.assertRaises(ValueError):voice.netlist(s,path,linear_solver='invented')

    def test_decoupling_is_an_explicit_intervention(self):
        text,meta=isolate.factory('board-decoupled')(voice.Scenario(),voice.ROOT/'references-local/voice-test.txt')
        self.assertIn('CF4_C27 BOARD4_DIAGNOSTIC_BUS F4_BASE_Q29',text)
        self.assertIn('Vmixer MIX_BUS_BOARD4_PIN4 0 0',text)
        self.assertIn('Vboard_fixture BOARD4_DIAGNOSTIC_BUS 0 0',text)
        self.assertTrue(meta['diagnostic_only'])

    def test_capacitor_coordinate_port_reflects_current_without_esr(self):
        p=coordinates.port('X','A','B',220e-6,1)
        self.assertIn('Ecoord_X COORD_PRE_X 0 A B 1',p)
        self.assertIn('Vcoord_X COORD_PRE_X COORD_X 1',p)
        self.assertIn('Fcoord_X A B Vcoord_X 1',p)
        self.assertFalse(any(l.startswith('R') for l in p))
        with self.assertRaises(ValueError):coordinates.port('X','A','B',0,1)

    def test_zero_approximation_is_original_circuit(self):
        path=voice.ROOT/'references-local/voice-test.txt';s=voice.Scenario()
        original,_=voice.netlist(s,path,linear_solver='klu')
        exact,meta=regularize.netlist(s,path,epsilon_ohm=0)
        self.assertEqual(original,exact)
        self.assertTrue(meta['zero_esr_limit'])
        with self.assertRaises(ValueError):regularize.netlist(s,path,epsilon_ohm=-.001)

    def test_nonstationary_output_is_not_repeated_for_listening(self):
        t=np.linspace(0,.003,3001);raw=np.zeros((len(t),len(voice.VECTORS)+1));raw[:,0]=t
        col=voice.VECTORS.index('v(f4_main_output)')+1
        raw[:,col]=2+np.sin(2*np.pi*1000*t)
        c,f,d=render.output_cycle(raw,[.001,.002,.003])
        self.assertAlmostEqual(f,1000);self.assertLess(d,1e-12)
        self.assertAlmostEqual(c[0].real,2,places=10)
        raw[:,col]+=20*t
        with self.assertRaises(ValueError):render.output_cycle(raw,[.001,.002,.003])


if __name__=='__main__':unittest.main()
