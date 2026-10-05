"""Preserved full bank: strict gates and polarity-correct pulse width."""
import copy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from validate_vco1_circuit_bank import load, audit


class VcoBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=load()

    def test_frozen_bank_passes_corrected_duty_interpretation(self):
        result=audit(self.report)
        self.assertEqual(result["new_solver_runs"],0)
        self.assertFalse(result["original_validator_passed"])
        self.assertEqual(result["original_error"],"pulse selector direction/domain gate failed")
        duty=result["pulse_duties"]
        for pair in duty.values():
            self.assertAlmostEqual(pair["negative"]+pair["high"],1)
        self.assertGreater(duty["10"]["high"],duty["11"]["high"])
        self.assertGreater(duty["11"]["high"],duty["12"]["high"])

    def test_period_charge_and_frequency_gates_cannot_be_bypassed(self):
        for key,value in (("period_spread_relative",1e-4),):
            r=copy.deepcopy(self.report)
            r["cases"]["c4-10-gear125"]["measurements"][key]=value
            with self.assertRaises(ValueError): audit(r)
        r=copy.deepcopy(self.report)
        r["cases"]["c4-10-gear125"]["measurements"]["cycle_charge_check"]["relative_imbalance"]=.003
        with self.assertRaises(ValueError): audit(r)
        r=copy.deepcopy(self.report)
        r["comparisons"]["c4-10-method"]["frequency_error_cents"]=2
        with self.assertRaises(ValueError): audit(r)

    def test_changed_trace_scene_or_invented_comparison_is_rejected(self):
        for mutation in ("incomplete","scene","comparison","source","pulse"):
            r=copy.deepcopy(self.report)
            if mutation=="incomplete": r["cases"]["keyboard-low"]["receipt"]["trajectory_complete"]=False
            if mutation=="scene": r["cases"]["keyboard-low"]["scenario"]["keyboard_v"]=-2
            if mutation=="comparison": r["comparisons"]["c4-10-method"]["phase_aligned_peak_v"]=0
            if mutation=="source": r["source_sha256_after"]={}
            if mutation=="pulse": r["cases"]["pulse-12"]["measurements"]["pulse_negative_duty"]=-.1
            with self.assertRaises(ValueError): audit(r)


if __name__=="__main__": unittest.main()
