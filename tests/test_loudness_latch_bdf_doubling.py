import copy
import json
import hashlib
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack,publication_check
from loudness_latch_bdf_survey import state_hash
from loudness_latch_bdf_doubling import estimate,trial,cubic_error_factors
from loudness_latch_bdf_doubling_probes import OUTPUT
from loudness_latch_increment_time import Policy,nodes,junctions,differences
from loudness_latch_time_reference import frozen_rate


class BdfDoubling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(OUTPUT.read_text())
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_full_and_both_half_steps_close_real_charge_and_keep_intermediate_memory(self):
        n=self.network
        for row in self.report["probes"]:
            old=unpack(n,row["previous"]);snapshot=state_hash(old)
            full=unpack(n,row["full"]);diag=row["diagnostics"]
            middle,fine=[unpack(n,s["history"]) for s in diag["shadow_half_steps"]]
            self.assertEqual(full.previous,old.current);self.assertEqual(middle.previous,old.current)
            self.assertEqual(fine.previous,middle.current);self.assertEqual(full.time_s,fine.time_s)
            paths=((old,full,row["full_diagnostics"],diag["full_publication"]),
                   (old,middle,diag["shadow_half_steps"][0]["diagnostics"],diag["shadow_half_steps"][0]["publication"]),
                   (middle,fine,diag["shadow_half_steps"][1]["diagnostics"],diag["shadow_half_steps"][1]["publication"]))
            for previous,candidate,d,stored in paths:
                h=d["actual_dt_s"];self.assertGreaterEqual(h,1e-12)
                virtual,c=n.effective_history(previous,h);self.assertLessEqual(c["ratio"],2.)
                delta=np.array(d["increment_v"])
                residual,_=n.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(delta,False)
                self.assertLess(np.max(np.abs(residual)),1e-11)
                self.assertEqual(n.network.publish(delta,10.,virtual,c["effective_dt_s"]),candidate.current)
                check=publication_check(n,previous,candidate,h,d)
                self.assertEqual(check,stored);self.assertLess(check["max_published_kcl_a"],1e-11)
                self.assertLess(check["max_branch_equation_error_v"],1e-14)
            self.assertEqual(diag["maximum_node_difference_v"],float(np.max(np.abs(differences(nodes(full.current),nodes(fine.current))))))
            self.assertEqual(diag["maximum_junction_difference_v"],float(np.max(np.abs(differences(junctions(n.network,full.current),junctions(n.network,fine.current))))))
            self.assertEqual(state_hash(old),snapshot)

    def test_replay_and_fd_reproduce_full_and_provisional_halves(self):
        n=self.network
        for row in self.report["probes"]:
            if row["ratio"] not in (.25,2.):continue
            old=unpack(n,row["previous"]);incoming=copy.deepcopy(old)
            full,_,fine,diag=estimate(n,old,10.,row["dt_s"])
            self.assertEqual(full,unpack(n,row["full"]));self.assertEqual(fine,unpack(n,row["fine"]))
            self.assertEqual(diag["maximum_node_difference_v"],row["diagnostics"]["maximum_node_difference_v"])
            fd,fd_diag=n.advance(old,10.,row["dt_s"],use_fd=True)
            half,hdiag=n.advance(old,10.,row["dt_s"]/2,use_fd=True)
            end,ediag=n.advance(half,10.,fd.time_s-half.time_s,use_fd=True)
            for previous,candidate,d,target in ((old,fd,fd_diag,full),(old,half,hdiag,unpack(n,diag["shadow_half_steps"][0]["history"])),(half,end,ediag,fine)):
                self.assertLess(np.max(np.abs(np.array(candidate.current.joint.node_v)-target.current.joint.node_v)),1e-8)
                self.assertLess(publication_check(n,previous,candidate,d["actual_dt_s"],d)["max_published_kcl_a"],1e-11)
            self.assertEqual(incoming,old)

    def test_exact_cubic_history_exposes_invalid_division_by_three(self):
        for row in self.report["cubic"]:
            factors=cubic_error_factors(row["ratio"])
            self.assertAlmostEqual(row["full_error_v"],factors["full"],places=13)
            self.assertAlmostEqual(row["fine_error_v"],factors["fine"],places=13)
            self.assertAlmostEqual(row["full_minus_fine_v"],factors["difference"],places=13)
            self.assertNotAlmostEqual(row["fine_error_v"],row["divided_by_three_v"],places=6)
        r=next(r for r in self.report["cubic"] if r["ratio"]==1.)
        self.assertAlmostEqual(r["fine_error_v"]/r["full_minus_fine_v"],13/19,places=14)
        for ratio in (0.,-1.,2.5,float("nan")):
            with self.assertRaises(ValueError):cubic_error_factors(ratio)

    def test_accepted_trial_returns_full_path_and_keeps_half_steps_unpublished(self):
        n=self.network;row=self.report["probes"][7];old=unpack(n,row["previous"]);incoming=copy.deepcopy(old)
        p=Policy(1.,1.,1.,1.,1.,1.,1e-4,1e-12,100)
        rate=frozen_rate(n.network,old.current,10.)
        result,diag,next_rate=trial(n,old,10.,row["dt_s"],p,rate)
        self.assertIsNotNone(result);self.assertEqual(len(result),1)
        self.assertEqual(result[0][0],unpack(n,row["full"]))
        self.assertEqual(diag["published_candidate"],"full-step")
        self.assertFalse(diag["richardson_factor_applied"])
        for s in diag["shadow_half_steps"]:self.assertFalse(s["published"])
        self.assertGreaterEqual(next_rate,0.);self.assertEqual(incoming,old)

    def test_bad_domain_source_bootstrap_and_tight_rejection_preserve_incoming_memory(self):
        n=self.network;row=self.report["probes"][7];old=unpack(n,row["previous"]);incoming=copy.deepcopy(old)
        for key,h in ((0.,row["dt_s"]),(10.,1e-12),(10.,float("nan")),(10.,3*old.previous_dt_s)):
            with self.assertRaises(ValueError):estimate(n,old,key,h)
            self.assertEqual(incoming,old)
        dc,_=n.initial_history()
        with self.assertRaises(ValueError):estimate(n,dc,0.,1e-6)
        p=Policy(1e-15,1e-15,1e-15,1e-15,1.,1.,1e-4,1e-12,100)
        result,diag,rate=trial(n,old,10.,row["dt_s"],p,frozen_rate(n.network,old.current,10.))
        self.assertIsNone(result);self.assertIsNone(rate)
        self.assertEqual(diag["reason"],"voltage-error-or-junction-increment")
        self.assertGreater(max(diag["voltage_error_ratio"],diag["junction_voltage_error_ratio"]),1.)
        self.assertEqual(incoming,old)

    def test_sources_and_prototype_scope(self):
        r=self.report
        for path,h in r["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        for flag in ("adaptive_trajectory_generated","temporal_refinement_admitted","temporal_error_bound_admitted",
                     "physical_switching_admitted","audio_admitted"):
            self.assertFalse(r[flag])


if __name__=="__main__":unittest.main()
