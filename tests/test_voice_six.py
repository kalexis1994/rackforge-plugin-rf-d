import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_six_build as build
import voice_six_runner as runner

class SixTests(unittest.TestCase):
    def test_six_announcement_and_disabled_mode(self):
        self.assertTrue(runner.log_status(runner.ANNOUNCEMENT+'\n',True)['activation_gate_passed'])
        self.assertTrue(runner.log_status('ngspice done\n',False)['activation_gate_passed'])

    def test_three_does_not_identify_six(self):
        self.assertFalse(runner.log_status(runner.ANNOUNCEMENT.replace('six-','three-'),True)['activation_gate_passed'])

    def test_mixed_unknown_announcement_rejected(self):
        log=runner.ANNOUNCEMENT+'\n'+runner.ANNOUNCEMENT.replace('six-','four-')
        self.assertFalse(runner.log_status(log,True)['activation_gate_passed'])

    def test_shadow_or_matrix_observer_rejected(self):
        for record in ('RFSHADOW,final,0,1','RFMATRIX,begin,','RFREFINE,replay,'):
            self.assertFalse(runner.log_status(runner.ANNOUNCEMENT+'\n'+record,True)['activation_gate_passed'])

    def test_disabled_cannot_publish_refinement(self):
        self.assertFalse(runner.log_status(runner.ANNOUNCEMENT,False)['activation_gate_passed'])

    def test_build_changes_only_declared_two_anchors(self):
        s=(build.PRIOR/'ngspice-46'/build.NAME).read_text(encoding='utf-8');p=build.patched(s)
        restored=p.replace('    for(step=0;step<6;step++) {','    for(step=0;step<3;step++) {',1).replace('six-corrections,pair-fma,all-real-NI','three-corrections,pair-fma,all-real-NI',1)
        self.assertEqual(restored,s)

    def test_ambiguous_loop_anchor_rejected(self):
        s=(build.PRIOR/'ngspice-46'/build.NAME).read_text(encoding='utf-8')
        with self.assertRaises(ValueError):build.patched(s+'\n    for(step=0;step<3;step++) {')

if __name__=='__main__':unittest.main()
