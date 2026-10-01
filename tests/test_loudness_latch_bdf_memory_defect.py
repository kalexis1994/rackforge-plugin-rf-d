from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from loudness_latch_bdf_memory_defect import OUTPUT,RATIOS,COUNTS,step,doubling,memory_gain,uniform_error,uniform_difference,generate


def read(value):return F(value["numerator"],value["denominator"])


class MemoryDefect(unittest.TestCase):
    def test_recurrence_satisfies_independent_quadratic_derivative(self):
        # Derivative of the Lagrange interpolant at destination, directly
        # from its three abscissae; no BDF coefficient helper is used.
        for r in RATIOS:
            h=F(1);k=h/r
            for t,current,previous in ((F(0),F(0),-k**3),(F(7,3),F(8,9),F(-11,7))):
                new=step(t,current,previous,k,h)
                x=(t-k,t,t+h);y=(previous,current,new);derivative=F(0)
                for i in range(3):
                    others=[j for j in range(3) if j!=i]
                    a,b=others
                    derivative+=y[i]*((x[2]-x[a])+(x[2]-x[b]))/((x[i]-x[a])*(x[i]-x[b]))
                self.assertEqual(derivative,3*(t+h)**2)

    def test_shared_offset_is_invisible_but_global_error_moves(self):
        for r in RATIOS:
            k=1/r;a,b=doubling(F(0),F(0),-k**3,k,F(1))
            for offset in (F(1,100),F(-17,5)):
                c,d=doubling(F(0),offset,-k**3+offset,k,F(1))
                self.assertEqual(c-d,a-b)
                self.assertEqual(c-a,offset);self.assertEqual(d-b,offset)

    def test_history_difference_gain_and_exact_local_cancellation(self):
        for r in RATIOS:
            k=1/r;a,b=doubling(F(0),F(0),-k**3,k,F(1))
            for current_error,previous_error in ((F(2,7),F(-3,5)),(F(0),F(19,4))):
                c,d=doubling(F(0),current_error,-k**3+previous_error,k,F(1))
                self.assertEqual((c-d)-(a-b),memory_gain(r)*(current_error-previous_error))
            previous_error=(a-b)/memory_gain(r)
            c,d=doubling(F(0),F(0),-k**3+previous_error,k,F(1))
            self.assertEqual(c,d);self.assertNotEqual(c,F(1))
        c,d=doubling(F(0),F(0),F(-1)+F(19,4),F(1),F(1))
        self.assertEqual(c,F(3,4));self.assertEqual(d,F(3,4))

    def test_uniform_published_memory_accumulates_despite_bounded_local_difference(self):
        for h in (F(1),F(1,1000)):
            previous=-h**3;current=F(0)
            for n in range(1,max(COUNTS)+1):
                full,fine=doubling((n-1)*h,current,previous,h,h)
                self.assertEqual(full-(n*h)**3,uniform_error(n,h))
                self.assertEqual(full-fine,uniform_difference(n,h))
                self.assertLess(full-fine,F(9,8)*h**3)
                previous,current=current,full
            self.assertGreater(uniform_error(256,h)/uniform_difference(256,h),450)
        # At a fixed final T=1, h=1/N: global error still converges as h^2.
        self.assertGreater(uniform_error(64,F(1,64)),uniform_error(256,F(1,256)))

    def test_stored_proof_source_and_scope(self):
        report=json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(report,generate())
        for source,h in report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),h)
        for row in report["ratios"]:
            self.assertEqual(read(row["difference"]),read(row["shifted_difference"]))
            self.assertEqual(read(row["cancelled_difference"]),0)
            self.assertNotEqual(read(row["cancelled_full_error"]),0)
        for key in ("nonlinear_DAE_calibrated","temporal_error_bound_admitted","physical_switching_admitted","audio_admitted"):
            self.assertFalse(report[key])


if __name__=="__main__":unittest.main()
