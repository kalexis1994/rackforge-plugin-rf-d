import sys,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_native_raw as raw
import voice_binary_runner as runner

class NativeTests(unittest.TestCase):
    def fixture(self,table=None,values=None,header=None,tail=b''):
        table=table or ['0 time time','1 v(x) voltage','2 i(@q[ic]) current']
        values=np.array([[0.,-0.,1e-6],[1e-6,1.,2e-6]],dtype='<f8') if values is None else values
        header=header or 'Title: fixture\nDate: fixture\nPlotname: Transient Analysis\nFlags: real\nNo. Variables: 3\nNo. Points: 2\n'
        return (header+'Variables:\n'+'\n'.join(table)+'\nBinary:\n').encode()+values.tobytes()+tail

    def parse(self,data,vectors=('v(x)','@q[ic]')):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'fixture.raw';p.write_bytes(data)
            a,meta=raw.read(p,vectors)
            return a.copy(),meta

    def test_real_layout_and_current_alias(self):
        a,m=self.parse(self.fixture());self.assertEqual(a.shape,(2,3))
        self.assertEqual(m['payload_bytes'],48);self.assertTrue(np.signbit(a[0,1]))
        self.assertEqual(m['variables'][2]['canonical_name'],'@q[ic]')

    def test_reordered_columns_restore_declared_order(self):
        values=np.array([[0,1e-6,-0.],[1e-6,2e-6,1.]],dtype='<f8')
        a,m=self.parse(self.fixture(['0 time time','1 @q[ic] current','2 v(x) voltage'],values))
        self.assertEqual(m['column_indices'],[0,2,1]);self.assertEqual(a[1,1],1.)

    def test_wrong_or_duplicate_vector_rejected(self):
        for table in (['0 time time','1 v(z) voltage','2 @q[ic] current'],['0 time time','1 v(x) voltage','2 v(x) voltage']):
            with self.assertRaises(ValueError):self.parse(self.fixture(table))

    def test_wrong_unit_rejected(self):
        with self.assertRaises(ValueError):self.parse(self.fixture(['0 time time','1 v(x) current','2 @q[ic] current']))

    def test_wrong_counts_complex_and_duplicate_header_rejected(self):
        data=self.fixture()
        for changed in (data.replace(b'Variables: 3',b'Variables: 4'),data.replace(b'Points: 2',b'Points: 3'),data.replace(b'Flags: real',b'Flags: complex'),data.replace(b'Flags: real',b'Flags: real\nFlags: real')):
            with self.assertRaises(ValueError):self.parse(changed)

    def test_truncated_extra_and_second_plot_rejected(self):
        data=self.fixture()
        for changed in (data[:-1],data+b'\0',data+data):
            with self.assertRaises(ValueError):self.parse(changed)

    def test_nonfinite_and_nonmonotonic_clock_rejected(self):
        for values in (np.array([[0,0,0],[0,1,1.]]),np.array([[0,0,0],[1e-6,np.nan,1.]]),np.array([[1e-6,0,0],[2e-6,1,1.]])):
            with self.assertRaises(ValueError):self.parse(self.fixture(values=values))

    def test_bit_gate_keeps_signed_zero_and_low_bit(self):
        a=np.array([[0.,-0.],[1.,2.]]);b=a.copy();self.assertTrue(raw.bits(a,b)['passed'])
        b[0,1]=0.;self.assertFalse(raw.bits(a,b)['passed'])
        b=a.copy();b[1,1]=np.nextafter(2.,3.);self.assertEqual(raw.bits(a,b)['bit_mismatches'],1)

    def test_dual_export_patch_only_changes_export_tail(self):
        r,p=runner.source('nominal500');old=p.with_suffix('.cir').read_bytes()
        deck,m=runner.patch(old,'nominal500',p.with_suffix('.txt').as_posix(),'new.txt','new.raw')
        self.assertEqual(deck.replace(m['export_after'].encode(),m['export_before'].encode(),1).replace(b'wrdata new.txt ',('wrdata '+p.with_suffix('.txt').as_posix()+' ').encode(),1),old)

    def test_long_binary_patch_preserves_electrical_bytes(self):
        r,p=runner.source('nominal500');old=p.with_suffix('.cir').read_bytes()
        deck,m=runner.patch(old,'nominal500',p.with_suffix('.txt').as_posix(),'long.txt','long.raw',True)
        restored=deck.replace(m['export_after'].encode(),m['export_before'].encode(),1)
        for change in reversed(m['temporal_patch']['changes']):restored=restored.replace(change['after'].encode(),change['before'].encode(),1)
        self.assertEqual(restored,old);self.assertFalse(m['electrical_changes'])

if __name__=='__main__':unittest.main()
