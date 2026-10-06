import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_full_note_shadow_trace as shadow
import voice_full_note_shadow_build as build

def log():
    lines=['RFMATRIX,begin,0.01594042,1e-18,100,1,257,2,2,0','RFREFINE,original,0,1','RFREFINE,original,1,1']
    for k in range(6):
        tag='RFREFINE' if k<3 else 'RFSHADOW'
        for j in range(2):lines.extend([f'{tag},r,{k},{j},0,0',f'{tag},correction,{k},{j},0,1,0'])
    return '\n'.join(lines+['RFSHADOW,final,0,1','RFSHADOW,final,1,1','RFREFINE,final,0,1','RFREFINE,final,1,1','RFMATRIX,end'])

def system():return dict(n=2,nodes={0:dict(name='v',type=3,unknown_unit='V',b=1.),1:dict(name='i',type=4,unknown_unit='A',b=1.)},entries={(0,0):1.,(1,1):1.},time_s=.01594042,h_s=1e-18,iteration=100)

class ShadowTests(unittest.TestCase):
    def test_six_complete_steps_same_precise_system(self):
        d=shadow.parse(log())[0]
        self.assertEqual(len(d['correction']),6)
        self.assertTrue(shadow.compare_six(system(),d,dict(rows=[dict(precise='1'),dict(precise='1')]))['passed'])

    def test_missing_scratch_residual_rejected(self):
        with self.assertRaises(ValueError):shadow.parse(log().replace('RFSHADOW,r,4,0,0,0\n',''))

    def test_scratch_cannot_overwrite_original_step(self):
        with self.assertRaises(ValueError):shadow.parse(log().replace('RFSHADOW,r,3,','RFSHADOW,r,2,'))

    def test_sixth_residual_requires_exact_arithmetic(self):
        d=shadow.parse(log().replace('RFSHADOW,r,5,0,0,0','RFSHADOW,r,5,0,1,0'))[0]
        with self.assertRaises(ValueError):shadow.compare_six(system(),d,dict(rows=[dict(precise='1'),dict(precise='1')]))

    def test_wrong_compensated_update_rejected(self):
        d=shadow.parse(log().replace('RFSHADOW,correction,4,0,0,1,0','RFSHADOW,correction,4,0,1,1,0'))[0]
        with self.assertRaises(ValueError):shadow.compare_six(system(),d,dict(rows=[dict(precise='1'),dict(precise='1')]))

    def test_patch_restores_original_pairs_before_publication(self):
        s=(build.PRIOR/'ngspice-46'/build.NAME).read_text(encoding='utf-8');changed=build.patched(s)
        a=s.index('static int RFLinearSolve(');b=s.index('/* NIiter() -')
        c=changed.index('/* NIiter() -')
        self.assertEqual(s[:a],changed[:a]);self.assertEqual(s[b:],changed[c:])
        self.assertLess(changed.index('memcpy(x,saved,n*sizeof(RFDD))'),changed.index('double published=x[c].hi+x[c].lo;'))

if __name__=='__main__':unittest.main()
