import sys
from pathlib import Path
import unittest
from dataclasses import replace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import filter_vca_circuit_reference as f
import filter_vca_circuit_probes as probes


class FilterVcaCircuitTests(unittest.TestCase):
    def test_input_has_finite_impedance_and_no_oscillator(self):
        text,meta=f.netlist(f.Scenario(),f.ROOT/'references-local/filter-test.txt')
        self.assertIn('Rfixture FIXTURE MIX_BUS_BOARD4_PIN4 1000',text)
        self.assertNotIn('Vmixer',text)
        self.assertNotIn('RAMP_C1',text)
        self.assertNotIn('LM741',text)
        self.assertIn('QF4_Q26 F4_Q26_COLLECTOR F4_CONTROL_BASE F4_CUTOFF_SHARED LAB_PNP',text)
        self.assertIn('RF4_R34 F4_Q16_BASE F4_Q15_BASE 820',text)
        self.assertIn('RF4_R75 F4_C2_RIGHT F4_MAIN_OUTPUT 1000',text)
        self.assertTrue(set(f.VECTORS).issubset(text.split()))
        self.assertFalse(any('741' in p for p in meta['source_sha256']))

    def test_invalid_drive_and_unresolved_frequency_rejected(self):
        for kw in ({'frequency_hz':0},{'amplitude_v':-1},{'source_ohm':0},{'frequency_hz':100000}):
            with self.assertRaises(ValueError):replace(f.Scenario(),**kw).validate()

    def test_reserved_scenarios_separate_from_refinement(self):
        s=probes.scenes()
        self.assertEqual(len(s),18)
        self.assertEqual(s['nominal1'].amplitude_v,s['nominal2'].amplitude_v)
        self.assertEqual(s['nominal1'].board.cutoff_fraction,s['nominal2'].board.cutoff_fraction)
        self.assertEqual(s['r61-alternate'].board.r61_ohm,200000)
        self.assertEqual(s['small-7040'].amplitude_v,.001)
        self.assertEqual(s['contour-mute'].board.first_loudness_v,0)

    def test_missing_scene_and_changed_gate_rejected(self):
        with self.assertRaises(ValueError):probes.validate(dict(cases={},gates=probes.GATES))
        with self.assertRaises(ValueError):probes.validate(dict(cases=dict.fromkeys(probes.scenes()),gates={}))


if __name__=='__main__':unittest.main()
