from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_latch_bdf_rational_solve import solve as rational_solve
from loudness_latch_bdf_transfer_solve import solve,backward_errors
from loudness_latch_bdf_reference import BdfNetwork
from loudness_latch_bdf_probes import unpack
from loudness_latch_bdf_memory_transfer import stamps
from bjt_charge_ngspice_probes import model_parameters


class TransferSolve(unittest.TestCase):
    def test_scaled_system_matches_independent_two_by_two_rational_inverse(self):
        j=np.array([[1e-20,0.],[-.5,2e10]])
        b=np.array([[1e-20,2e-20],[3e10,0.]])
        before=(j.copy(),b.copy());a,c,d,e=map(F.from_float,j.ravel())
        expected=[]
        for col in range(2):
            u,v=map(F.from_float,b[:,col]);det=a*e-c*d
            expected.append((float((e*u-c*v)/det),float((a*v-d*u)/det)))
        expected=np.array(expected).T
        x,receipt=solve(j,b);exact,proof=rational_solve(j,b)
        np.testing.assert_array_equal(exact,expected)
        np.testing.assert_allclose(x,expected,rtol=1e-14,atol=0)
        self.assertTrue(proof["exact_rational_residual_zero"])
        self.assertLess(receipt["binary_componentwise_backward_error"],1e-10)
        np.testing.assert_array_equal(j,before[0]);np.testing.assert_array_equal(b,before[1])

    def test_actual_failed_map_reproduces_then_refines_under_unchanged_gate(self):
        r=json.loads(gzip.decompress((ROOT/"evidence/loudness_latch_bdf_memory_windows_attempt1.json.gz").read_bytes()))
        n=BdfNetwork(200,model_parameters(1,"finite_transit"));old=unpack(n,r["initial"])
        s=r["reference_step"];new=unpack(n,s["history"]);d=s["diagnostics"]
        virtual,c=n.effective_history(old,d["actual_dt_s"])
        _,j=n.network.increment_evaluator(10.,virtual,c["effective_dt_s"])(np.array(d["increment_v"]))
        b,_,_=stamps(n,new,c["effective_dt_s"])
        raw=np.linalg.solve(j,b)
        np.testing.assert_array_equal(raw,np.array(r["failed_operator"]["node_map"]))
        _,errors=backward_errors(j,b,raw)
        self.assertGreater(errors["binary_componentwise_backward_error"],r["backward_gate"])
        x,audit=solve(j,b);exact,_=rational_solve(j,b)
        self.assertEqual(audit["backward_gate"],r["backward_gate"])
        self.assertLess(max(backward_errors(j,b,x)[1].values()),r["backward_gate"])
        self.assertLess(np.max(np.abs(x-exact)/(1+np.abs(exact))),1e-10)
        self.assertGreater(audit["refinements"],0)

    def test_singular_nonfinite_or_incomplete_inputs_are_rejected(self):
        for function in (solve,rational_solve):
            for j,b in ((np.zeros((2,2)),np.ones((2,1))),
                        (np.array([[1.,1.],[1.,1.]]),np.ones((2,1))),
                        (np.array([[float("nan")]]),np.ones((1,1))),
                        (np.eye(2),np.ones((1,1)))):
                with self.assertRaises((ValueError,np.linalg.LinAlgError)):function(j,b)
