"""Historical direct equations consume the same own DC; adapters do not change state bits."""
import os,subprocess,json,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from run_chain_startup import OWN as BASE,parse
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack
from profile_execution_cost import numerical,final_state
from check_hybrid_schur import comparison
def derive():
    s=(ROOT/'tools/chain_startup_probe.rs').read_text(encoding='utf8')
    s=s.replace('voice::advance(','historical_advance(')
    s+='''
#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"]mod historical;
struct Workspace{workspace:historical::Workspace,p:historical::Parameters}
impl Workspace{fn new()->Self{Self{workspace:historical::Workspace::new(),p:historical::Parameters::new(chain()).unwrap()}}}
fn new_state(s:historical::State)->State{State{high:s.high,low:s.low,optional:s.optional}}
fn new_pair(p:historical::Pair)->Pair{Pair{delta:p.delta.map(new_state),stages:p.stages.map(new_state),residual_a:p.residual_a,correction_v:p.correction_v,iterations:p.iterations}}
fn historical_advance(w:&mut Workspace,p:Parameters,s:&mut State,c:Controls,h:f64)->Result<Accepted,StepError>{
    let mut state=historical::State{high:s.high,low:s.low,optional:s.optional};let mut pp=w.p;pp.time=p.time;let cc=historical::Controls{key:c.key,short:c.short,optional:c.optional};
    let q=historical::advance(&mut w.workspace,pp,&mut state,cc,h)?;
    *s=new_state(state);Ok(Accepted{coarse:new_pair(q.coarse),fine:q.fine.map(new_pair),h:q.h,error:q.error,attempts:q.attempts})
}
'''
    return s
def main():
    source=ROOT/'tools/chain_startup_control.rs';s=derive()
    if source.exists():assert source.read_bytes()==s.encode()
    else:source.write_text(s,encoding='utf8',newline='\n')
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(BASE+['tools/check_chain_startup_control.py','tools/chain_startup_control.rs','crates/rf-d-circuit/src/direct_hybrid_voice.rs','crates/rf-d-circuit/src/direct_hybrid_solver.rs'])
    native='evidence/chain_startup_native02.json';r=dict(passed=False,native=native,native_sha256=sha(ROOT/native),**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),admission_benchmark=False,real_time=False)
    exe=work/'control.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);last=None
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(source),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(exe),'16777216'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);assert last.returncode==0,last.stderr.decode(errors='replace');r['stdout']=packed(last.stdout);d=parse(last.stdout)
        control=json.loads((ROOT/native).read_text(encoding='utf8'));reference=unpack(control['profiles'][1]['stdout']);rd=parse(reference)
        assert numerical(last.stdout)==numerical(reference) and final_state(last.stdout)==final_state(reference) and d['dc']==rd['dc'] and d['events']==rd['events']
        r['comparison']=comparison(d['grid'],rd['grid'],last.stdout,reference);r['measurement']=d['measurement'];r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/chain_startup_control{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/chain_startup_control{k:02d}.json',r);print('CHAIN_STARTUP_CONTROL',r['passed'],r.get('comparison'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
