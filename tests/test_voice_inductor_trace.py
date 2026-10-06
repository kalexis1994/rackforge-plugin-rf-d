"""Negative association gates and independent high precision constitutive checks."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_inductor_trace as trace


class TraceTests(unittest.TestCase):
    LOAD='RFLTRACE,load,1,.1,l.xic3.l2,1,257,3,1,1,1,0,10,-10,0,0,10,-10,1,0,0'
    SOLVE='RFLTRACE,solve,1,.1,1,3,1,1,0,0'

    def test_association_rejects_branch_current_and_missing_load(self):
        for text in (self.SOLVE,self.LOAD+'\n'+self.LOAD,self.LOAD+'\n'+self.SOLVE.replace(',3,1,1,',',4,1,1,'),
                     self.LOAD+'\n'+self.SOLVE.replace(',3,1,1,',',3,2,1,')):
            with self.assertRaises(ValueError):trace.pairs(text)

    def test_nonfinite_late_history_rejected(self):
        with self.assertRaises(ValueError):trace.pairs(self.LOAD.replace(',10,-10,0,',',10,-10,nan,')+'\n'+self.SOLVE)

    def test_decimal_retains_small_residual_lost_in_double(self):
        p=trace.pairs(self.LOAD+'\n'+self.SOLVE)[0]
        p['load'].update(req_ohm=1e16,veq_v=-1e16,a0_per_s=1e16,a1_per_s=-1e16)
        p['solve']['pos_v']=.001
        m=trace.evaluate(p)
        self.assertEqual(m['stamped_row_residual_v'],.001)
        self.assertEqual(m['history_stamp_error_v'],0)
        self.assertEqual((.001-1e16)-(-1e16),0)
        self.assertEqual(m['best_binary64_row_residual_v'],.001)
        self.assertGreater(m['stamp_voltage_per_current_ulp_v'],1)

    def test_gear_two_uses_second_real_history(self):
        p=trace.pairs(self.LOAD+'\n'+self.SOLVE)[0]
        p['load'].update(order=2,a0_per_s=15,a1_per_s=-20,a2_per_s=5,flux2_wb=3,req_ohm=15,veq_v=-5)
        p['solve'].update(pos_v=10,new_current_a=1)
        m=trace.evaluate(p)
        self.assertEqual(m['history_stamp_error_v'],0)
        self.assertEqual(m['stamped_row_residual_v'],0)

    def test_repeated_clock_starts_another_attempt(self):
        first=trace.pairs(self.LOAD+'\n'+self.SOLVE+'\n'+self.LOAD+'\n'+self.SOLVE)
        self.assertEqual([p['attempt'] for p in first],[1,2])
        self.assertEqual(trace.summarize(first)['final_attempt_iterations'],1)


if __name__=='__main__':unittest.main()
