from dataclasses import replace
from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_full_note as note

class LongNoteTests(unittest.TestCase):
    def deck(self,name='nominal500'):
        s=note.short.scenes()[name]
        return b'unchanged electrical branches\nRtest node 0 1000\n'+note.keyboard(s)+note.tran(s)+b'wrdata old.txt '+b' '.join(n.encode() for n in s.vectors)+b'\n.end\n'
    def test_temporal_patch_preserves_all_electrical_bytes(self):
        old=self.deck();new,m=note.patch(old,'nominal500','old.txt','new.txt')
        self.assertIn(b'Rtest node 0 1000\n',new);self.assertEqual(len(m['changes']),3)
        self.assertIn(note.keyboard(note.scenes()['nominal500']),new)
        self.assertIn(note.tran(note.scenes()['nominal500']),new)
        for edit in reversed(m['changes']):new=new.replace(edit['after'].encode(),edit['before'].encode(),1)
        self.assertEqual(old,new)
    def test_duplicate_anchor_rejected(self):
        with self.assertRaises(ValueError):note.patch(self.deck()+note.keyboard(note.short.scenes()['nominal500']),'nominal500','old.txt','new.txt')
    def test_changed_source_anchor_rejected(self):
        with self.assertRaises(ValueError):note.patch(self.deck().replace(b'0.002 0',b'0.003 0'),'nominal500','old.txt','new.txt')
    def test_four_policies_and_fixed_long_events(self):
        ss=note.scenes();self.assertEqual(tuple(ss),tuple(note.short.scenes()))
        for name,s in ss.items():
            old=note.short.scenes()[name]
            self.assertEqual((s.oscillator.duration_s,s.trigger_on_s,s.trigger_off_s),(.35,.01,.2))
            self.assertEqual(s.controls,old.controls);self.assertEqual(s.oscillator.max_step_s,old.oscillator.max_step_s)
            self.assertEqual(s.oscillator.method,old.oscillator.method)
    def fixture(self):
        s=note.scenes()['nominal500'];s=replace(s,board=replace(s.board,oscillator=replace(s.oscillator,max_step_s=1e-5)))
        t=np.linspace(0,.35,35001);a=np.zeros((len(t),len(s.vectors)+1));a[:,0]=t
        a[:,s.vectors.index('v(ramp_c1)')+1]=-3+5*np.mod(440*t,1)
        a[:,s.vectors.index('v(f4_main_output)')+1]=.2+.1*np.sin(2*np.pi*440*t)
        return a,s
    def test_four_windows_use_only_their_own_mean(self):
        a,s=self.fixture();m=note.measurement(a,s)
        self.assertEqual(tuple(m['windows']),tuple(note.WINDOWS))
        self.assertAlmostEqual(m['windows']['held']['output_ac_rms_v'],.1/np.sqrt(2),delta=5e-4)
        self.assertNotAlmostEqual(m['windows']['held']['output_dc_v'],0,places=2)
    def test_partial_note_cannot_fill_windows(self):
        a,s=self.fixture()
        with self.assertRaises(ValueError):note.measurement(a[:-100],s)
    def test_long_pair_reports_all_failures_without_early_exit(self):
        a,s=self.fixture();b=a.copy();b[:,s.vectors.index('v(e2_timing_c2)')+1]=.006
        r=note.contrast(a,b,s,s);self.assertFalse(r['passed']);self.assertFalse(r['gates']['trace'])
        self.assertEqual(len(r['max_trace_difference_v']),5);self.assertEqual(r['grid_points'],70001)
        self.assertFalse(r['phase_alignment']);self.assertEqual(len(r['output_window_rms']),4)

if __name__=='__main__':unittest.main()
