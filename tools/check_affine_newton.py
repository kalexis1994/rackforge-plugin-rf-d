"""Prepared affine Newton: original directions, physical trajectories and fresh cost."""
import json,os,subprocess,time,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_affine_newton import derive
from affine_evidence import Sources
from check_split_ladder import OWN as BASE_OWN
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse,compare,US
from check_hybrid_schur import comparison
from audit_observed_note import trace,absolute
OWN=list(dict.fromkeys(BASE_OWN+['tools/prepare_affine_newton.py','tools/affine_evidence.py','tools/check_affine_newton.py','tools/affine_newton_local.rs',*derive(),'crates/rf-d-circuit/src/affine_newton_frame.rs','docs/AFFINE_NEWTON_PROTOCOLO.md','tools/split_ladder_probe.rs']))
LOCAL_KEYS=['pairs','stages','directions','physical_entries','invalid_cases','exact_retries','direction_fraction','physical_backward','preparations','physical_solves','reduced_rhs','physical_refinements','max_initial_backward','max_final_backward','reduced_solves','reduced_refinements','reduced_max_final_backward']
AFFINE_KEYS=['preparations','physical_solves','reduced_rhs','physical_refinements','max_nonzeros','max_initial_backward','max_final_backward']
def run():
    work=ROOT/'tmp/lab-current';work.mkdir(exist_ok=True);assert not list(work.iterdir())
    sources=Sources(OWN)
    r=dict(passed=False,numerical_integration_verified=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles=[],new_private_sound_inputs=0,new_audio=False,physical_fidelity=False,real_time=False)
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    old=json.loads((ROOT/'evidence/hybrid_direct_native03.json').read_text(encoding='utf8'));assert old['passed'];previous=[p for p in old['profiles'] if p['mode']=='direct']
    prior=json.loads((ROOT/'evidence/split_ladder_native02.json').read_text(encoding='utf8'));assert prior['numerical_integration_verified'];prior=[p for p in prior['profiles'] if p['mode']=='split']
    seed=unpack(old['projected_seed']);seed_path=work/'seed.bin';seed_path.write_bytes(seed);r['projected_seed']=packed(seed)
    rows=[]
    for p in previous:
        _,roots,_=parse(unpack(p['stdout']));rows.extend(','.join(map(str,row)) for row in roots)
    local_input=('\n'.join(rows)+'\n').encode();r['local_input']=packed(local_input)
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);r['private_used_sha256']={};refs=[]
    for maximum in[16777216,8388608]:
        path=ROOT/'references-local/observed-note01'/f'profile-{maximum}.stdout.gz';g,_,_=trace(path.with_suffix(''));refs.append({k:[absolute(v[0])[248],absolute(v[0])[138],absolute(v[0])[171],absolute(v[0])[12],*v[1]] for k,v in g.items() if k>=40000*US});r['private_used_sha256'][path.relative_to(ROOT).as_posix()]=sha(path)
    flags=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code'];command=[];last=None;stdin=None;phase='compile';r['compiles']=[]
    try:
        for name,source,cfg in[('local','affine_newton_local.rs',['--cfg','laboratory']),('baseline','affine_newton_probe.rs',[]),('previous','split_ladder_probe.rs',['--cfg','condensed']),('affine','affine_newton_probe.rs',['--cfg','condensed'])]:
            command=[*flags,*cfg,str(ROOT/'tools'/source),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/(name+'.exe'))];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compiles'].append(dict(mode=name,exit_code=last.returncode));assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='local';stdin=local_input;command=[str(work/'local.exe')];last=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        values=list(map(float,next(line for line in last.stdout.decode().splitlines() if line.startswith('LOCAL,')).split(',')[1:]));assert len(values)==len(LOCAL_KEYS);r['local']=dict(zip(LOCAL_KEYS,values));r['local_stdout']=packed(last.stdout);print('AFFINE_LOCAL',r['local'],flush=True)
        stdin=None;grids=[]
        for name,maximum in[('baseline',32*US),('previous',32*US),('affine',64*US),('affine',32*US)]:
            phase='profile';command=[str(work/(name+'.exe')),str(seed_path),str(maximum)];start=time.monotonic();last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
            item=dict(mode=name,maximum_full_ticks=maximum,exit_code=last.returncode,wall_s=time.monotonic()-start,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));r['profiles'].append(item);assert last.returncode==0,item['stderr'];grid,roots,final=parse(last.stdout);item['measurement']=final
            i=0 if maximum==64*US else 1;reference_data=unpack(previous[i]['stdout']);reference_grid,_,_=parse(reference_data);item['direct_comparison']=comparison(grid,reference_grid,last.stdout,reference_data);item['full_voice_comparison']=compare(grid,refs[i]);previous_raw=unpack(prior[i]['stdout']);previous_grid,_,_=parse(previous_raw);item['previous_comparison']=comparison(grid,previous_grid,last.stdout,previous_raw)
            v=list(map(float,next(s for s in last.stdout.decode().splitlines() if s.startswith('SOLVER,')).split(',')[1:]));item['solver']=dict(solves=int(v[0]),refinements=int(v[1]),max_nonzeros=int(v[2]),max_initial_backward=v[3],max_final_backward=v[4]);assert v[4]<=1e-11
            if name=='affine':
                v=list(map(float,next(s for s in last.stdout.decode().splitlines() if s.startswith('AFFINE,')).split(',')[1:]));assert len(v)==len(AFFINE_KEYS);item['affine']=dict(zip(AFFINE_KEYS,v));assert item['affine']['max_final_backward']<=1e-11;grids.append(grid)
            print('AFFINE_PROFILE',name,maximum,final['solve_s'],item['direct_comparison'],flush=True)
        phase='refinement';r['refinement']=compare(grids[0],grids[1],True);r['numerical_integration_verified']=True
        phase='cost';r['cost_ratio']=r['profiles'][3]['measurement']['solve_s']/r['profiles'][0]['measurement']['solve_s'];r['previous_cost_ratio']=r['profiles'][3]['measurement']['solve_s']/r['profiles'][1]['measurement']['solve_s'];assert r['cost_ratio']<=.9,r['cost_ratio'];r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());return r
def main():
    k=1
    while (ROOT/f'evidence/affine_newton_native{k:02d}.json').exists():k+=1
    r=run();write(ROOT/f'evidence/affine_newton_native{k:02d}.json',r);print('AFFINE_NATIVE',r['passed'],r.get('cost_ratio'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
