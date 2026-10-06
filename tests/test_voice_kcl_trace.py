"""Orientation, exact scalars and negative association gates for selected KCL."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_kcl_trace as trace
import voice_inductor_trace as inductor


class KCLTests(unittest.TestCase):
    def text(self):
        load='RFLTRACE,load,1,.1,l.xic3.l2,1,257,3,1,1,1,0,10,-10,0,0,10,-10,1,0,0'
        solve='RFLTRACE,solve,1,.1,1,3,1,1,0,0'
        values=[1,.1,1,3,1,1,0,0,0,0,0,0,0,0,0,0,.001,.001,0,0]
        return '\n'.join(('RFKTRACE,res,1,.1,r.xic3.r13,.001','RFKTRACE,gm,1,.1,g.xic3.g4,3.1623e-8',
                          load,solve,'RFKTRACE,solve,'+','.join(map(str,values))))

    def test_oriented_kcl_and_eos_exact_binary_scalar(self):
        p=trace.pairs(self.text())[0];p['conductance_s']=.125;p['transconductance_s']=.25
        p['solve'].update(new_17_v=2,new_16_v=1,new_3_v=-.5,new_49_v=0,new_current_a=.125,
                          new_7_v=1.001,new_1_v=0)
        m=trace.evaluate(p)
        self.assertEqual(m['new_kcl17_a'],0);self.assertEqual(m['new_kcl16_a'],0)
        self.assertEqual(m['new_branch_source_mismatch_a'],0)
        self.assertLess(abs(m['new_eos_row_v']),2e-16)

    def test_positive_stamp_orientation_rejects_reversed_source(self):
        p=trace.pairs(self.text())[0];p['conductance_s']=.125;p['transconductance_s']=.25
        p['solve'].update(new_17_v=2,new_16_v=1,new_3_v=.5,new_49_v=0,new_current_a=.125)
        self.assertEqual(trace.evaluate(p)['new_kcl16_a'],-.25)

    def test_missing_duplicate_wrong_clock_and_coefficient_rejected(self):
        t=self.text();prefix=t.splitlines()[0]
        for bad in (t.replace(prefix+'\n',''),prefix+'\n'+t,
                    t.replace('gm,1,.1','gm,2,.1'),t.replace('g.xic3.g4,3.1623e-8','g.xic3.g4,3.1624e-8')):
            with self.assertRaises(ValueError):trace.pairs(bad)

    def test_late_nan_and_wrong_terminal_rejected(self):
        lines=self.text().splitlines();row=lines[-1].split(',');row[2+trace.FIELDS.index('new_17_v')]='1'
        lines[-1]=','.join(row)
        for bad in (self.text().rsplit(',',1)[0]+',nan','\n'.join(lines)):
            with self.assertRaises(ValueError):trace.pairs(bad)

    def test_exact_equivalent_source_residual_reconstructed(self):
        p=trace.pairs(self.text())[0];p['conductance_s']=.125;p['transconductance_s']=.25
        p['solve'].update(new_17_v=2,new_16_v=1,new_3_v=-.5,new_49_v=0,new_current_a=.25)
        m=trace.evaluate(p)
        self.assertEqual(m['new_kcl17_a'],-.125)
        self.assertEqual(m['new_kcl16_a'],0)
        self.assertEqual(m['req_times_branch_source_mismatch_v'],1.25)


if __name__=='__main__':unittest.main()
