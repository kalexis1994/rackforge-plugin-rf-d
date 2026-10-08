"""Measure circuit-derived startup, preserving every source/build/failure and retry."""
import argparse,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from vco1_newton_reference import ROOT,sha
BASE='3191073143a47f66aaa0a6b4f2627edafad92775'
NEW=['crates/rf-d-circuit/src/vco1_startup.rs','crates/rf-d-circuit/tests/vco1_startup.rs','crates/rf-d-circuit/tests/vco1_startup_no_alloc.rs','docs/VCO1_ARRANQUE_PROTOCOLO.md','tools/vco1_startup_native.py']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 if not 1<=a<=99:raise ValueError('attempt')
 out=ROOT/f'evidence/voice_vco1_startup_native{a:02d}.json';work=ROOT/f'references-local/vco1-startup-native{a:02d}'
 if out.exists() or work.exists():raise ValueError('preserve attempted production')
 qp=ROOT/'evidence/voice_vco1_newton_tests01.json';q=json.loads(qp.read_text(encoding='utf8'))
 if not q['passed'] or q['covered_test_count']!=220:raise ValueError('inherited admission')
 names=set(q['source_sha256'])|set(NEW)|{qp.relative_to(ROOT).as_posix()};before={n:sha(ROOT/n) for n in sorted(names)}
 compiler=json.loads((ROOT/'evidence/voice_vco1_newton_native01.json').read_text(encoding='utf8'))['compiler'];rustc=Path(compiler['path'])
 if sha(rustc)!=compiler['sha256']:raise ValueError('pinned compiler')
 private={n:sha(ROOT/n) for n in ('references-local/datasheets/ti_lm741_lm741.lib',)}
 free=shutil.disk_usage(ROOT).free;report=dict(passed=False,schema='rf-d/vco1-own-startup-production/v1',base_commit=BASE,source_sha256=before,private_input_sha256=private,compiler=compiler,commands=[],unchanged_replays=[],outputs=[],new_spice_processes=0,new_audio=False,resource_passed=free>2*1024**3+64*1024**2,available_free_bytes=free,estimated_bytes=64*1024**2,estimates_are_not_bounds=True)
 def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 write()
 if not report['resource_passed']:return
 work.mkdir();library=work/'librf_d_circuit.rlib';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];start=time.perf_counter()
 commands=[('compile',[str(rustc),'-C','opt-level=2','--edition=2021','--crate-type','lib','--crate-name','rf_d_circuit','crates/rf-d-circuit/src/lib.rs','-o',str(library)])]
 for name in ('vco1_startup','vco1_startup_no_alloc'):
  exe=work/(name+'.exe');commands.extend([('compile',[str(rustc),'-C','opt-level=2','--edition=2021','--test','--crate-name',name,'crates/rf-d-circuit/tests/'+name+'.rs','--extern','rf_d_circuit='+str(library),'-o',str(exe)]),('test',[str(exe),'--nocapture','--test-threads=1'])])
 try:
  for kind,cmd in commands:
   p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=300);report['commands'].append(dict(kind=kind,command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));write()
   if kind=='test' or p.returncode:print('\n'.join(l for l in (p.stdout+p.stderr).splitlines() if not l.startswith(('STARTUP_ROOT,','STARTUP_SEED,'))),flush=True)
   if p.returncode:
    report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in NEW};write();rp=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=300);report['unchanged_replays'].append(dict(command=cmd,exit_code=rp.returncode,stdout=rp.stdout,stderr=rp.stderr,source_sha256={n:sha(ROOT/n) for n in before}));write();raise ValueError('native command rejected')
  report['passed']=True
 except Exception as exc:report['error']=repr(exc)
 report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},compiler_sha256_after=sha(rustc));report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.glob('*') if p.is_file()];report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after'];write();print('own startup:',report['passed'],report.get('error',''),flush=True)
if __name__=='__main__':main()
