"""Full own-started Euler trajectory bank; complete exports, fixed gates and replay."""
import argparse,json,os,re,shutil,subprocess,time
from pathlib import Path
import numpy as np
from vco1_newton_reference import ROOT,sha
from vco1_circuit_probes import observations,comparison,GATES
NAMES=['crates/rf-d-circuit/src/vco1_adaptive.rs','tools/vco1_adaptive_trajectory.rs','tools/vco1_adaptive_cycles.py','docs/VCO1_SUBPASOS_PROTOCOLO.md']
COLS=143
NODES=[43,48,46,54,44,15,35,7,10,21,4,3,39,20]
def metrics(path,ns):
 count=path.stat().st_size//(COLS*8)
 if path.stat().st_size!=count*COLS*8 or count<2:raise ValueError('whole adaptive export')
 raw=np.memmap(path,dtype='<f8',mode='r',shape=(count,COLS))
 for start in range(0,count,8192):
  b=raw[start:start+8192]
  if not np.isfinite(b).all() or np.max(np.abs(b[:,1:99]))>40 or np.max(np.abs(b[:,99:135]))>1 or np.max(b[:,139:141])>1:raise ValueError('finite/domain/Newton gates')
  ticks=b[:,0]/(125e-9/4096)
  if np.max(np.abs(ticks-np.round(ticks)))>2e-6:raise ValueError('integer tick clock')
 steps=np.diff(raw[:,0])
 if raw[0,0]!=0. or abs(raw[-1,0]-.03)>1e-15 or np.min(steps)<125e-9/4096-1e-17 or np.max(steps)>ns*1e-9+1e-17:raise ValueError('complete adaptive step coverage')
 view=np.column_stack([raw[:,0],*[raw[:,1+n] for n in NODES],raw[:,135],raw[:,136]])
 m=observations(view,None)
 return m,dict(rows=count,columns=COLS,minimum_actual_dt_s=float(steps.min()),maximum_actual_dt_s=float(steps.max()),last_time_s=float(raw[-1,0]),max_residual_ratio=float(raw[:,139].max()),max_correction_ratio=float(raw[:,140].max()),max_iterations=int(raw[:,141].max()),max_trials=int(raw[:,142].max()),panel_current_min_a=float(raw[:,138].min()),panel_current_max_a=float(raw[:,138].max()))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 if not 1<=a<=99:raise ValueError('attempt')
 out=ROOT/f'evidence/voice_vco1_adaptive_cycles{a:02d}.json';work=ROOT/f'references-local/vco1-adaptive-cycles{a:02d}'
 if out.exists() or work.exists():raise ValueError('preserve full trajectory attempt')
 parent=json.loads((ROOT/'evidence/voice_vco1_substep_native01.json').read_text(encoding='utf8'))
 before={n:sha(ROOT/n) for n in sorted(set(parent['source_sha256'])|set(NAMES))}
 compiler=parent['compiler'];rustc=Path(compiler['path'])
 if sha(rustc)!=compiler['sha256']:raise ValueError('pinned compiler')
 estimated=sum(round(.03/(ns*1e-9))+1 for ns in (500,250,125))*2*COLS*8
 free=shutil.disk_usage(ROOT).free
 r=dict(schema='rf-d/vco1-own-step-doubling-bank/v1',passed=False,gates=GATES,local_error_v=2e-6,local_error_a=2e-9,maximum_is_accepted_half_step=True,source_sha256=before,compiler=compiler,commands=[],unchanged_replays=[],cases={},comparisons={},outputs=[],new_spice_processes=0,new_audio=False,available_free_bytes=free,estimated_export_bytes=estimated,resource_passed=free>estimated+2*1024**3,startup='circuit-derived, C1=0 explicit source removed before first Euler step',current_definition='Qa/Q10/JFET terminal companion currents include charge; frozen finite Qa/Q10 observation excludes gate current',columns=['time_s']+['x'+str(k) for k in range(134)]+['qa_collector_a','q10_collector_a','jfet_gate_a','panel_source_a','residual_ratio','correction_ratio','iterations','trials'])
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save()
 if not r['resource_passed']:return
 work.mkdir();env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];library=work/'librf_d_circuit.rlib';exe=work/'trajectory.exe';start=time.perf_counter()
 def command(cmd,export=None):
  p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=600);r['commands'].append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));save();print(p.stdout,flush=True)
  if p.returncode:
   if export and export.exists():
    original=export.with_suffix('.failed-original.bin');shutil.copy2(export,original);r['failed_export']=dict(path=original.relative_to(ROOT).as_posix(),sha256=sha(original),bytes=original.stat().st_size)
   r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in NAMES};save()
   rp=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=600);r['unchanged_replays'].append(dict(command=cmd,exit_code=rp.returncode,stdout=rp.stdout,stderr=rp.stderr,source_sha256={n:sha(ROOT/n) for n in before},export_sha256=sha(export) if export and export.exists() else None));save();raise ValueError('trajectory command rejected: '+p.stderr)
 try:
  command([str(rustc),'-C','opt-level=2','--edition=2021','--crate-type','lib','--crate-name','rf_d_circuit','crates/rf-d-circuit/src/lib.rs','-o',str(library)])
  command([str(rustc),'-C','opt-level=2','--edition=2021','tools/vco1_adaptive_trajectory.rs','--extern','rf_d_circuit='+str(library),'-o',str(exe)])
  for pf in (10,100):
   for ns in (500,250,125):
    label=f'c4-{pf}-adaptive{ns}';path=work/(label+'.bin');print('Begin '+label,flush=True);command([str(exe),str(ns),str(pf),str(path),'30'],path)
    m,coverage=metrics(path,ns);r['cases'][label]=dict(c4_pf=pf,dt_ns=ns,measurements=m,coverage=coverage,path=path.relative_to(ROOT).as_posix(),sha256=sha(path));save();print(label,'frequency',m['frequency_hz'],'spread',m['period_spread_relative'],'charge',m['cycle_charge_check']['relative_imbalance'],flush=True)
  for pf in (10,100):r['comparisons'][f'c4-{pf}-fine']=comparison(r['cases'][f'c4-{pf}-adaptive250']['measurements'],r['cases'][f'c4-{pf}-adaptive125']['measurements'])
  for case in r['cases'].values():
   m=case['measurements']
   if m['period_spread_relative']>GATES['period_spread_relative'] or m['cycle_charge_check']['relative_imbalance']>GATES['cycle_charge_relative']:raise ValueError('periodicity/C1 gate')
  for c in r['comparisons'].values():
   if c['frequency_error_cents']>GATES['frequency_refinement_cents'] or max(c['output_extrema_error_v'].values())>GATES['output_extrema_refinement_v']:raise ValueError('fine adaptive refinement gate')
  r['passed']=True
 except Exception as exc:
  r['error']=repr(exc);save()
  if r['cases'] and not r['unchanged_replays']:
   # Replay the same measurement/decision on retained bytes before any repair.
   try:
    repeated={n:metrics(ROOT/c['path'],c['dt_ns'])[0] for n,c in r['cases'].items()}
    r['unchanged_replays'].append(dict(stage='metrics and frozen gates',measurements_identical=all(repeated[n]==c['measurements'] for n,c in r['cases'].items()),source_sha256={n:sha(ROOT/n) for n in before},error=r['error']))
   except Exception as e:r['unchanged_replays'].append(dict(stage='metrics',error=repr(e)))
 r.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},compiler_sha256_after=sha(rustc));r['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()];r['passed']=r['passed'] and before==r['source_sha256_after'];save();print('Step-doubling bank:',r['passed'],r.get('error',''),flush=True)
if __name__=='__main__':main()
