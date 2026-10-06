from pathlib import Path
import sys,unittest
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_full_note_matrix_trace as m
import voice_matrix_trace as old
from test_voice_matrix import SAMPLE as ORIGINAL
SAMPLE=ORIGINAL.replace('0.0022774','0.0159404')

class LongMatrixTests(unittest.TestCase):
    def test_new_window_and_original_window_stay_separate(self):
        self.assertEqual(len(m.parse(SAMPLE)),1);self.assertEqual(len(old.parse(ORIGINAL)),1)
        with self.assertRaises(ValueError):m.parse(ORIGINAL)
        with self.assertRaises(ValueError):old.parse(SAMPLE)
    def test_complete_map_uses_original_precise_solver(self):
        r=m.analyze(m.parse(SAMPLE)[0])
        self.assertEqual(Decimal(r['rows'][0]['observed_minus_precise']),0)
        self.assertEqual(Decimal(r['rows'][1]['observed_minus_precise']),0)
    def test_incomplete_and_nonfinite_rejected(self):
        for text in (SAMPLE.replace('RFMATRIX,x,1,2\n',''),SAMPLE.replace('x,1,2','x,1,nan')):
            with self.assertRaises(ValueError):m.parse(text)
    def test_delta_and_iteration_selection_remain_strict(self):
        for text in (SAMPLE.replace('5e-18','5e-16'),SAMPLE.replace(',100,1,',',99,1,')):
            with self.assertRaises(ValueError):m.parse(text)

if __name__=='__main__':unittest.main()
