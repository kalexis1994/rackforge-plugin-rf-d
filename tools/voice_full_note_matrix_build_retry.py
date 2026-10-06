"""Relocate the existing read-only matrix observer; keep RFLinearSolve exact."""
import difflib,json,os,shutil,subprocess
from pathlib import Path
import vco1_circuit_reference as vco

ROOT=vco.ROOT;PRIOR=ROOT/'references-local/voice-circuit/newton-build08'
WORK=ROOT/'references-local/voice-circuit/newton-build09';TREE=WORK/'ngspice-46'
NAME='src/maths/ni/niiter.c';PROTOCOL='docs/VOZ_NOTA_LARGA_MATRIZ_PROTOCOLO.md'

def once(s,a,b):
    if s.count(a)!=1:raise ValueError('unique observer anchor required')
    return s.replace(a,b,1)

def patched(s):
    s=once(s,'int RFMatrixTrace = 0;','int RFMatrixTrace = 0;\nstatic unsigned int RFLongMatrixCaptures=0;')
    s=once(s,'                ckt->CKTtime>=0.0022773 && ckt->CKTtime<=0.0022775 &&',
        '                ckt->CKTtime>=0.01594035 && ckt->CKTtime<=0.01594045 &&')
    s=once(s,'                ckt->CKTdelta<=1e-17 && (iterno==100 || iterno==101);',
        '                ckt->CKTdelta<=1e-17 && (iterno==100 || iterno==101) && RFLongMatrixCaptures<16;')
    return once(s,'            if (RFMatrixTrace) {\n                fprintf(stderr,"RFMATRIX,begin,',
        '            if (RFMatrixTrace) {\n                ++RFLongMatrixCaptures;\n                fprintf(stderr,"RFMATRIX,begin,')

def inventory(tree):return {p.relative_to(tree).as_posix():vco.sha(p) for p in sorted(tree.rglob('*')) if p.is_file()}

def main():
    output=ROOT/'evidence/voice_full_note_matrix_build01.json'
    if WORK.exists() or output.exists():raise ValueError('preserve observer preparation')
    original=(PRIOR/'ngspice-46'/NAME).read_text(encoding='utf-8');changed=patched(original)
    # Preparation guard: the arithmetic function is byte-identical.
    def solve(s):return s[s.index('static int RFLinearSolve('):s.index('/* NIiter() -')]
    if solve(original)!=solve(changed):raise ValueError('solve changed while relocating observer')
    size=sum(p.stat().st_size for folder in ('ngspice-46','baseline02') for p in (PRIOR/folder).rglob('*') if p.is_file())
    if shutil.disk_usage(ROOT).free<size+2*1024**3:raise ValueError('observer copy plus margin unavailable')
    WORK.mkdir();shutil.copytree(PRIOR/'ngspice-46',TREE);shutil.copytree(PRIOR/'baseline02',WORK/'baseline02')
    relocated={}
    for p in (WORK/'baseline02').rglob('*'):
        if p.is_file() and p.name in ('Makefile','config.status','libtool','makedefs','GNUmakefile'):
            b=p.read_bytes();a=b.replace(b'newton-build08',b'newton-build09')
            if a!=b:relocated[p.relative_to(WORK).as_posix()]=dict(before_sha256=vco.sha(p));p.write_bytes(a);relocated[p.relative_to(WORK).as_posix()]['after_sha256']=vco.sha(p)
    (TREE/NAME).write_text(changed,encoding='utf-8',newline='\n')
    before=inventory(PRIOR/'ngspice-46');after=inventory(TREE)
    if set(before)!=set(after) or [n for n in before if before[n]!=after[n]]!=[NAME]:raise ValueError('only observer source may change')
    (WORK/'source-inventory.json').write_text(json.dumps(dict(before=before,after=after),indent=2)+'\n',encoding='utf-8',newline='\n')
    (WORK/'bin').mkdir();(WORK/'init02').mkdir()
    module=WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    (WORK/'init02/spinit').write_text('codemodel '+module.as_posix()+'\n',encoding='utf-8',newline='\n')
    compiler=Path('C:/msys64/ucrt64/bin/gcc.exe');env=os.environ.copy();env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    shell='export MSYSTEM=UCRT64; export PATH=/ucrt64/bin:/usr/bin; make -C src/maths/ni -j2 && make -C src ngspice.exe -j2'
    cmd=['C:/msys64/usr/bin/bash.exe','--noprofile','--norc','-c',shell]
    report=dict(schema='rf-d/full-note-matrix-build/v1',source_inventory_sha256=vco.sha(WORK/'source-inventory.json'),source_files=len(before),
        patch=dict(path=NAME,before_sha256=before[NAME],after_sha256=after[NAME],diff=''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),n=2))),
        relocated_generated_files=relocated,prior_build_sha256=vco.sha(PRIOR/'build.json'),copy_bytes=size,
        protocol_sha256=vco.sha(ROOT/PROTOCOL),helper_sha256=vco.sha(Path(__file__)),
        compiler_path=compiler.as_posix(),compiler_sha256=vco.sha(compiler),compiler_version=subprocess.check_output([str(compiler),'--version'],env=env,text=True),
        command=cmd,cflags='-O2 -g -m64',ldflags='-m64',corrections=3,numerical_algorithm_changed=False,
        observer_selection_changed=True,capture_limit=16,window_s=[.01594035,.01594045],device_stamps_changed=False,state_update_changed=False,new_spice_solves=0)
    try:
        with (WORK/'build.log').open('wb') as log:
            p=subprocess.run(cmd,cwd=WORK/'baseline02',env=env,stdout=log,stderr=subprocess.STDOUT);report['exit_code']=p.returncode
        if p.returncode==0:
            shutil.copy2(WORK/'baseline02/src/ngspice.exe',WORK/'bin/observer.exe')
            report['executable_sha256']=vco.sha(WORK/'bin/observer.exe')
    except Exception as e:report['compile_error']=str(e)
    finally:
        report['build_log_sha256']=vco.sha(WORK/'build.log');report['compiler_sha256_after']=vco.sha(compiler)
        report['helper_sha256_after']=vco.sha(Path(__file__))
        (WORK/'build.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if report.get('exit_code')!=0:raise ValueError('observer compilation rejected; preserve sources/log/receipt')
    print('observer compiled; arithmetic unchanged;',len(before),'source files checked',flush=True)

if __name__=='__main__':main()
