"""One lab-only linear refinement variant; original device/state code unchanged."""
import json,shutil
from pathlib import Path
import voice_matrix_build_retry as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/newton-build08'
TREE=WORK/'ngspice-46'

def patched(s):
    once=prior.once
    s=once(s,'#include "ngspice/fteext.h"','#include "ngspice/fteext.h"\n#include "rfdd.h"')
    marker='/* NIiter() - return value is non-zero for convergence failure */'
    # C templates retain literal backslash-n in strings; decode neither C nor JSON.
    function=(ROOT/'tools/voice_refine_function_replay.c').read_text(encoding='utf-8').replace('\\\\n','\\n')
    s=once(s,marker,'#ifdef KLU\n'+function+'\n#endif\n\n'+marker)
    marker='            SMPsolve(ckt->CKTmatrix, ckt->CKTrhs, ckt->CKTrhsSpare);'
    replacement='''#ifdef KLU
            error=RFLinearSolve(ckt);
            if(error) { FREE(OldCKTstate0); return error; }
#else
'''+marker+'\n#endif'
    return once(s,marker,replacement)

def main():
    if WORK.exists():raise ValueError('preserve previous build')
    name='src/maths/ni/niiter.c';s=patched((prior.TREE/name).read_text(encoding='utf-8'))
    WORK.mkdir();shutil.copytree(prior.TREE,TREE)
    shutil.copytree(prior.WORK/'baseline02',WORK/'baseline02');moved={}
    for p in (WORK/'baseline02').rglob('*'):
        if p.is_file() and p.name in ('Makefile','config.status','libtool','makedefs','GNUmakefile'):
            b=p.read_bytes();a=b.replace(b'newton-build06',b'newton-build08')
            if a!=b:
                before=vco.sha(p);p.write_bytes(a)
                moved[p.relative_to(WORK).as_posix()]=dict(before_sha256=before,after_sha256=vco.sha(p))
    (WORK/'bin').mkdir();shutil.copy2(prior.WORK/'bin/observer.exe',WORK/'bin/prior.exe')
    module=WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    if vco.sha(module)!=vco.sha(prior.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'):raise ValueError('module identity')
    (WORK/'init02').mkdir();(WORK/'init02/spinit').write_text('codemodel '+module.as_posix()+'\n',encoding='utf-8',newline='\n')
    p=TREE/name;before=vco.sha(p);p.write_text(s,encoding='utf-8',newline='\n')
    header=TREE/'src/maths/ni/rfdd.h';shutil.copy2(ROOT/'tools/voice_refine_dd.h',header)
    helpers=(Path(__file__),ROOT/'tools/voice_refine_dd.h',ROOT/'tools/voice_refine_function_replay.c')
    report=dict(schema='rf-d/linear-refine-build/v1',patches={name:dict(before_sha256=before,after_sha256=vco.sha(p))},
        added_files={'src/maths/ni/rfdd.h':vco.sha(header)},relocated_generated_files=moved,
        previous_audit_sha256=vco.sha(ROOT/'evidence/voice_matrix_observation01.json'),
        protocol_sha256=vco.sha(ROOT/'docs/NEWTON_REFINAMIENTO_LINEAL_PROTOCOLO.md'),
        helper_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
        solver_changed=True,device_stamps_changed=False,state_update_changed=False,
        corrections=3,environment='RF_D_LINEAR_REFINE=1',scope='all real NIiter solves including DC; same KLU factors and original effective A/b',
        arithmetic_domain='product operands zero or 2^-400<=abs(x)<=2^400; finite sum/intermediates; explicit error outside domain')
    (WORK/'patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('refinement candidate prepared; NI changed; one arithmetic header added',flush=True)

if __name__=='__main__':main()
