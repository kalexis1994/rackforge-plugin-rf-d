"""Rational transformation, independent roots and memory invariants."""
import sys,unittest
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_741_row_math as math


class RowTests(unittest.TestCase):
    def test_row_operation_exact_across_scales(self):
        g=F(1,1000);gm=F(31623,10**12)
        for req in (F(0),F(1),F(10**7),F(1061*10**14)):
            rows=math.original_rows(req,g,gm);gain=(req+1/g)*gm;scale=max(F(1),gain)
            combined=tuple((rows[0][k]-req*(rows[1][k]+rows[2][k])-rows[2][k]/g)/scale for k in range(6))
            reduced,rhs=math.stamps(req,F(-11),g,gm)
            self.assertEqual(reduced,combined);self.assertEqual(rhs,F(-11)/scale)

    def test_independent_dc_root(self):
        g=F(1,8);gm=F(1,4);v98=F(1);control=F(-1);i=-gm*control
        v17=v98;v16=v17-i/g;values=(v98,v17,v16,control,F(0),i)
        row,rhs=math.stamps(F(0),F(0),g,gm)
        self.assertEqual(sum(a*b for a,b in zip(row,values)),rhs)

    def test_gear_one_and_two_shared_real_histories(self):
        history=(F(7,100),F(3,100));copy=tuple(history);L=F(1061,2000)
        for order,coeff in ((1,(F(10),F(-10),F(0))),(2,(F(15),F(-20),F(5)))):
            req,veq=math.history_stamp(order,coeff,history,L)
            g=F(1,1000);gm=F(1,100);v98=F(1);control=F(-2);i=-gm*control
            v17=v98-req*i-veq;v16=v17-i/g;values=(v98,v17,v16,control,F(0),i)
            for row,rhs in ((math.original_rows(req,g,gm)[0],veq),math.stamps(req,veq,g,gm)):
                self.assertEqual(sum(a*b for a,b in zip(row,values)),rhs)
            self.assertEqual(history,copy)

    def test_scale_divides_rhs_and_preserves_sign(self):
        row,rhs=math.stamps(F(1000),F(-11),F(1,8),F(1,4))
        self.assertEqual(row[3],1);self.assertEqual(row[4],-1)
        self.assertEqual(rhs,F(-11,252))

    def test_invalid_domain_rejected(self):
        for g,gm,req in ((F(0),F(1),F(1)),(F(1),F(-1),F(1)),(F(1),F(1),F(-1))):
            with self.assertRaises(ValueError):math.stamps(req,F(0),g,gm)


if __name__=='__main__':unittest.main()
