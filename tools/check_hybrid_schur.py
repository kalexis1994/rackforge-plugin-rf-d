"""Condensed trajectories, frozen exterior gates and fresh cost control."""
import base64,json,os,subprocess,time,traceback
import numpy as np
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse,compare,US
from audit_observed_note import trace,absolute
OWN=['tools/prepare_hybrid_schur.py','tools/check_hybrid_schur.py','tools/hybrid_schur_local.rs','tools/hybrid_schur_probe.rs','docs/HYBRID_SCHUR_PROTOCOLO.md','crates/rf-d-circuit/src/hybrid_schur_voice.rs','crates/rf-d-circuit/src/hybrid_schur_solver.rs','crates/rf-d-circuit/src/hybrid_nominal_voice.rs','crates/rf-d-circuit/src/dual_voice_chain.rs','crates/rf-d-circuit/src/hybrid_phase_source.rs','crates/rf-d-circuit/src/hybrid_phase_profile.rs','evidence/hybrid_voice_native05.json','evidence/hybrid_voice_tests01.json']
OWN+=['tools/refine_hybrid_schur.py']
def final_state(data):
    line=next(s for s in data.decode().splitlines() if s.startswith('FINAL,'));v=list(map(float,line.split(',')[1:]));return np.array(v[11:129])+np.array(v[129:247])
def comparison(g,ref,data,reference_data):
    assert g.keys()==ref.keys();a=np.array(list(g.values()));b=np.array(list(ref.values()));e=a-b
    node=float(np.max(abs(e[:,:4])/(20e-6+2e-6*abs(b[:,:4]))));load=float(np.max(abs(e[:,4:])/(2e-9+2e-5*abs(b[:,4:]))))
    rms=float(np.sqrt(np.mean(e[:,0]**2))/np.sqrt(np.mean(b[:,0]**2)));peak=float(max(abs(e[:,0]))/max(abs(b[:,0])));mean=float(abs(np.mean(e[:,0])))
    x=final_state(data);y=final_state(reference_data);last=float(max(abs(x-y)/(20e-6+2e-6*abs(y))))
    result=dict(observations=len(g),max_node_fraction=node,max_load_fraction=load,final_state_fraction=last,j7_rms_relative=rms,j7_peak_relative=peak,j7_mean_error_v=mean)
    assert max(node,load,last)<=1 and rms<=.001 and peak<=.003 and mean<=1e-6,result
    return result
def run():
    work=ROOT/'tmp/lab-current';work.mkdir(exist_ok=True);assert not list(work.iterdir())
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in OWN},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles=[],new_private_sound_inputs=0,new_audio=False,physical_fidelity=False,real_time=False)
    old=json.loads((ROOT/'evidence/hybrid_voice_native05.json').read_text(encoding='utf8'));assert old['passed']
    seed=unpack(old['projected_seed']);seed_path=work/'seed.bin';seed_path.write_bytes(seed);r['projected_seed']=packed(seed)
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    r['private_used_sha256']={};refs=[]
    for maximum in [16777216,8388608]:
        path=ROOT/'references-local/observed-note01'/f'profile-{maximum}.stdout.gz';grid,_,_=trace(path.with_suffix(''))
        refs.append({k:[absolute(v[0])[248],absolute(v[0])[138],absolute(v[0])[171],absolute(v[0])[12],*v[1]] for k,v in grid.items() if k>=40000*US});r['private_used_sha256'][path.relative_to(ROOT).as_posix()]=sha(path)
    flags=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code']
    command=[];last=None;input_data=None;phase='compile';r['compiles']=[]
    try:
        for name,source,cfg in [('local','hybrid_schur_local.rs',[]),('baseline','hybrid_schur_probe.rs',[]),('condensed','hybrid_schur_probe.rs',['--cfg','condensed'])]:
            command=[*flags,*cfg,str(ROOT/'tools'/source),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/(name+'.exe'))]
            last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compiles'].append(dict(mode=name,exit_code=last.returncode));assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='local';rows=[]
        for profile in old['profiles']:
            _,roots,_=parse(unpack(profile['stdout']));rows.extend(','.join(map(str,x)) for x in roots)
        input_data=('\n'.join(rows)+'\n').encode();r['local_input']=packed(input_data);command=[str(work/'local.exe')]
        last=subprocess.run(command,cwd=ROOT,env=env,input=input_data,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        x=list(map(float,last.stdout.decode().strip().split(',')[1:]));r['local']=dict(corrections=int(x[0]),max_direction_fraction=x[1],solves=int(x[2]),refinements=int(x[3]),max_initial_backward=x[4],max_final_backward=x[5],max_nonzeros=int(x[6]),rejections=int(x[7]));print('SCHUR_LOCAL',r['local'],flush=True)
        input_data=None;grids=[]
        for name,maximum in [('baseline',32*US),('condensed',64*US),('condensed',32*US)]:
            phase='profile';command=[str(work/(name+'.exe')),str(seed_path),str(maximum)];start=time.monotonic()
            last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
            item=dict(mode=name,maximum_full_ticks=maximum,exit_code=last.returncode,wall_s=time.monotonic()-start,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));r['profiles'].append(item);assert last.returncode==0,item['stderr']
            grid,roots,final=parse(last.stdout);item['measurement']=final
            i=0 if maximum==64*US else 1;reference_data=unpack(old['profiles'][i]['stdout']);reference_grid,_,_=parse(reference_data)
            item['hybrid_comparison']=comparison(grid,reference_grid,last.stdout,reference_data);item['full_voice_comparison']=compare(grid,refs[i]);
            if name=='condensed':
                z=next(s for s in last.stdout.decode().splitlines() if s.startswith('SOLVER,'));v=list(map(float,z.split(',')[1:]));item['solver']=dict(solves=int(v[0]),refinements=int(v[1]),max_nonzeros=int(v[2]),max_initial_backward=v[3],max_final_backward=v[4]);assert v[4]<=1e-11;grids.append(grid)
            print('SCHUR_PROFILE',name,maximum,final['solve_s'],item['hybrid_comparison'],flush=True)
        phase='refinement';r['refinement']=compare(grids[0],grids[1],True)
        phase='cost';control=r['profiles'][0]['measurement']['solve_s'];candidate=r['profiles'][2]['measurement']['solve_s'];r['cost_ratio']=candidate/control;assert r['cost_ratio']<=.9,r['cost_ratio']
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN if n!='evidence/hybrid_voice_tests01.json'},sort_keys=True).encode()),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,input=input_data,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());return r
def main():
    k=1
    while (ROOT/f'evidence/hybrid_schur_native{k:02d}.json').exists():k+=1
    r=run();write(ROOT/f'evidence/hybrid_schur_native{k:02d}.json',r);print('SCHUR_NATIVE',r['passed'],r.get('cost_ratio'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
