"""Reject misleading diagnosis records and trajectory comparisons."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_newton_trace as trace
import voice_newton_probe as probe


class ObservationTests(unittest.TestCase):
    def test_nan_in_later_vector_rejected(self):
        raw=np.zeros((2,7));raw[1,0]=1;raw[1,6]=np.nan
        with self.assertRaises(ValueError):probe.exact(raw,raw)

    def test_partial_clock_is_compared_exactly(self):
        raw=np.zeros((2,7));raw[1,0]=.002
        self.assertTrue(probe.exact(raw,raw.copy())['passed'])
        other=raw.copy();other[1,0]=np.nextafter(other[1,0],1)
        self.assertFalse(probe.exact(raw,other)['passed'])

    def test_malformed_and_nonfinite_records_rejected(self):
        for line in ('RFTRACE,step,1,1,0','RFTRACE,step,nan,1,0,1','RFTRACE,trunc,1,0,1,0'):
            with self.assertRaises(ValueError):trace.parse(line)

    def test_reported_correction_must_match_values(self):
        with self.assertRaises(ValueError):trace.parse('RFTRACE,iteration,1,1,1,1,1,x,20,1,2,.1')

    def test_newton_and_truncation_rejections_stay_separate(self):
        records=trace.parse('\n'.join((
            'RFTRACE,iteration,1,.1,1,1,0,x,10,1,2,.1',
            'RFTRACE,step,1,.1,0,2',
            'RFTRACE,trunc,1,.1,.05,0',
            'RFTRACE,jfet,1,.01,jq,0,2,1,.1,4,3,.1,-2,-3',
            'RFTRACE,iteration,1,.01,101,1,1,x,2,1,1.2,.1',
            'RFTRACE,step,1,.01,103,1')))
        report=trace.summarize(records)
        self.assertEqual(report['newton_nonzero_returns'],1)
        self.assertEqual(report['truncation_reductions'],1)
        self.assertEqual(report['last_attempt_iterations'],1)
        self.assertEqual(report['last_attempt_rejected_devices'],{'jq':1})
        self.assertEqual(report['last_attempt_limiter_events'],0)
        self.assertFalse(report['full_nonlinear_kcl_residual_observed'])

    def test_identical_attempt_clock_does_not_select_earlier_step(self):
        rows=['RFTRACE,iteration,1,.1,1,1,0,x,10,1,2,.1',
              'RFTRACE,step,1,.1,103,1',
              'RFTRACE,iteration,1,.1,2,1,0,y,10,1,2,.1',
              'RFTRACE,step,1,.1,103,1']
        report=trace.summarize(trace.parse('\n'.join(rows)))
        self.assertEqual(report['last_attempt_last_iterations'][0]['node'],'y')


if __name__=='__main__':unittest.main()
