"""Two-stage nonlinear ladder reduction, physical trajectory and fresh cost."""
import base64,json,os,subprocess,time,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_split_ladder import derive
from check_ladder_voice import OWN as BASE_OWN
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse,compare,US
from check_hybrid_schur import comparison
from audit_observed_note import trace,absolute
OWN=list(dict.fromkeys(BASE_OWN+['tools/prepare_split_ladder.py','tools/check_split_ladder.py','tools/split_ladder_local.rs',*derive(),'crates/rf-d-circuit/src/split_ladder_binding.rs','docs/SPLIT_LADDER_PROTOCOLO.md','evidence/ladder_voice_native01.json']))
SPLIT_KEYS=['physical_dc_error_a','physical_j_error_s','reduced_j_fraction','maximum_transfer_offset_v','kernel_seeds','kernel_error_v','transfer_invalid_cases','full_residual_checks','congruence_entries','legal_parent_edges']
LOCAL_KEYS=['pairs','stages','directions','fd_columns','invalid_cases','reconstructed_error_v','original_residual_a','direction_fraction','fd_fraction','charge_error_a','solves','refinements','max_initial_backward','max_final_backward','max_nonzeros']
def run():
    work=ROOT/'tmp/lab-current';work.mkdir(exist_ok=True);assert not list(work.iterdir())
    r=dict(passed=False,numerical_integration_verified=False,source_sha256={n:sha(ROOT/n) for n in OWN},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles=[],new_private_sound_inputs=0,new_audio=False,physical_fidelity=False,real_time=False)
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    old=json.loads((ROOT/'evidence/hybrid_direct_native03.json').read_text(encoding='utf8'));assert old['passed'];previous=[p for p in old['profiles'] if p['mode']=='direct'];integrated=json.loads((ROOT/'evidence/ladder_voice_native01.json').read_text(encoding='utf8'));assert integrated['numerical_integration_verified'];prior=[p for p in integrated['profiles'] if p['mode']=='ladder']
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
        for name,source,cfg in[('local','split_ladder_local.rs',['--cfg','laboratory']),('baseline','split_ladder_probe.rs',[]),('previous','ladder_voice_probe.rs',['--cfg','condensed']),('split','split_ladder_probe.rs',['--cfg','condensed'])]:
            command=[*flags,*cfg,str(ROOT/'tools'/source),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/(name+'.exe'))];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compiles'].append(dict(mode=name,exit_code=last.returncode));assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='local';stdin=local_input;command=[str(work/'local.exe')];last=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        lines=last.stdout.decode().splitlines();x=list(map(float,next(line for line in lines if line.startswith('LOCAL,')).split(',')[1:]));assert len(x)==len(LOCAL_KEYS);r['local']=dict(zip(LOCAL_KEYS,x));r['local_stdout']=packed(last.stdout)
        x=list(map(float,next(line for line in lines if line.startswith('SPLIT,')).split(',')[1:]));assert len(x)==len(SPLIT_KEYS);r['split']=dict(zip(SPLIT_KEYS,x));print('SPLIT_LOCAL',r['local'],r['split'],flush=True)
        stdin=None;grids=[]
        for name,maximum in[('baseline',32*US),('previous',32*US),('split',64*US),('split',32*US)]:
            phase='profile';command=[str(work/(name+'.exe')),str(seed_path),str(maximum)];start=time.monotonic();last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
            item=dict(mode=name,maximum_full_ticks=maximum,exit_code=last.returncode,wall_s=time.monotonic()-start,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));r['profiles'].append(item);assert last.returncode==0,item['stderr'];grid,roots,final=parse(last.stdout);item['measurement']=final
            i=0 if maximum==64*US else 1;reference_data=unpack(previous[i]['stdout']);reference_grid,_,_=parse(reference_data);item['direct_comparison']=comparison(grid,reference_grid,last.stdout,reference_data);item['full_voice_comparison']=compare(grid,refs[i]);previous_raw=unpack(prior[i]['stdout']);previous_grid,_,_=parse(previous_raw);item['previous_comparison']=comparison(grid,previous_grid,last.stdout,previous_raw)
            z=next(s for s in last.stdout.decode().splitlines() if s.startswith('SOLVER,'));v=list(map(float,z.split(',')[1:]));item['solver']=dict(solves=int(v[0]),refinements=int(v[1]),max_nonzeros=int(v[2]),max_initial_backward=v[3],max_final_backward=v[4]);assert v[4]<=1e-11
            if name=='split':grids.append(grid)
            print('SPLIT_PROFILE',name,maximum,final['solve_s'],item['direct_comparison'],flush=True)
        phase='refinement';r['refinement']=compare(grids[0],grids[1],True);r['numerical_integration_verified']=True
        phase='cost';r['cost_ratio']=r['profiles'][3]['measurement']['solve_s']/r['profiles'][0]['measurement']['solve_s'];r['previous_cost_ratio']=r['profiles'][3]['measurement']['solve_s']/r['profiles'][1]['measurement']['solve_s'];assert r['cost_ratio']<=.9,r['cost_ratio'];r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN},sort_keys=True).encode()),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());return r
def main():
    k=1
    while (ROOT/f'evidence/split_ladder_native{k:02d}.json').exists():k+=1
    r=run();write(ROOT/f'evidence/split_ladder_native{k:02d}.json',r);print('SPLIT_NATIVE',r['passed'],r.get('cost_ratio'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
