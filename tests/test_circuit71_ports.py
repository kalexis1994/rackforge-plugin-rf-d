import json
import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from circuit71_loudness_vectors import evaluator,metrics
from cutoff_j7_vectors import setup
from circuit71_port_vectors import derivatives


class JointPorts(unittest.TestCase):
    def test_fresh_perturbations_of_dc_and_immutable_temporal_sources(self):
        report=json.loads((ROOT/"evidence/circuit71_port_vectors.json").read_text())
        dc=next(c for c in report["cases"] if c["c2_v"]==9.3 and c["reset_base_v"]==0.01)
        temporal=next(c for c in report["cases"] if c["mode"]=="transient" and c["c2_v"]==3.2)
        for case in (dc,temporal):
            old=copy.deepcopy(case["old"])
            admittance,gradient=derivatives(setup(case["r61_ohm"]),case["node_v"],case["c2_v"],
                case["reset_base_v"],old,case["bus_v"],report["fd_delta_v"])
            self.assertEqual(old,case["old"])
            self.assertLess(max(abs(a-b) for ra,rb in zip(admittance,case["admittance_s"]) for a,b in zip(ra,rb)),1e-9)
            self.assertLess(max(abs(a-b) for ra,rb in zip(gradient,case["node_gradient_v_per_v"]) for a,b in zip(ra,rb)),2e-5)

    def test_tight_fd_roots_refinement_and_loaded_reset_branch(self):
        report=json.loads((ROOT/"evidence/circuit71_port_vectors.json").read_text())
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["cases"]),36)
        values={r:setup(r) for r in (200,200000)}
        reset_conducting=[]
        for case in report["cases"]:
            residual=evaluator(values[case["r61_ohm"]],case["c2_v"],case["reset_base_v"],
                               old=case["old"],bus=case["bus_v"])(case["node_v"])
            self.assertLess(max(map(abs,residual)),report["kcl_gate_a"])
            self.assertLess(case["diagnostics"]["correction_v"],report["correction_gate_v"])
            self.assertLess(case["refinement_admittance_s"],report["gates"]["refinement_admittance_s"])
            self.assertLess(case["refinement_node_gradient_v_per_v"],report["gates"]["refinement_node_gradient_v_per_v"])
            m=metrics(case["node_v"],case["c2_v"],case["reset_base_v"])
            self.assertEqual(case["current_a"],[m["timing_current_a"],m["reset_current_a"]])
            if case["c2_v"]==9.3 and case["reset_base_v"]==0.01:
                reset_conducting.append(case)
        self.assertEqual(len(reset_conducting),2)
        for case in reset_conducting:
            self.assertLess(case["current_a"][1],-1e-6)
            self.assertGreater(case["admittance_s"][1][1],1e-6)
            self.assertGreater(abs(case["admittance_s"][0][1]-case["admittance_s"][1][0]),1e-6,
                               "active port must not be forced reciprocal")


if __name__=="__main__":unittest.main()
