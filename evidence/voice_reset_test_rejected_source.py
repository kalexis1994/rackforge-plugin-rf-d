from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_jfet_decomposed as model
import voice_jfet_decomposed_probes as probes
import voice_vco_rshunt as shunt


class ResetScreenTests(unittest.TestCase):
    def test_decomposition_preserves_terminals_and_both_charged_junctions(self):
        s=probes.coupled.Scenario()
        fn,_=model.port_factory(s,'vco',[0,.04],[0,0],False)
        deck,meta=fn(s,model.ROOT/'artifacts/test.txt')
        self.assertNotIn('JQ7_left ',deck);self.assertNotIn('JQ7_right ',deck)
        self.assertEqual(deck.count('Bchannel_'),2);self.assertEqual(deck.count('Djunction_'),4)
        self.assertIn('Djunction_JQ7_left_gs RAMP_C1 FET_COMMON_SOURCE E402_GS',deck)
        self.assertIn('Djunction_JQ7_left_gd RAMP_C1 FET_LEFT_DRAIN E402_GD',deck)
        self.assertIn('TT=0 TNOM=25',deck)
        self.assertIn('CC1 0 RAMP_C1 1e-08',deck)
        self.assertEqual(json.dumps(meta['scenario'],sort_keys=True),json.dumps(json.loads(json.dumps(meta['scenario'])),sort_keys=True))

    def test_unsupported_device_domain_rejects(self):
        original=model.vco.read(model.vco.DEVICES)
        for key,value in (('B',.8),('RD',10),('RS',10),('TNOM',27),('LEVEL',2)):
            card=json.loads(json.dumps(original));card['jfet'][key]=value
            with patch.object(model.vco,'read',return_value=card):
                with self.assertRaises(ValueError):model.decompose('.model LAB_E402 NJF()\nJx d g s LAB_E402\n.options temp=25\n')

    def test_terminal_benchmark_keeps_independent_primitive(self):
        deck,_=probes.benchmark(probes.coupled.Scenario(),model.ROOT/'artifacts/test.txt')
        self.assertIn('Ja d_a g_a s_a REFERENCE',deck)
        self.assertNotIn('Jb d_b g_b s_b LAB_E402',deck)
        self.assertIn('Bchannel_Jb d_b s_b I=',deck)
        self.assertEqual(deck.count('Djunction_Jb'),2)

    def test_historical_generation_preserves_bus_waveform(self):
        path=model.ROOT/'references-local/voice-circuit/port-behavioral01/fixed-contour-control-03-vco.cir'
        if not path.exists():self.skipTest('private frozen reproduction deck unavailable')
        fn,_=probes.historical_factory('fixed-contour-control-03-vco')
        deck,meta=fn(probes.coupled.Scenario(),model.ROOT/'artifacts/test.txt')
        original=path.read_text(encoding='utf-8')
        section=lambda s:s[s.index('Bmixer MIXER_DRIVE'):s.index('Vmixer MIX_BUS_BOARD4_PIN4')]
        self.assertEqual(section(original),section(deck))
        self.assertTrue(meta['diagnostic_only'])

    def test_regularization_changes_only_export_and_declared_option(self):
        path=model.ROOT/'references-local/voice-circuit/port-behavioral01/fixed-contour-control-01-vco.cir'
        if not path.exists():self.skipTest('private frozen reproduction deck unavailable')
        original=path.read_text(encoding='utf-8');s=probes.coupled.Scenario()
        export=model.ROOT/'artifacts/test.txt'
        for r in shunt.CANDIDATES+shunt.REFINED:
            fn,old=shunt.factory('constant',r);deck,meta=fn(s,export)
            restored=deck.replace(f'rshunt={r:.17g} ','').replace(export.as_posix(),path.with_suffix('.txt').as_posix())
            self.assertEqual(restored,original)
            self.assertFalse(meta['exact_original_equations']);self.assertFalse(meta['added_shunts_are_physical_components'])
        with self.assertRaises(ValueError):shunt.factory('constant',1e12)

    def test_wave_and_event_gates_reject_drift_without_alignment(self):
        t=np.linspace(0,.04,80001);wave=np.zeros((len(t),len(probes.p.VCO_VECTORS)+1));wave[:,0]=t
        wave[:,1]=-4+4*np.mod(t*440,1)
        self.assertTrue(probes.contrast(wave,wave)['passed'])
        shifted=wave.copy();shifted[:,1]=-4+4*np.mod((t+20e-9)*440,1)
        self.assertFalse(probes.contrast(shifted,wave)['passed'])
        with self.assertRaises(ValueError):probes.contrast(wave[:100],wave)

    def test_nonfinite_waveform_cannot_pass_control_contrast(self):
        t=np.linspace(0,.04,80001);wave=np.zeros((len(t),len(probes.p.VCO_VECTORS)+1));wave[:,0]=t
        wave[:,1]=-4+4*np.mod(t*440,1)
        invalid=wave.copy();invalid[:,3]=np.nan
        with self.assertRaises(ValueError):probes.contrast(invalid,wave)


if __name__=='__main__':unittest.main()
