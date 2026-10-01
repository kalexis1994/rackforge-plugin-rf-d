import copy
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_chain94_reference import JointNetwork,State
from loudness_contour_reference import State as ContourState
from circuit66_vca_release_probes import transient_evaluator
from loudness_descriptor_stability import reduced_modes,joint_static,diagnostic_latch_caps,pole_matching_error

def state_from_dict(x):
    return State(tuple(x["node_v"]),tuple(x["audio_capacitor_v"]),x["c10_v"],ContourState(**x["contour"]))

class LoadedContour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fold=json.loads((ROOT/"evidence/loudness_chain94_fold.json").read_text())

    def test_both_roots_and_every_history_close_the_same_loaded_step(self):
        for case in self.fold["cases"]:
            network=JointNetwork(case["r61_ohm"])
            old=state_from_dict(case["prefix"][-1]["state"])
            snapshot=copy.deepcopy(old)
            self.assertIsNone(case["analytic"]["selected"])
            self.assertIsNone(case["full_fd"]["selected"])
            self.assertEqual(case["root_count"],2)
            self.assertLess(case["max_root_reproduction_error_v"],1e-6)
            for root in case["analytic"]["roots"]:
                state=state_from_dict(root["state"])
                r,j=network.evaluator(10.0,old,.001)(np.array(state.node_v))
                self.assertLess(max(map(abs,r)),1e-11)
                rf,jf=network.evaluator(10.0,old,.001)(np.array(state.node_v),use_fd=True)
                self.assertTrue(np.all(np.abs(j-jf)<1e-8+2e-5*np.abs(jf)))
                self.assertLess(max(map(abs,rf-r)),1e-15)
                actual=network.state(np.array(state.node_v),10.0,old,.001)
                self.assertEqual(actual.audio_capacitor_v,state.audio_capacitor_v)
                self.assertEqual(actual.c10_v,state.c10_v)
                self.assertEqual(actual.contour.capacitor_v,state.contour.capacitor_v)
                self.assertEqual(j[32,network.out],-1/68000)
                self.assertEqual(j[network.out,32],-1/68000)
            with self.assertRaises(ValueError):network.step(old,10.0,.001,iterations=1)
            self.assertEqual(old,snapshot)
            for dt in (None,0,float("nan"),float("inf")):
                with self.assertRaises(ValueError):network.evaluator(10.0,old,dt)
            invalid=State(old.node_v,old.audio_capacitor_v[:-1],old.c10_v,old.contour)
            with self.assertRaises(ValueError):network.evaluator(10.0,invalid,.001)
            invalid=State(old.node_v,old.audio_capacitor_v,float("nan"),old.contour)
            with self.assertRaises(ValueError):network.evaluator(10.0,invalid,.001)
            separation=max(abs(a-b) for a,b in zip(case["analytic"]["roots"][0]["state"]["node_v"],case["analytic"]["roots"][1]["state"]["node_v"]))
            self.assertGreater(separation,1.0)

    def test_dc_and_prefix_reproduction_with_a_new_seed(self):
        case=self.fold["cases"][0]
        network=JointNetwork()
        reference=state_from_dict(case["prefix"][0]["state"])
        state,diag=network.solve([v+.001 for v in reference.node_v],0.0,use_fd=True)
        self.assertLess(max(abs(a-b) for a,b in zip(state.node_v,reference.node_v)),1e-6)
        for row in case["prefix"][1:]:
            state,diag=network.step(state,row["keyboard_v"],.001)
            self.assertLess(max(abs(a-b) for a,b in zip(state.node_v,row["state"]["node_v"])),1e-6)
            self.assertLess(diag["correction_v"],1e-8)

    def test_descriptor_preserves_series_capacitor_and_growing_modes(self):
        # A series capacitor's pole is -1/((Ra+Rs)*C), not -1/(Ra*C).
        ra,rs,c=1000.0,25000.0,10e-6
        g=np.array([[1/ra,0.0],[0.0,1/rs]])
        result=reduced_modes(g,[(0,1,c)],.001)
        self.assertAlmostEqual(result["poles"][0]["real_per_s"],-1/((ra+rs)*c),places=12)
        # Backward Euler can damp an actually growing continuous mode when
        # its step crosses 2/lambda. That must never become a stability claim.
        result=reduced_modes(np.array([[-.001]]),[(0,None,1e-6)],.01)
        self.assertEqual(result["growing_modes"],1)
        self.assertAlmostEqual(result["max_real_per_s"],1000.0)
        self.assertLess(result["max_implicit_euler_amplification"],1.0)
        for path in ("loudness_descriptor_stability.json","loudness_fast_charge_audit.json"):
            report=json.loads((ROOT/"evidence"/path).read_text())
            self.assertIsNone(report["selected"])
            self.assertFalse(report["physical_switching_admitted"])
            for case in report["cases"]:
                self.assertLess(case["max_relative_pole_matching_error"],report["gates"]["pole_matching_relative"])
                for mode in ("analytic","independent_fd"):
                    self.assertLess(case[mode]["coordinate_error"],report["gates"]["coordinate_error"])
                    self.assertLess(case[mode]["max_eigen_residual"],report["gates"]["eigen_residual"])
                    expected=int(path=="loudness_fast_charge_audit.json" and .1<case["q25_collector_v"]<2)
                    self.assertEqual(case[mode]["growing_modes"],expected)

    def test_third_root_seed_coverage_and_missing_fast_instability_remain_visible(self):
        report=json.loads((ROOT/"evidence/loudness_chain94_root_survey.json").read_text())
        for case in report["cases"]:
            self.assertIsNone(case["selected"])
            self.assertFalse(case["enumeration_exhaustive"])
            self.assertEqual(len(case["trials"]),51)
            self.assertEqual(len(case["roots"]),3)
            for root in case["roots"]:
                self.assertLess(root["full_fd_error_v"],1e-6)
                self.assertLess(root["full_fd_diagnostics"]["correction_v"],1e-8)
            middle=next(r for r in case["roots"] if .1<r["state"]["contour"]["node_v"]["RESET_COLLECTOR"]<2)
            self.assertEqual(middle["slow_modes"]["growing_modes"],0)
            self.assertEqual(middle["diagnostic_fast_modes"]["growing_modes"],1)
            growing=[p for p in middle["diagnostic_fast_modes"]["poles"] if p["real_per_s"]>0]
            self.assertLess(growing[0]["implicit_euler_amplification_abs"],1)
        a=[dict(real_per_s=x,imag_per_s=0) for x in (1,1,2)]
        b=[dict(real_per_s=x,imag_per_s=0) for x in (1,2,2)]
        self.assertGreater(pole_matching_error(a,b),0)

    def test_refined_primary_path_stops_without_erasing_capacitors(self):
        report=json.loads((ROOT/"evidence/loudness_chain94_time_survey.json").read_text())
        self.assertEqual(len(report["cases"]),8)
        self.assertTrue(report["numerical_quality_passed"])
        self.assertEqual(sum(c["accepted_steps"] for c in report["cases"]),370)
        for case in report["cases"]:
            self.assertIsNotNone(case["primary_rejection"])
            self.assertIsNone(case["selected_alternative"])
            last=case["samples"][-1]
            self.assertEqual(last["time_s"],case["accepted_steps"]*case["dt_s"])
            self.assertEqual(tuple(last["audio_capacitor_v"]),tuple(case["final_state"]["audio_capacitor_v"]))
            self.assertEqual(last["contour_capacitor_v"],case["final_state"]["contour"]["capacitor_v"])

    def test_mass_rank_and_c10_resistor_are_explicit(self):
        network=JointNetwork()
        x=self.fold["cases"][0]["analytic"]["roots"][0]["state"]["node_v"]
        g,caps=joint_static(network,x,10.0)
        self.assertEqual(len(g),95)
        self.assertEqual(len(caps),21)
        self.assertEqual(caps[17],(22,94,10e-6))
        self.assertEqual(g[94,7],-1/25500)
        result=reduced_modes(g,caps,.001)
        self.assertEqual(result["dynamic_rank"],21)
        extra=diagnostic_latch_caps(network.contour,66,10e-12,5e-12)
        self.assertEqual(reduced_modes(g,caps+extra,.001)["dynamic_rank"],25)

if __name__=="__main__":unittest.main()
