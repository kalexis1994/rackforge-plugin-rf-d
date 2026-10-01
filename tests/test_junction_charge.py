from dataclasses import FrozenInstanceError
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from junction_charge_reference import Depletion,LowInjectionDiffusion,Junction,ChargeHistory,companion
from junction_charge_probes import integral_capacitance
from loudness_junction_domain_audit import generate as domain_audit


class JunctionCharge(unittest.TestCase):
    def setUp(self):
        self.model = Junction(Depletion(7e-12,.75,.5,.4),LowInjectionDiffusion(3e-9,1e-14,.026))

    def test_quadrature_and_derivatives_across_synthetic_domains(self):
        report = json.loads((ROOT/"evidence/junction_charge_probes.json").read_text())
        self.assertEqual(len(report["cases"]),300)
        for row in report["cases"]:
            p = row["synthetic_model"]
            model = Junction(Depletion(**p["depletion"]),LowInjectionDiffusion(**p["diffusion"]))
            v = row["voltage_v"]
            q,c = model.evaluate(v)
            self.assertAlmostEqual(q,row["charge_c"],delta=1e-22+abs(q)*1e-12)
            qi = integral_capacitance(model,0,v)
            g = report["gates"]
            self.assertLessEqual(abs(q-qi),g["charge_abs_c"]+g["charge_relative"]*abs(q))
            derivative = (model.evaluate(v+1e-6)[0]-model.evaluate(v-1e-6)[0])/(2e-6)
            self.assertLessEqual(abs(c-derivative),g["derivative_abs_f"]+g["derivative_relative"]*abs(c))
        self.assertTrue(report["synthetic_parameters_only"])
        self.assertFalse(report["physical_charge_identified"])

    def test_knee_charge_capacitance_and_slope_are_continuous(self):
        for m in (0,.33,.5,1):
            for fc in (0,.4,.8):
                d = Depletion(7e-12,.75,m,fc)
                k,h = fc*.75,1e-7
                qm,cm = d.evaluate(k-h)
                q,c = d.evaluate(k)
                qp,cp = d.evaluate(k+h)
                self.assertAlmostEqual((qp-q)/h,c,delta=c*2e-6)
                self.assertAlmostEqual((q-qm)/h,c,delta=c*2e-6)
                # One-sided slopes have O(h) truncation; extrapolate before
                # comparing continuity instead of treating that error as a jump.
                cmh = d.evaluate(k-h/2)[1]
                cph = d.evaluate(k+h/2)[1]
                left = 2*(c-cmh)/(h/2)-(c-cm)/h
                right = 2*(cph-c)/(h/2)-(cp-c)/h
                self.assertAlmostEqual(left,right,delta=1e-19+abs(right)*1e-7)

    def test_log_limit_zero_reference_and_tiny_signal(self):
        for m in (0,.5,.999999999,1):
            d = Depletion(7e-12,.75,m,.4)
            self.assertEqual(d.evaluate(0),(0,7e-12))
            for v in (-1e-12,1e-12):
                self.assertAlmostEqual(d.evaluate(v)[0]/v,7e-12,delta=1e-23)
        log_model = Depletion(7e-12,.75,1,.4)
        for v in (-10,-1,.2,.29):
            nearby = Depletion(7e-12,.75,.999999999,.4)
            self.assertAlmostEqual(nearby.evaluate(v)[0],log_model.evaluate(v)[0],delta=1e-19)

    def test_terminal_conservation_jacobian_and_unpublished_history(self):
        old = ChargeHistory(self.model.evaluate(.2)[0])
        snapshot = old.charge_c
        step = companion(self.model,.73,.05,old,1e-6)
        self.assertEqual(sum(step.current_a),0)
        self.assertEqual(old.charge_c,snapshot)
        for col in range(2):
            a,b = [.73,.05],[.73,.05]
            h = 1e-6
            a[col] += h
            b[col] -= h
            ia = companion(self.model,*a,old,1e-6).current_a
            ib = companion(self.model,*b,old,1e-6).current_a
            for row in range(2):
                self.assertAlmostEqual((ia[row]-ib[row])/(2*h),step.jacobian_s[row][col],
                    delta=abs(step.jacobian_s[row][col])*1e-6)
        with self.assertRaises(FrozenInstanceError):
            old.charge_c = 0
        with self.assertRaises(ValueError):
            companion(self.model,2,0,old,1e-6)
        self.assertEqual(old.charge_c,snapshot)

    def test_charge_increment_integrates_and_differs_from_endpoint_c_delta_v(self):
        values = (-1,.1,.31,.4,.6,.68,.2,-1)
        history = ChargeHistory(self.model.evaluate(values[0])[0])
        initial = history.charge_c
        total = 0
        for v in values[1:]:
            step = companion(self.model,v,0,history,1e-6)
            total += step.current_a[0]*1e-6
            history = step.candidate
        self.assertAlmostEqual(total,history.charge_c-initial,delta=1e-24)
        report = json.loads((ROOT/"evidence/junction_charge_probes.json").read_text())
        self.assertGreater(report["nonlinear_increment"]["relative_difference"],1)

    def test_invalid_parameters_and_nonfinite_history_fail_explicitly(self):
        for args in ((-1,.75,.5,.4),(1,0,.5,.4),(1,.75,-1,.4),(1,.75,2,.4),
                     (1,.75,.5,1),(1,.75,.5,-1),(math.nan,.75,.5,.4)):
            with self.assertRaises(ValueError):
                Depletion(*args)
        for args in ((-1,1,.026),(1,0,.026),(1,1,0),(1,1,math.inf)):
            with self.assertRaises(ValueError):
                LowInjectionDiffusion(*args)
        with self.assertRaises(TypeError):
            Depletion()
        with self.assertRaises(ValueError):
            ChargeHistory(math.nan)
        for dt in (0,-1,math.inf,math.nan):
            with self.assertRaises(ValueError):
                companion(self.model,0,0,ChargeHistory(0),dt)
        for v in (math.inf,math.nan,2):
            with self.assertRaises(ValueError):
                self.model.evaluate(v)

    def test_bias_domain_is_recorded_without_transit_fit(self):
        report = domain_audit()
        self.assertEqual(len(report["cases"]),12)
        self.assertFalse(report["normalization_is_transit_fit"])
        self.assertIsNone(report["selected"])
        for row in report["cases"]:
            self.assertFalse(row["cob_test"]["bias_matches"])
            self.assertFalse(row["transit_time_assigned"])
            self.assertAlmostEqual(sum(row["outgoing_current_a"].values()),0,delta=1e-18)
            for key in ("forward","reverse"):
                self.assertEqual(row["diffusion_f_per_1ns_unit"][key],row["derivative_s"][key]*1e-9)
        for ref,count in (("Q25",2),("Q15",4)):
            self.assertEqual(sum(r["both_junctions_forward"] for r in report["cases"] if r["ref"]==ref),count)


if __name__ == "__main__":
    unittest.main()
