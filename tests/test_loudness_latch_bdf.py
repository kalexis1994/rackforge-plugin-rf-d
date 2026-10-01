import copy
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from bjt_charge_ngspice_probes import model_parameters
from loudness_latch_bdf_reference import BdfNetwork,History,coefficients
from loudness_latch_bdf_probes import unpack,publication_check,scalar_rc
from loudness_latch_increment_probes import state_hash


class ChargeBdf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/"evidence/loudness_latch_bdf_probes.json").read_text())
        cls.network=BdfNetwork(200,model_parameters(1,"finite_transit"))

    def test_quadratic_interpolation_coefficients_and_charge_origin_invariance(self):
        for h,k in ((1.,2.),(2.,1.),(.125,1.),(1e-9,1e-9)):
            c=coefficients(h,k)
            t=np.array([0.,-h,-h-k])
            weights=np.linalg.solve(np.array([np.ones(3),t,t*t]),[0.,1.,0.])*h
            self.assertLess(np.max(np.abs(weights-[c["a0"],c["a1"],c["a2"]])),1e-14)
            F=Fraction.from_float
            a,b,z=map(F,(1e-12,1.2e-12,1.3e-12))
            derivative=lambda a,b,z:(F(c["a0"])*(a-b)-F(c["a2"])*(b-z))/F(h)
            for origin in map(F,(-1e-9,0.,1e-9)):
                self.assertEqual(derivative(a+origin,b+origin,z+origin),derivative(a,b,z))

    def test_startup_occurs_only_once_and_fd_reproduces_charge_states(self):
        n=self.network
        for k,row in enumerate(self.report["intervals"]):
            old=unpack(n,row["old"]);snapshot=copy.deepcopy(old)
            new,d=n.advance(old,10.,row["dt_s"])
            self.assertEqual(new,unpack(n,row["new"]))
            self.assertEqual(old,snapshot)
            self.assertEqual(new.previous,old.current)
            self.assertEqual(new.previous_dt_s,row["dt_s"])
            self.assertLess(d["max_kcl_a"],1e-11);self.assertLess(d["correction_v"],1e-8)
            self.assertEqual(d["method"],"backward-euler-startup" if k==0 else "variable-bdf2-charge/v1")
            self.assertLess(row["fd_max_node_difference_v"],1e-8)
            self.assertLess(row["jacobian_max_scaled_difference"],1e-8)

    def test_direct_true_history_charge_conservation_including_series_c10(self):
        n=self.network
        for row in self.report["intervals"]:
            old,new=unpack(n,row["old"]),unpack(n,row["new"])
            check=publication_check(n,old,new,row["dt_s"],row["diagnostics"])
            self.assertEqual(check,row["publication"])
            self.assertLess(check["max_published_kcl_a"],1e-11)
            self.assertLess(check["max_branch_equation_error_v"],1e-14)
            self.assertTrue(check["round_trip_exact"])
            for device in check["nonlinear_devices"]:
                self.assertLess(abs(device["sum_terminal_a"]),1e-50)

    def test_scalar_rc_refinement_is_second_order_after_declared_be_startup(self):
        rows=self.report["scalar_rc"]
        for row in rows:self.assertEqual(scalar_rc(row["dt_s"]),row)
        for a,b in zip(rows,rows[1:]):
            self.assertGreater(a["final_error_v"]/b["final_error_v"],3.8)
            self.assertLess(a["final_error_v"]/b["final_error_v"],4.3)
        self.assertLess(rows[-1]["final_error_v"],1e-6)

    def test_bad_interval_or_history_never_falls_back_or_changes_either_state(self):
        n=self.network;old=unpack(n,self.report["intervals"][2]["old"])
        snapshots=(state_hash(old.current),state_hash(old.previous))
        for h in (0.,float("nan"),3*old.previous_dt_s):
            with self.assertRaises(ValueError):n.advance(old,10.,h)
        with self.assertRaises(ValueError):n.advance(old,10.,old.previous_dt_s,iterations=1)
        with self.assertRaises(ValueError):replace(old,previous=None,previous_dt_s=None,previous_key_v=None)
        other=BdfNetwork(200000,model_parameters(1,"finite_transit"))
        with self.assertRaises(ValueError):other.advance(old,10.,old.previous_dt_s)
        self.assertEqual((state_hash(old.current),state_hash(old.previous)),snapshots)

    def test_pinned_sources_and_scope(self):
        for path,h in self.report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
        for flag in ("independent_spatial_oracle","physical_switching_admitted","temporal_refinement_admitted","audio_admitted"):
            self.assertFalse(self.report[flag])
        self.assertEqual(self.report["history_reset_count"],0)


if __name__=="__main__":unittest.main()
