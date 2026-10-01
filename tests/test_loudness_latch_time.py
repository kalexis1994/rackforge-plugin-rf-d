import copy
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_charge_reference import ChargedNetwork
from loudness_latch_time_reference import trial,frozen_rate,voltages,charges,scaled_error
from loudness_latch_time_probes import POLICIES,quality,pack,unpack,state_hash,trace


class AdaptiveChargedLatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/"evidence/loudness_latch_time_probes.json").read_text())

    def test_dc_initialization_matches_static_circuit_and_all_charge_histories(self):
        for case in self.report["cases"]:
            network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
            state=unpack(network,case["initial"],0.0)
            r,_=network.joint.evaluator(0.0)(np.array(state.joint.node_v),jacobian=False)
            self.assertLess(np.max(np.abs(r)),1e-11)
            self.assertEqual(network.latch.prepare(state.joint.node_v),state.latch)
            self.assertEqual(len(state.joint.audio_capacitor_v)+len(state.joint.contour.capacitor_v)+1,21)
            self.assertEqual(pack(state)["oriented_charge_c"],case["initial"]["oriented_charge_c"])

    def test_every_published_half_interval_closes_same_history_kcl_and_charge(self):
        for case in self.report["cases"]:
            network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
            old=unpack(network,case["initial"],0.0)
            end=0.0
            for row in case["accepted"]:
                self.assertEqual(row["start_s"],end)
                dt=row["dt_s"]/2
                for name in ("half","fine"):
                    state=unpack(network,row[name],10.0)
                    r,_=network.evaluator(10.0,old,dt)(np.array(state.joint.node_v),jacobian=False)
                    self.assertLess(np.max(np.abs(r)),1e-11)
                    actual=network.joint.state(np.array(state.joint.node_v),10.0,old.joint,dt)
                    self.assertEqual(actual.audio_capacitor_v,state.joint.audio_capacitor_v)
                    self.assertEqual(actual.c10_v,state.joint.c10_v)
                    self.assertEqual(actual.contour.capacitor_v,state.joint.contour.capacitor_v)
                    candidate=network.latch.evaluate(state.joint.node_v,old.latch,dt)["candidate"]
                    self.assertEqual(candidate,state.latch)
                    old=state
                end=row["start_s"]+row["dt_s"]
            self.assertEqual(end,case["final_time_s"])
            self.assertEqual(json.loads(json.dumps(pack(old))),case["final"])
            self.assertEqual(case["accepted_backward_euler_steps"],2*len(case["accepted"]))

    def test_step_doubling_and_mode_guard_regenerate_across_transition(self):
        for index,case in enumerate(self.report["cases"]):
            network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
            rows=case["accepted"]
            smallest=min(range(len(rows)),key=lambda i:rows[i]["dt_s"])
            for i in sorted(set((0,len(rows)//2,smallest,len(rows)-1))):
                row=rows[i]
                old=unpack(network,case["initial"] if i==0 else rows[i-1]["fine"],0.0 if i==0 else 10.0)
                snapshot=copy.deepcopy(old)
                full,_=network.step(old,10.0,row["dt_s"])
                half=unpack(network,row["half"],10.0);fine=unpack(network,row["fine"],10.0)
                d=row["diagnostics"];p=POLICIES[index]
                self.assertAlmostEqual(scaled_error(full.joint.node_v,fine.joint.node_v,p.voltage_abs_v,p.voltage_relative),d["voltage_error_ratio"],delta=1e-5)
                self.assertAlmostEqual(scaled_error(charges(full),charges(fine),p.charge_abs_c,p.charge_relative),d["charge_error_ratio"],delta=1e-5)
                change=max(np.max(np.abs(voltages(network,half)-voltages(network,old))),np.max(np.abs(voltages(network,fine)-voltages(network,half))))
                self.assertEqual(change,d["junction_increment_v"])
                self.assertAlmostEqual(frozen_rate(network,half,10.0),d["frozen_positive_rates_per_s"][1],delta=1e-3)
                self.assertAlmostEqual(frozen_rate(network,fine,10.0),d["frozen_positive_rates_per_s"][2],delta=1e-3)
                # Same half-interval history for every FD column, including
                # the smallest accepted time scale in each policy.
                r,j=network.evaluator(10.0,old,row["dt_s"]/2)(np.array(half.joint.node_v))
                rf,jf=network.evaluator(10.0,old,row["dt_s"]/2)(np.array(half.joint.node_v),use_fd=True)
                self.assertTrue(np.all(np.abs(j-jf)<1e-8+2e-5*np.abs(jf)))
                np.testing.assert_allclose(r,rf,atol=0,rtol=0)
                self.assertEqual(old,snapshot)

    def test_rejected_trials_name_the_unchanged_accepted_state(self):
        for case in self.report["cases"]:
            network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
            states={0.0:unpack(network,case["initial"],0.0)}
            for row in case["accepted"]:
                states[row["start_s"]+row["dt_s"]]=unpack(network,row["fine"],10.0)
            self.assertGreater(len(case["rejected"]),0)
            for row in case["rejected"]:
                self.assertEqual(state_hash(states[row["time_s"]]),row["previous_state_sha256"])
            self.assertEqual(case["attempts"],len(case["accepted"])+len(case["rejected"]))
            self.assertEqual(case["history_reset_count"],0)
            self.assertIsNone(case["selected_alternative"])
            if not case["complete"]:self.assertIsNotNone(case["stop"])

    def test_invalid_policy_trial_and_empty_quality_fail_without_publication(self):
        p=POLICIES[0]
        for name,value in (("voltage_abs_v",0),("charge_relative",float("nan")),("maximum_attempts",True),
                           ("minimum_step_s",p.maximum_step_s*2)):
            with self.assertRaises(ValueError):replace(p,**{name:value})
        network=ChargedNetwork(200,model_parameters(1,"finite_transit"))
        old=unpack(network,self.report["cases"][0]["initial"],0.0);snapshot=copy.deepcopy(old)
        for h in (0,-1,float("nan"),p.minimum_step_s/2,p.maximum_step_s*2):
            with self.assertRaises(ValueError):trial(network,old,10.0,h,p,0.0)
        with self.assertRaises(ValueError):trial(network,old,10.0,p.maximum_step_s,p,float("inf"))
        self.assertEqual(old,snapshot)
        empty=copy.deepcopy(self.report);empty["cases"]=[];self.assertFalse(quality(empty))
        altered=copy.deepcopy(self.report);altered["cases"][0]["policy"]["voltage_abs_v"]*=10;self.assertFalse(quality(altered))
        self.assertTrue(quality(self.report))

    def test_refinement_observation_hashes_and_unadmitted_scope(self):
        a,b=self.report["cases"]
        ta,va=trace(a);tb,vb=trace(b)
        times=np.unique(np.concatenate((ta,tb)));times=times[times<=min(ta[-1],tb[-1])]
        start=max(ta[1],tb[1]);times=times[times>=start]
        aa=np.column_stack([np.interp(times,ta,va[:,k]) for k in range(94)])
        bb=np.column_stack([np.interp(times,tb,vb[:,k]) for k in range(94)])
        self.assertEqual(float(np.max(np.abs(aa-bb))),self.report["refinement"]["max_node_difference_v"])
        self.assertEqual(start,self.report["refinement"]["comparison_start_s"])
        for path,h in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        for flag in ("independent_trajectory_oracle","temporal_error_bound_admitted","physical_charge_identified","physical_switching_admitted","audio_admitted"):
            self.assertFalse(self.report[flag])
        self.assertIsNone(self.report["selected"])


if __name__=="__main__":unittest.main()
