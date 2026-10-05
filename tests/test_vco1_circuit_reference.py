"""Independent terminal, device-domain and observation checks for VCO1."""
from dataclasses import replace
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from vco1_circuit_reference import Scenario, DEVICES, netlist, crossings, measure


class VcoCircuitTests(unittest.TestCase):
    def manifest(self, scene=Scenario()):
        deck, meta = netlist(scene, ROOT/"references-local/vco1-circuit/test-export.txt")
        return deck, {b["ref"]:b for b in meta["branches"]}

    def test_primary_schematic_return_rails_are_separate(self):
        deck, parts = self.manifest()
        # These terminals were visually checked on two original schematic scans,
        # not inferred from the implementation's waveform.
        self.assertEqual(parts["Q2"]["terminals"], ["Q2_COLLECTOR", "SCHMITT_DRIVE", "Q2_EMITTER"])
        self.assertEqual(parts["Q12"]["terminals"], ["Q12_COLLECTOR", "Q12_BASE", "NEG10_V"])
        for ref, node in (("R14","Q2_COLLECTOR"),("R29","Q2_EMITTER"),
                          ("R23","TRI_OUTPUT_21B"),("R44","Q11_BASE"),("R35","Q12_BASE")):
            self.assertEqual(set(parts[ref]["terminals"]), {node,"NEG10_V"})
        self.assertEqual(set(parts["R34"]["terminals"]), {"SCHMITT_DRIVE","SAW_OUTPUT_9B"})
        self.assertEqual(set(parts["R33"]["terminals"]), {"GND","SAW_OUTPUT_9B"})

    def test_converter_rc_reset_and_waveforms_are_all_present(self):
        deck, parts = self.manifest()
        for name in ("IC2.Qa","IC2.Qb","IC2.Qc","IC1","IC3","Q7_left","Q7_right",
                     "Q1","Q2","Q3","Q4","Q5","Q6","Q8","Q9","Q10","Q11","Q12",
                     "C1","C2","C3","C4","C14","R42","R78_dc","R78_series","R78_cap",
                     "R30_PANEL","R31_PANEL","R45_PANEL"):
            self.assertIn(name, parts)
        self.assertEqual(parts["IC2.Qa"]["terminals"][0], "RAMP_C1")
        self.assertEqual(parts["Q10"]["terminals"], ["RAMP_C1","Q10_BASE","GND"])
        self.assertEqual(parts["R78_series"]["value"], 220)
        self.assertEqual(parts["R78_cap"]["value"], 1e-8)
        self.assertIn("XIC1 IC1_PLUS IC1_SUM 0 NEG10_V IC1_OUT LM741", deck)
        self.assertIn("XIC3 QB_COLLECTOR NEG4_REF POS10_V NEG10_V IC3_OUT LM741", deck)
        self.assertNotIn("PULSE(", deck.upper())
        self.assertNotIn("SIN(", deck.upper())
        self.assertEqual(deck.count(".ic "), 1)

    def test_e402_hypothesis_agrees_with_declared_datasheet_test_point(self):
        p = json.loads(DEVICES.read_text(encoding="utf-8"))["jfet"]
        current = p["BETA"]*p["VTO"]**2*(1+20*p["LAMBDA"])
        gm = 2*p["BETA"]*(-p["VTO"])*(1+20*p["LAMBDA"])
        crss = p["CGD"]/math.sqrt(1+20/p["PB"])
        self.assertAlmostEqual(current, .002, places=14)
        self.assertAlmostEqual(gm, .0016, places=14)
        self.assertAlmostEqual(crss/1e-12, 1.2, places=12)
        self.assertAlmostEqual((crss+p["CGS"])/1e-12, 4.5, places=12)
        self.assertTrue(.0005 <= current <= .005)
        self.assertTrue(-4.5 <= p["VTO"] <= -1)

    def test_contacts_use_exact_constraints_and_keep_open_width_open(self):
        for fraction in (0, 1):
            deck, parts = self.manifest(replace(Scenario(), r8_fraction=fraction, level_fraction=fraction, r11_active_ohm=0))
            self.assertIn("VR11_active IC1_SUM R37_TOP 0", deck)
            self.assertEqual(parts["R8_low" if fraction==0 else "R8_high"]["kind"], "contact")
            self.assertEqual(parts["R6_panel_low" if fraction==0 else "R6_panel_high"]["kind"], "contact")
        for contact in (8,9):
            _, parts = self.manifest(replace(Scenario(),lower_contact=contact))
            self.assertNotIn("SW6_width", parts)
        _, a = self.manifest()
        _, b = self.manifest(replace(Scenario(),c4_f=100e-12))
        self.assertEqual(a["C4"]["value"], 10e-12)
        self.assertEqual(b["C4"]["value"], 100e-12)

    def test_invalid_scenarios_fail_before_solver(self):
        for key, value in (("keyboard_v",math.nan),("duration_s",0),("max_step_s",-1),
                           ("r8_fraction",1.1),("level_fraction",-.1),("r11_active_ohm",1001),
                           ("c4_f",50e-12),("method","unknown"),("lower_contact",13)):
            with self.assertRaises(ValueError):
                replace(Scenario(),**{key:value}).validate()

    def test_crossings_interpolate_on_nonuniform_grid(self):
        t=np.array([0.,.1,.4,.5,.9])
        v=np.array([-3.,-1.,-3.,-1.,-3.])
        np.testing.assert_allclose(crossings(t,v,-2,True), [.05,.45],rtol=0,atol=1e-15)
        np.testing.assert_allclose(crossings(t,v,-2,False), [.25,.7],rtol=0,atol=1e-15)
        with self.assertRaises(ValueError):
            measure(np.column_stack([t,np.zeros((len(t),16))]),settle_s=0)


if __name__ == "__main__":
    unittest.main()
