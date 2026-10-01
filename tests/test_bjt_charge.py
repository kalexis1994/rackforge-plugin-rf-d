from dataclasses import replace,FrozenInstanceError
import json
import math
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_reference import Parameters,Device,History
from junction_charge_reference import Depletion
from bjt_charge_ngspice_probes import model_parameters,compare


def from_dict(p):
    return Parameters(**dict(p,depletion_be=Depletion(**p["depletion_be"]),depletion_bc=Depletion(**p["depletion_bc"])))


class BipolarCharge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT/"evidence/bjt_charge_ngspice_probes.json").read_text())

    def test_all_independent_simulator_exports_match_regenerated_terminal_law(self):
        self.assertEqual(len(self.report["cases"]),72)
        g = self.report["gates"]
        for row in self.report["cases"]:
            result = Device(from_dict(row["parameters"])).evaluate(row["terminal_v"])
            c = np.asarray(result.capacitance_f)
            comparisons = [compare(result.current_a,row["ngspice_current_a"],g["current_abs_a"],g["current_relative"]),
                compare([result.candidate.be_c,result.candidate.bc_c],row["ngspice_oriented_charge_c"],g["charge_abs_c"],g["charge_relative"]),
                compare([c[2,2],c[1,1]],row["ngspice_junction_cap_f"],g["capacitance_abs_f"],g["capacitance_relative"])]
            for ac in row["ac"]:
                expected = np.asarray(result.jacobian_s)+1j*2*np.pi*ac["frequency_hz"]*c
                independent = np.asarray(ac["ngspice_real_s"])+1j*np.asarray(ac["ngspice_imag_s"])
                comparisons.append(compare(expected,independent,g["admittance_abs_s"],g["admittance_relative"]))
            self.assertTrue(all(c["passed"] for c in comparisons),row["label"])
        self.assertFalse(self.report["physical_charge_identified"])

    def test_every_terminal_column_by_fd_static_charge_and_transient(self):
        for row in self.report["cases"]:
            device = Device(from_dict(row["parameters"]))
            v = np.asarray(row["terminal_v"])
            old = device.evaluate(v+np.array([-.0002,.0001,0])).candidate
            static = device.evaluate(v)
            transient = device.evaluate(v,old,1e-9)
            for col in range(3):
                a,b = v.copy(),v.copy()
                a[col]+=1e-6; b[col]-=1e-6
                plus,minus = device.evaluate(a),device.evaluate(b)
                cg = (np.asarray(plus.terminal_charge_c)-minus.terminal_charge_c)/2e-6
                ig = (np.asarray(plus.current_a)-minus.current_a)/2e-6
                tg = (np.asarray(device.evaluate(a,old,1e-9).current_a)-device.evaluate(b,old,1e-9).current_a)/2e-6
                self.assertTrue(compare(np.asarray(static.capacitance_f)[:,col],cg,1e-19,1e-6)["passed"])
                self.assertTrue(compare(np.asarray(static.jacobian_s)[:,col],ig,1e-12,1e-6)["passed"])
                self.assertTrue(compare(np.asarray(transient.jacobian_s)[:,col],tg,1e-12,1e-6)["passed"])

    def test_gauge_charge_conservation_and_restricted_mass_passivity(self):
        for row in self.report["cases"]:
            device = Device(from_dict(row["parameters"]))
            a = device.evaluate(row["terminal_v"])
            b = device.evaluate(np.asarray(row["terminal_v"])+.1)
            self.assertAlmostEqual(sum(a.terminal_charge_c),0,delta=1e-24)
            self.assertAlmostEqual(sum(a.current_a),0,delta=1e-17)
            self.assertTrue(compare(a.current_a,b.current_a,1e-14,1e-10)["passed"])
            c = np.asarray(a.capacitance_f)
            self.assertLess(max(abs(c.sum(axis=0))),1e-24)
            self.assertLess(max(abs(c.sum(axis=1))),1e-24)
            self.assertLess(max(abs(np.asarray(a.jacobian_s).sum(axis=0))),1e-16)
            self.assertLess(max(abs(np.asarray(a.jacobian_s).sum(axis=1))),1e-16)
            self.assertTrue(np.array_equal(c,c.T))
            self.assertGreaterEqual(min(np.linalg.eigvalsh(c)),-1e-24)

    def test_history_is_bound_to_parameters_and_stays_intact_on_rejection(self):
        p = model_parameters(1,"finite_transit")
        device = Device(p)
        old = device.evaluate((.65,.3,0)).candidate
        copy = (old.be_c,old.bc_c,old.parameters)
        result = device.evaluate((.651,.3,0),old,1e-9)
        self.assertNotEqual(result.candidate.be_c,old.be_c)
        for changed in (replace(p,polarity=-1),replace(p,transit_forward_s=2e-9),replace(p,beta_forward=120)):
            with self.assertRaises(ValueError):
                Device(changed).evaluate((.65,.3,0),old,1e-9)
        for dt in (None,0,-1,math.nan,math.inf):
            with self.assertRaises(ValueError):
                device.evaluate((.65,.3,0),old,dt)
        with self.assertRaises(ValueError):
            device.evaluate((2,.3,0),old,1e-9)
        with self.assertRaises(FrozenInstanceError):
            old.be_c = 0
        self.assertEqual(copy,(old.be_c,old.bc_c,old.parameters))

    def test_invalid_terminal_and_parameter_contracts(self):
        p = model_parameters(1,"finite_transit")
        for values in ((0,0),(0,0,math.nan),(0,0,math.inf)):
            with self.assertRaises(ValueError):
                Device(p).evaluate(values)
        for args in (dict(polarity=True),dict(polarity=0),dict(saturation_a=0),dict(beta_reverse=-1),
                     dict(emission_be_v=0),dict(transit_reverse_s=-1),dict(beta_forward=math.inf)):
            with self.assertRaises(ValueError):
                replace(p,**args)
        with self.assertRaises(TypeError):
            Parameters()
        with self.assertRaises(ValueError):
            History(p,math.nan,0)
        with self.assertRaises(ValueError):
            Device(p).evaluate((.65,.3,0),dt_s=1e-9)


if __name__=="__main__":
    unittest.main()
