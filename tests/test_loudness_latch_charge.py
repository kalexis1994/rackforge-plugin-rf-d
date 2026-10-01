import copy
from dataclasses import asdict,replace
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters,compare
from loudness_latch_charge_reference import ChargedNetwork,LatchCharge,History
from loudness_latch_charge_probes import GATES,passes,joint_state,stamp_terminal_matrix
from loudness_descriptor_stability import joint_static,reduced_modes,pole_matching_error


class NonlinearLatchCharge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/"evidence/loudness_latch_charge_probes.json").read_text())
        cls.ng=json.loads((ROOT/"evidence/bjt_charge_ngspice_probes.json").read_text())

    def setup_case(self,case):
        network=ChargedNetwork(case["r61_ohm"],model_parameters(1,case["profile"]))
        previous=network.prepare(joint_state(case["replay"]["previous"]["joint"]))
        self.assertEqual(json.loads(json.dumps(asdict(previous))),case["replay"]["previous"])
        return network,previous

    def test_rebuild_independent_ac_mass_and_descriptor_at_all_twelve_biases(self):
        self.assertTrue(passes(self.report))
        empty=copy.deepcopy(self.report);empty["cases"]=[];self.assertFalse(passes(empty))
        changed=copy.deepcopy(self.report);changed["gates"]["replay_kcl_a"]*=10;self.assertFalse(passes(changed))
        for case in self.report["cases"]:
            network,_=self.setup_case(case)
            x=case["frozen_node_v"]
            g,caps=joint_static(network.joint,x,10.0)
            gf,_=joint_static(network.joint,x,10.0,use_fd=True)
            extended=np.array(x+[x[7]])
            latch=LatchCharge(network.joint.contour,66,95,model_parameters(1,case["profile"]))
            evaluated=latch.evaluate(extended)
            matched=[next(c for c in self.ng["cases"] if c["label"]==f"latch-{case['r61_ohm']}-{case['root']}-{ref}"
                          and c["profile"]==case["profile"] and c["parameters"]["polarity"]==1) for ref in ("Q25","Q15")]
            for saved in case["independent_ac_checks"]:
                frequency=saved["frequency_hz"]
                independent=stamp_terminal_matrix(latch,[np.array(next(a for a in c["ac"] if a["frequency_hz"]==frequency)["ngspice_imag_s"])/(2*np.pi*frequency) for c in matched])
                check=compare(evaluated["capacitance_f"],independent,GATES["capacitance_abs_f"],GATES["capacitance_relative"])
                self.assertEqual(check,saved["check"])
                self.assertTrue(check["passed"])
            ng_caps=[]
            for terminals,c in zip(latch.terminals,matched):
                b,co,e=[i for i,_ in terminals];be,bc=c["ngspice_junction_cap_f"]
                ng_caps.extend(((b,e,be),(co,b,bc)))
            a=reduced_modes(g,caps+latch.capacitors(extended),.001)
            b=reduced_modes(gf,caps+ng_caps,.001)
            self.assertEqual(a["dynamic_rank"],25)
            self.assertEqual(a["algebraic_unknowns"],70)
            self.assertLess(pole_matching_error(a["poles"],b["poles"]),GATES["pole_matching_relative"])
            self.assertEqual(a["growing_modes"],int(case["root"]=="middle"))
            self.assertEqual(case["growing_modes_damped_by_1ms_backward_euler"],int(case["root"]=="middle"))

    def test_full_charge_derivative_and_temporal_increment_use_fixed_history(self):
        for case in self.report["cases"]:
            network,previous=self.setup_case(case)
            snapshot=copy.deepcopy(previous)
            x=np.array(case["frozen_node_v"])
            evaluated=network.latch.evaluate(x,previous.latch,.001)
            fd=np.zeros((94,94))
            for col in range(94):
                a=x.copy();b=x.copy();a[col]+=1e-6;b[col]-=1e-6
                plus=network.latch.evaluate(a,previous.latch,.001)
                minus=network.latch.evaluate(b,previous.latch,.001)
                fd[:,col]=(plus["increment_a"]-minus["increment_a"])*.001/2e-6
            self.assertTrue(compare(evaluated["capacitance_f"],fd,GATES["fd_capacitance_abs_f"],GATES["fd_capacitance_relative"])["passed"])
            q=network.latch.evaluate(x)["charge_c"]
            old_q=network.latch.evaluate(previous.joint.node_v)["charge_c"]
            np.testing.assert_allclose(evaluated["increment_a"],(q-old_q)/.001,rtol=1e-15,atol=1e-24)
            self.assertEqual(previous,snapshot)

    def test_all_replayed_roots_close_joint_kcl_and_publish_all_histories_together(self):
        for case in self.report["cases"]:
            network,previous=self.setup_case(case)
            x=np.array(case["replay"]["state"]["joint"]["node_v"])
            r,j=network.evaluator(10.0,previous,.001)(x)
            rf,jf=network.evaluator(10.0,previous,.001)(x,use_fd=True)
            self.assertLess(np.max(np.abs(r)),GATES["replay_kcl_a"])
            np.testing.assert_allclose(r,rf,rtol=0,atol=0)
            self.assertTrue(np.all(np.abs(j-jf)<1e-8+2e-5*np.abs(jf)))
            joint=network.joint.state(x,10.0,previous.joint,.001)
            self.assertEqual(json.loads(json.dumps(asdict(joint))),case["replay"]["state"]["joint"])
            latch=network.latch.evaluate(x,previous.latch,.001)["candidate"]
            self.assertEqual(json.loads(json.dumps(asdict(latch))),case["replay"]["state"]["latch"])
            self.assertEqual(len(joint.audio_capacitor_v)+len(joint.contour.capacitor_v)+1,21)
            self.assertEqual(len(latch.devices),2)
            self.assertIsNone(case["replay"]["selected"])
            self.assertLess(case["replay"]["full_fd_error_v"],1e-6)

    def test_perturbed_fd_solve_reproduces_a_root_without_selecting_it(self):
        for case in self.report["cases"]:
            network,previous=self.setup_case(case)
            snapshot=copy.deepcopy(previous)
            target=np.array(case["replay"]["state"]["joint"]["node_v"])
            result,diag=network.solve(target+1e-4,10.0,previous,.001,use_fd=True)
            self.assertLess(np.max(np.abs(np.array(result.joint.node_v)-target)),1e-6)
            self.assertGreater(diag["iterations"],0)
            self.assertEqual(previous,snapshot)

    def test_failure_layout_and_reparameterization_preserve_original_history(self):
        case=self.report["cases"][0]
        network,previous=self.setup_case(case)
        snapshot=copy.deepcopy(previous)
        x=np.array(case["replay"]["state"]["joint"]["node_v"])
        with self.assertRaises(ValueError):network.solve(x+1e-3,10.0,previous,.001,iterations=1)
        for dt in (None,0,-1,float("nan"),float("inf")):
            with self.assertRaises(ValueError):network.evaluator(10.0,previous,dt)
        with self.assertRaises(ValueError):network.latch.evaluate(x,replace(previous.latch,layout=(95,previous.latch.layout[1])),.001)
        changed=ChargedNetwork(case["r61_ohm"],model_parameters(1,"finite_transit"))
        with self.assertRaises(ValueError):changed.evaluator(10.0,previous,.001)
        with self.assertRaises(ValueError):History(previous.latch.layout,list(previous.latch.devices))
        with self.assertRaises(ValueError):network.latch.evaluate(x,None,.001)
        with self.assertRaises(ValueError):network.latch.evaluate(x[:-1])
        self.assertEqual(previous,snapshot)

    def test_existing_static_hypothesis_and_unadmitted_scope_are_explicit(self):
        network,_=self.setup_case(self.report["cases"][0])
        with self.assertRaises(ValueError):LatchCharge(network.joint.contour,66,94,model_parameters(-1,"zero_transit"))
        with self.assertRaises(ValueError):LatchCharge(network.joint.contour,66,93,model_parameters(1,"zero_transit"))
        for flag in ("physical_charge_identified","physical_switching_admitted","audio_admitted","trajectory_refinement_admitted","enumeration_exhaustive"):
            self.assertFalse(self.report[flag])
        self.assertIsNone(self.report["selected"])
        self.assertEqual(len(self.report["omitted_contour_dynamic_bjts"]),8)


if __name__=="__main__":unittest.main()
