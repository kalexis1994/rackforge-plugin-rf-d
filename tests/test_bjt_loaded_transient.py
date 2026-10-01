import json
import copy
import math
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_reference import History
from bjt_loaded_transient_reference import Circuit,State,input_voltage
from bjt_loaded_transient_probes import passes,GATES,run_primary
from bjt_charge_ngspice_probes import model_parameters
from test_bjt_charge import from_dict


class LoadedBipolarTransient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT/"evidence/bjt_loaded_transient_probes.json").read_text())

    def test_independent_refinement_and_native_voltage_gates_are_regenerated(self):
        r = self.report
        self.assertEqual(r["gates"],GATES)
        self.assertEqual(len(r["cases"]),4)
        self.assertTrue(passes(r))
        self.assertEqual(sum(n["steps"] for c in r["cases"] for n in c["native"]),252000)
        for case in r["cases"]:
            self.assertEqual(len(case["native"]),6)
            self.assertEqual(len(case["independent"]),2)
            coarse,fine = [np.asarray(i["observed"]) for i in case["independent"]]
            self.assertEqual(fine.shape,(501,5))
            self.assertLessEqual(np.max(np.abs(coarse[:,:3]-fine[:,:3])),GATES["independent_refinement_error_v"])
            errors = []
            for native in case["native"]:
                own = np.array([o["node_v"] for o in native["observed"]])
                error = np.max(np.abs(own-fine[:,:3]))
                self.assertAlmostEqual(error,native["max_node_error_vs_independent_v"],delta=1e-15)
                self.assertEqual(native["history_reset_count"],0)
                self.assertGreater(native["both_junctions_forward_steps"],0)
                charges = np.array([[o["be_c"],o["bc_c"]] for o in native["observed"]])
                self.assertAlmostEqual(np.max(np.abs(charges[1:]-fine[1:,3:])),native["max_charge_error_vs_independent_c"],delta=1e-25)
                errors.append(error)
            self.assertTrue(all(b<a for a,b in zip(errors,errors[1:])))
            self.assertLessEqual(errors[-1],GATES["native_node_error_v"])
            self.assertLessEqual(errors[-1]/errors[0],GATES["fine_over_coarse_error"])
        self.assertFalse(r["physical_charge_identified"])
        self.assertIsNone(r["selected_latch_branch"])

    def test_saved_one_interval_histories_close_kcl_and_all_terminal_charges(self):
        for case in self.report["cases"]:
            p = from_dict(case["parameters"])
            circuit = Circuit(p)
            native = case["native"][-1]
            for sample in native["observed"][1:]:
                old = sample["previous"]
                state = State(tuple(old["node_v"]),History(p,old["be_c"],old["bc_c"]))
                residual,j,result = circuit.evaluate(sample["node_v"],input_voltage(sample["time_s"],p.polarity),state,native["dt_s"])
                self.assertLess(np.max(np.abs(residual)),GATES["max_kcl_a"])
                self.assertEqual(result.candidate.be_c,sample["be_c"])
                self.assertEqual(result.candidate.bc_c,sample["bc_c"])
                self.assertAlmostEqual(sum(result.current_a),0,delta=1e-16)

    def test_independent_fd_solve_uses_the_same_history_during_switch_and_release(self):
        for case in self.report["cases"]:
            p = from_dict(case["parameters"])
            circuit = Circuit(p)
            native = case["native"][-1]
            for index in (5,80,200,260,400):
                sample = native["observed"][index]
                old = sample["previous"]
                state = State(tuple(old["node_v"]),History(p,old["be_c"],old["bc_c"]))
                snapshot = (state.node_v,state.charge)
                solved,diag = circuit.solve(state.node_v,input_voltage(sample["time_s"],p.polarity),state,native["dt_s"],use_fd=True)
                self.assertLess(np.max(np.abs(np.asarray(solved.node_v)-sample["node_v"])),1e-7)
                self.assertLess(diag["max_kcl_a"],GATES["max_kcl_a"])
                self.assertEqual(snapshot,(state.node_v,state.charge))

    def test_pnp_and_npn_mirror_nodes_while_preserving_oriented_charge(self):
        for profile in ("zero_transit","finite_transit"):
            a = next(c for c in self.report["cases"] if c["profile"]==profile and c["polarity"]==1)
            b = next(c for c in self.report["cases"] if c["profile"]==profile and c["polarity"]==-1)
            for na,nb in zip(a["native"],b["native"]):
                for sa,sb in zip(na["observed"],nb["observed"]):
                    self.assertEqual(tuple(sa["node_v"]),tuple(-v for v in sb["node_v"]))
                    self.assertEqual(sa["be_c"],sb["be_c"])
                    self.assertEqual(sa["bc_c"],sb["bc_c"])

    def test_failed_solve_and_invalid_mesh_leave_accepted_history_intact(self):
        p = model_parameters(1,"finite_transit")
        circuit = Circuit(p)
        state,_ = circuit.initial()
        snapshot = (state.node_v,state.charge)
        with self.assertRaises(ValueError):
            circuit.solve(state.node_v,3,state,.25e-9,iterations=1)
        self.assertEqual(snapshot,(state.node_v,state.charge))
        for time in (-1,math.nan,3e-6):
            with self.assertRaises(ValueError):
                input_voltage(time,1)
        for h in (0,-1,math.nan,5e-9,.3e-9):
            with self.assertRaises(ValueError):
                run_primary(p,h)
        with self.assertRaises(ValueError):
            State(list(state.node_v),state.charge)

    def test_aborted_and_insufficient_accuracy_attempts_are_retained(self):
        r = self.report
        self.assertEqual(r["oracle_rejected_attempts"][0]["returncode"],0)
        self.assertFalse(r["oracle_rejected_attempts"][0]["admitted"])
        self.assertEqual(len(r["rejected_accuracy_surveys"]),2)
        for s in r["rejected_accuracy_surveys"]:
            self.assertFalse(s["admitted"])
        self.assertGreater(r["rejected_accuracy_surveys"][0]["zero_transit"]["node_error_v"],GATES["native_node_error_v"])
        self.assertGreater(r["rejected_accuracy_surveys"][1]["finite_transit_independent_refinement_error_v"],GATES["independent_refinement_error_v"])
        incomplete = copy.deepcopy(r)
        incomplete["cases"] = []
        self.assertFalse(passes(incomplete))
        changed = copy.deepcopy(r)
        changed["gates"]["native_node_error_v"] = 100
        self.assertFalse(passes(changed))
        for case in r["cases"]:
            for independent in case["independent"]:
                self.assertFalse(independent["initial_charge_export_valid"])
                self.assertEqual(independent["observed"][0][3:],[0,0])
            self.assertNotEqual(case["native"][0]["observed"][0]["bc_c"],0)


if __name__=="__main__":
    unittest.main()
