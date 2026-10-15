"""Measure both current execution paths without altering their equations."""
import json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_execution_cost import derive
from affine_evidence import Sources
from check_affine_newton import OWN as BASE
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse
from check_hybrid_schur import comparison
OWN=list(dict.fromkeys(BASE+['tools/prepare_execution_cost.py','tools/profile_execution_cost.py','docs/EXECUTION_COST_PROTOCOLO.md',*derive(),'crates/rf-d-circuit/src/direct_hybrid_solver.rs']))
NAMES=['full_evaluation','residual_evaluation','local_kernel','parent_parts','binding_validation','binding_merge','prepare','physical_csr','local_algebra','retained_projection','factor_or_reduced_prepare','solve','correction_or_reduced_solve','physical_backward','unused14','unused15','unused16','unused17','advance']
def numerical(raw):return [s for s in raw.splitlines() if s.startswith((b'GRID,',b'ROOT,',b'SOLVER,',b'AFFINE,'))]
def final_state(raw):return next(s for s in raw.decode().splitlines() if s.startswith('FINAL,')).split(',')[12:]
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(OWN)
    r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),timing_includes_exact_replays=True,admission_benchmark=False,profiles=[],new_audio=False,physical_fidelity=False,real_time=False)
    control=json.loads((ROOT/'evidence/affine_newton_native01.json').read_text(encoding='utf8'));assert control['numerical_integration_verified'];r['control_receipt']='evidence/affine_newton_native01.json';r['control_receipt_sha256']=sha(ROOT/r['control_receipt'])
    seed=work/'seed.bin';seed.write_bytes(unpack(control['projected_seed']));r['projected_seed']=control['projected_seed'];env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);last=None;command=[];phase='compile'
    try:
        for name,cfg,index in [('direct',[],0),('affine',['--cfg','condensed'],3)]:
            exe=work/(name+'.exe');command=[COMPILER,'--edition=2021',*cfg,'-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/execution_cost_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
            phase='compile';last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
            phase='profile';command=[str(exe),str(seed),'16777216'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);assert last.returncode==0,last.stderr.decode(errors='replace')
            raw=last.stdout;g,_,f=parse(raw);reference=unpack(control['profiles'][index]['stdout']);og,_,_=parse(reference)
            item=dict(mode=name,stdout=packed(raw),measurement=f,comparison=comparison(g,og,raw,reference));r['profiles'].append(item)
            assert numerical(raw)==numerical(reference) and final_state(raw)==final_state(reference)
            values=list(map(int,next(s for s in raw.decode().splitlines() if s.startswith('EXECUTION,')).split(',')[1:]));assert len(values)==2*len(NAMES)
            item['timers']={n:dict(ns=values[2*k],calls=values[2*k+1]) for k,n in enumerate(NAMES)}
            print('EXECUTION_PROFILE',name,{n:dict(seconds=x['ns']*1e-9,calls=x['calls']) for n,x in item['timers'].items() if x['calls']},flush=True)
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/execution_cost_profile{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/execution_cost_profile{k:02d}.json',r);print('EXECUTION_COST',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
