import sys,unittest
from pathlib import Path
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_matrix_trace as m
import voice_matrix_rounding as rounding

SAMPLE='''RFMATRIX,begin,0.0022774,5e-18,100,1,257,2,4,0
RFMATRIX,node,0,5,3,node,4,0
RFMATRIX,node,1,7,4,branch,7,0
RFMATRIX,factor,refactor-after-gmin,2,0.001,0
RFMATRIX,a,0,0,2
RFMATRIX,a,1,0,1
RFMATRIX,a,0,1,1
RFMATRIX,a,1,1,3
RFMATRIX,x,0,1
RFMATRIX,x,1,2
RFMATRIX,end
'''

class MatrixTests(unittest.TestCase):
    def test_complete_mapping_units_solution(self):
        s=m.parse(SAMPLE)[0];r=m.analyze(s)
        self.assertEqual(r['rows'][0]['unknown_unit'],'V');self.assertEqual(r['rows'][0]['row_unit'],'A')
        self.assertEqual(r['rows'][1]['old'],7);self.assertEqual(r['rows'][1]['row_unit'],'V')
        self.assertEqual(Decimal(r['rows'][1]['observed_minus_precise']),0)
    def test_incomplete_missing_x(self):
        with self.assertRaises(ValueError):m.parse(SAMPLE.replace('RFMATRIX,x,1,2\n',''))
    def test_duplicate_entry_and_snapshot(self):
        with self.assertRaises(ValueError):m.parse(SAMPLE.replace('RFMATRIX,end','RFMATRIX,a,0,0,2\nRFMATRIX,end'))
        with self.assertRaises(ValueError):m.parse(SAMPLE+SAMPLE)
    def test_bad_map_nan_or_selection(self):
        for old,new in [('node,1,7','node,1,5'),('x,1,2','x,1,nan'),('5e-18','5e-16'),('node,0,5,3','node,0,5,-1')]:
            with self.subTest(new=new),self.assertRaises(ValueError):m.parse(SAMPLE.replace(old,new))
    def test_factor_retry_requires_separate_capture(self):
        with self.assertRaises(ValueError):m.parse(SAMPLE.replace('RFMATRIX,x,0,1','RFMATRIX,factor,factor-after-gmin,2,0.001,0\nRFMATRIX,x,0,1'))
    def test_binary64_is_exact_decimal(self):
        self.assertEqual(m.exact(.1),Decimal.from_float(.1));self.assertNotEqual(m.exact(.1),Decimal('0.1'))
    def test_pivoting(self):
        d=Decimal;f=m.lu([[d(0),d(1)],[d(2),d(1)]])
        self.assertEqual(m.solve_factored(f,[d(3),d(7)]),[d(2),d(3)])
    def test_singular(self):
        with self.assertRaises(ValueError):m.lu([[Decimal(0)]])
    def test_small_backward_error_can_hide_large_voltage_error(self):
        s=m.parse(SAMPLE)[0];eps=2.**-52
        s['entries']={(0,0):1.,(0,1):1.,(1,0):1.,(1,1):1.+eps}
        s['nodes'][0]['b']=0.;s['nodes'][1]['b']=eps
        s['x']={0:-.5,1:.5};r=m.analyze(s)
        self.assertEqual(Decimal(r['rows'][0]['observed_minus_precise']),Decimal('.5'))
        self.assertLess(Decimal(r['rows'][1]['componentwise_backward_error']),Decimal('2e-16'))
    def test_absent_selection_is_explicit_empty_not_substitution(self):
        self.assertEqual(m.parse('ngspice-46 done\n'),[])
    def test_rounding_single_publication(self):
        s=m.parse(SAMPLE)[0];r=rounding.rounded(s,m.analyze(s))
        self.assertEqual(Decimal(r['rows'][0]['rounding_error']),0)
        self.assertEqual(Decimal(r['rows'][1]['residual']),0)
    def test_decomposition_keeps_different_system_scope(self):
        s=m.parse(SAMPLE)[0];a=m.analyze(s);s['x'][0]=1.5;b=m.analyze(s)
        r=rounding.decompose(a,b,'node')
        self.assertEqual(Decimal(r['observed_change']),Decimal('.5'))
        self.assertEqual(Decimal(r['precise_roots_change']),0)
        self.assertEqual(Decimal(r['linear_error_change']),Decimal('.5'))

if __name__=='__main__':unittest.main()
