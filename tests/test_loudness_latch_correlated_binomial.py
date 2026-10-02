import sys,unittest
from fractions import Fraction as F
from math import comb,isqrt
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import loudness_latch_correlated_enclosure as bound
import loudness_latch_dense_charge as poly
from bjt_charge_ngspice_probes import model_parameters


class IndependentBinomial(unittest.TestCase):
    def test_half_grading_81_exact_coefficients_and_rational_sqrt_amplitude(self):
        parameters=model_parameters(1,'finite_transit');dep=parameters.depletion_be
        v=(F(1,10),F(1,100),F(1,1000));center=poly.evaluate(v,F(1,2))
        cp,error,_=bound.capacitance_polynomial(v,dep,0.,parameters.saturation_a,parameters.emission_be_v,F(0),F(1),True)
        target=1/(1-center/F(dep.potential_v));grid=1<<512
        integer=isqrt(target.numerator*grid*grid//target.denominator)
        amplitude=(F(dep.cj0_f)*F(integer,grid),F(dep.cj0_f)*F(integer+1,grid))
        self.assertLessEqual(F(integer,grid)**2,target);self.assertGreater(F(integer+1,grid)**2,target)
        for u in (F(0),F(1,4),F(1,2),F(3,4),F(1)):
            w=(poly.evaluate(v,u)-center)/(F(dep.potential_v)-center)
            series=sum((F(comb(2*k,k),4**k)*w**k for k in range(81)),F(0))
            tail=amplitude[1]*abs(w)**81/(1-abs(w))
            values=[a*series for a in amplitude];lo=min(values)-tail;hi=max(values)+tail
            actual=poly.evaluate(cp,u);self.assertLessEqual(actual-error,lo);self.assertGreaterEqual(actual+error,hi)

    def test_binomial_range_guard_and_exact_knee_capacitance_continuity(self):
        p=model_parameters(1,'finite_transit');dep=p.depletion_be;knee=F(dep.forward_fraction*dep.potential_v)
        with self.assertRaisesRegex(ValueError,'binomial remainder domain'):
            bound.capacitance_polynomial((F(-10),F(20),F(-10)),dep,0.,p.saturation_a,p.emission_be_v,F(0),F(1),True)
        reference=bound.old.junction_bounds(dep,p.transit_forward_s,p.saturation_a,p.emission_be_v,knee)[1]
        for below in (True,False):
            cp,error,_=bound.capacitance_polynomial((knee,),dep,p.transit_forward_s,p.saturation_a,p.emission_be_v,F(0),F(1),below)
            value=poly.evaluate(cp,F(1,2))
            # Independent point enclosure must overlap each continued representation.
            self.assertLessEqual(value-error,reference[1]);self.assertGreaterEqual(value+error,reference[0])
