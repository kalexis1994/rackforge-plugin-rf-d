import sys,unittest
from pathlib import Path
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_matrix_trace as matrix
import voice_refine_trace as refine
import voice_refine_arithmetic_retry as arithmetic
from test_voice_matrix import SAMPLE

def replay():
    text=SAMPLE.split('RFMATRIX,x,')[0]
    text+='RFREFINE,replay,three-corrections,pair-fma,all-real-NI\n'
    for i in range(2):text+=f'RFREFINE,original,{i},0\n'
    for step in range(3):
        for i,r in enumerate((4,7) if step==0 else (0,0)):text+=f'RFREFINE,r,{step},{i},{r},0\n'
        for i,x in enumerate((1,2)):
            text+=f'RFREFINE,correction,{step},{i},{x if step==0 else 0},{x},0\n'
    for i,x in enumerate((1,2)):text+=f'RFREFINE,final,{i},{x}\n'
    return text+'RFMATRIX,x,0,0\nRFMATRIX,x,1,0\nRFMATRIX,end\n'

class RefineTests(unittest.TestCase):
    def test_replay_same_matrix_precise_root(self):
        text=replay();s=matrix.parse(text)[0];d=refine.parse(text)[0]
        r=refine.compare(s,d,matrix.analyze(s));self.assertTrue(r['passed']);self.assertEqual(r['max_voltage_error'],'0')
        self.assertEqual(d['original'][0],0);self.assertEqual(s['x'][0],0);self.assertEqual(d['final'][0],1)
    def test_missing_correction(self):
        with self.assertRaises(ValueError):refine.parse(replay().replace('RFREFINE,correction,2,1,0,2,0\n',''))
    def test_duplicate_index(self):
        with self.assertRaises(ValueError):refine.parse(replay().replace('RFREFINE,final,0,1','RFREFINE,final,0,1\nRFREFINE,final,0,1'))
    def test_domain_error_is_failure(self):
        with self.assertRaises(ValueError):refine.parse('RFREFINE,error,dimension-domain-finiteness-or-matrix-change\n')
    def test_wrong_compiled_residual_rejected(self):
        text=replay().replace('RFREFINE,r,0,0,4,0','RFREFINE,r,0,0,5,0');s=matrix.parse(text)[0];d=refine.parse(text)[0]
        with self.assertRaises(ValueError):refine.compare(s,d,matrix.analyze(s))
    def test_wrong_update_rejected(self):
        text=replay().replace('RFREFINE,correction,0,0,1,1,0','RFREFINE,correction,0,0,1,1.5,0');s=matrix.parse(text)[0];d=refine.parse(text)[0]
        with self.assertRaises(ValueError):refine.compare(s,d,matrix.analyze(s))
    def test_arithmetic_exact_binary_pair(self):
        case=dict(kind='exact-product',exact=str(Decimal.from_float(.1)),scale='1')
        self.assertTrue(arithmetic.check([case],'1 0.1 0\n')[0]['passed'])
        self.assertFalse(arithmetic.check([case],'1 0.10001 0\n')[0]['passed'])
    def test_domain_rejection_and_output_count(self):
        self.assertTrue(arithmetic.check([dict(kind='domain-rejection',rejected=True)],'0\n')[0]['passed'])
        with self.assertRaises(ValueError):arithmetic.check([dict(kind='domain-rejection',rejected=True)],'')

if __name__=='__main__':unittest.main()
