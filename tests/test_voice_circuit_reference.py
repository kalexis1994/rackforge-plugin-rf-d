import sys
from pathlib import Path
import unittest
from dataclasses import replace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_circuit_reference as voice
import vco1_circuit_reference as vco


class VoiceCircuitTests(unittest.TestCase):
    def test_primary_ladder_terminals_and_polarities(self):
        g=vco.read(voice.GRAPH)
        q={p['ref']:p for p in g['transistors']}
        # Independent SVC-9 Fig 9-11 constraints, not another generated netlist.
        self.assertEqual((q['Q2']['collector'],q['Q3']['collector']),('POS10_V','POS10_V'))
        self.assertEqual(q['Q29']['emitter'],q['Q30']['emitter'])
        self.assertEqual(q['Q28']['collector'],'Q28_COLLECTOR')
        self.assertEqual(q['Q26']['polarity'],'PNP')
        self.assertEqual(q['Q28']['polarity'],'NPN')
        self.assertEqual(q['Q14']['base'],q['Q16']['collector'])
        self.assertEqual(q['Q13']['base'],q['Q15']['collector'])
        self.assertEqual(q['Q12']['base'],q['Q14']['collector'])
        self.assertEqual(q['Q17']['base'],q['Q13']['collector'])
        self.assertEqual(len(q),25)

    def test_documented_audio_capacitors(self):
        p={p['ref']:p for p in vco.read(voice.GRAPH)['capacitors']}
        for ref in ('C3','C7','C11','C16'):
            self.assertEqual(p[ref]['farad'],68e-9)
        self.assertEqual((p['C27']['a'],p['C27']['b']),('MIX_BUS_BOARD4_PIN4','BASE_Q29'))
        self.assertEqual((p['C6']['a'],p['C6']['b']),('C6_LEFT','Q16_BASE'))
        self.assertEqual((p['C2']['a'],p['C2']['b']),('Q17_COLLECTOR','C2_RIGHT'))
        self.assertEqual(p['C9']['farad'],100e-6)

    def test_coupling_has_no_mixer_source_or_buffer(self):
        text,meta=voice.netlist(voice.Scenario(),voice.ROOT/'references-local/voice-test.txt')
        self.assertNotIn('Vmixer ',text)
        self.assertIn('CRF',text.replace('CF4_C27','CRF'))
        self.assertIn('CF4_C27 MIX_BUS_BOARD4_PIN4 F4_BASE_Q29',text)
        self.assertIn('RF4_R60 F4_TAIL F4_Q28_COLLECTOR',text)
        self.assertNotIn('Itail',text)
        self.assertIn('QF4_Q28 F4_Q28_COLLECTOR F4_CUTOFF_SHARED 0 LAB_NPN',text)
        self.assertTrue(set(voice.EXTRA).issubset(text.split()))
        self.assertEqual(len(meta['board4_branches']),104)

    def test_zero_ohm_trim_contacts_are_exact(self):
        text,_=voice.netlist(replace(voice.Scenario(),scale_ohm=0,regen_bottom_ohm=0,
                                   emphasis_ohm=0,cutoff_fraction=0,range_fraction=1),
                             voice.ROOT/'references-local/voice-test.txt')
        self.assertIn('VF4_R49 F4_CONTROL_BASE F4_SCALE_LOW 0',text)
        self.assertIn('VF4_R14_PANEL F4_EMPHASIS_PIN7 F4_EMPHASIS_PIN6 0',text)
        self.assertIn('VF4_R11_PANEL_low NEG10_V F4_CUTOFF_WIPER 0',text)

    def test_invalid_boundaries_and_profiles_rejected(self):
        for kw in ({'r61_ohm':2000},{'cutoff_fraction':1.1},{'main_load_ohm':0},
                   {'first_balance_ohm':26},{'scale_ohm':float('nan')},
                   {'oscillator':replace(vco.Scenario(),imposed_mixer_v=1)}):
            with self.assertRaises(ValueError): replace(voice.Scenario(),**kw).validate()


if __name__=='__main__': unittest.main()
