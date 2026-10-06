from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import loudness_board4_circuit as c
import render_loudness_board4 as render


class LoadedNoteListeningTests(unittest.TestCase):
    def raw(self,amplitude=.1):
        s=c.Scenario();t=np.linspace(0,.35,35001)
        raw=np.zeros((len(t),len(s.vectors)+1));raw[:,0]=t
        raw[:,s.vectors.index('v(f4_main_output)')+1]=.2+amplitude*np.sin(2*np.pi*440*t)
        return raw,s

    def test_full_duration_preserves_fixed_gain_and_removes_dc(self):
        raw,s=self.raw();audio,dc=render.adapt(raw,s)
        self.assertEqual(len(audio),16800)
        self.assertAlmostEqual(dc,.2,places=12)
        self.assertAlmostEqual(float(np.max(np.abs(audio[2000:14000]))),.1/8,delta=2e-6)
        self.assertEqual(audio[0],0);self.assertEqual(audio[-1],0)
        self.assertTrue(np.isfinite(audio).all())

    def test_clipping_is_rejected_without_renormalization(self):
        raw,s=self.raw(amplitude=20)
        with self.assertRaises(ValueError):render.adapt(raw,s)


if __name__=='__main__':unittest.main()
