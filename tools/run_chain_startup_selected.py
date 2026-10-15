"""Run the self-contained cold-start API and prove identity with the audited prototype."""
import json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from run_chain_startup import OWN as BASE,parse
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,compare,US
from profile_execution_cost import numerical,final_state
def derive():
    s=(ROOT/'tools/chain_startup_probe.rs').read_text(encoding='utf8');a=s.index('fn seed(');b=s.index('fn vals(',a)
    s=s[:a]+'fn seed(mode:usize)->Result<State,StepError>{startup::numerical_guess(chain(),mode)}\n'+s[b:]
    old='let r=initialize(p,guess,100).map_err(|e|format!("DC mode={mode}:{e:?}"))?;';assert s.count(old)==1
    return s.replace(old,'let r=(if mode==0{startup::cold_start(chain())}else{initialize(p,guess,100)}).map_err(|e|format!("DC mode={mode}:{e:?}"))?;',1)
def main():
    path=ROOT/'tools/chain_startup_selected.rs';s=derive()
    if path.exists():assert path.read_bytes()==s.encode()
    else:path.write_text(s,encoding='utf8',newline='\n')
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(BASE+['tools/run_chain_startup_selected.py','tools/chain_startup_selected.rs','tools/profile_execution_cost.py'])
    native='evidence/chain_startup_native02.json';control=json.loads((ROOT/native).read_text());assert control['passed'];r=dict(passed=False,native=native,native_sha256=sha(ROOT/native),**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles=[],uses_40ms_projected_seed=False,self_contained_cold_start=True,physical_fidelity=False,real_time=False)
    exe=work/'selected.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);last=None
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(path),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace');grids=[]
        for i,maximum in enumerate([64*US,32*US]):
            command=[str(exe),str(maximum)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);assert last.returncode==0,last.stderr.decode(errors='replace');d=parse(last.stdout);reference=unpack(control['profiles'][i]['stdout']);other=parse(reference)
            assert numerical(last.stdout)==numerical(reference) and final_state(last.stdout)==final_state(reference) and d['dc']==other['dc'] and d['events']==other['events']
            item=dict(maximum_full_ticks=maximum,stdout=packed(last.stdout),measurement=d['measurement'],dc=d['dc']);r['profiles'].append(item);grids.append(d['grid']);print('SELF_CONTAINED_STARTUP',maximum,d['measurement'],flush=True)
        r['refinement']=compare(grids[0],grids[1],True);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/chain_startup_selected{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/chain_startup_selected{k:02d}.json',r);print('CHAIN_STARTUP_SELECTED',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
