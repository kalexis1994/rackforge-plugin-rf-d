"""Time the previous reduced and original direction calls, including exact replays."""
import json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
from affine_evidence import Sources
from check_affine_newton import OWN as BASE
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse
from check_hybrid_schur import comparison
def derive():
    s=(ROOT/'crates/rf-d-circuit/src/split_ladder_voice.rs').read_text(encoding='utf8')
    s=once(s,'pub fn direction(','fn inner_direction(');s=once(s,'pub fn original_direction(','fn inner_original_direction(')
    s+='''
use std::{time::Instant,sync::atomic::{AtomicU64,Ordering}};
static CALLS:[AtomicU64;4]=[const{AtomicU64::new(0)};4];
pub fn call_profile()->[u64;4]{std::array::from_fn(|k|CALLS[k].load(Ordering::Relaxed))}
pub fn direction(w:&mut Workspace,s:&[Stage;2],rhs:[f64;M])->Result<([f64;RM],[f64;M]),StepError>{
    let clock=Instant::now();let r=inner_direction(w,s,rhs);CALLS[0].fetch_add(clock.elapsed().as_nanos()as u64,Ordering::Relaxed);CALLS[2].fetch_add(1,Ordering::Relaxed);r
}
pub fn original_direction(w:&mut Workspace,s:&[Stage;2],rhs:[f64;M])->Result<[f64;M],StepError>{
    let clock=Instant::now();let r=inner_original_direction(w,s,rhs);CALLS[1].fetch_add(clock.elapsed().as_nanos()as u64,Ordering::Relaxed);CALLS[3].fetch_add(1,Ordering::Relaxed);r
}
'''
    p=(ROOT/'tools/split_ladder_probe.rs').read_text(encoding='utf8');p=once(p,'src/split_ladder_voice.rs','src/profiled_affine_predecessor.rs')
    p=once(p,'    assert_eq!(heap,0);','    {write!(w,"CALLPROFILE").unwrap();for n in circuit::call_profile(){write!(w,",{n}").unwrap();}writeln!(w).unwrap();}\n    assert_eq!(heap,0);')
    return {'crates/rf-d-circuit/src/profiled_affine_predecessor.rs':s,'tools/affine_predecessor_probe.rs':p}
def main():
    for n,s in derive().items():
        p=ROOT/n
        if p.exists():assert p.read_bytes()==s.encode(),n
        else:p.write_text(s,encoding='utf8',newline='\n')
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir())
    sources=Sources(BASE+['tools/profile_affine_predecessor.py',*derive()]);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),timing_includes_exact_replays=True,admission_benchmark=False,scope='whole previous reduced direction and original direction calls, including prepare/refine/reconstruct')
    old=json.loads((ROOT/'evidence/split_ladder_native02.json').read_text(encoding='utf8'));assert old['numerical_integration_verified'];r['control_receipt']='evidence/split_ladder_native02.json';r['control_receipt_sha256']=sha(ROOT/r['control_receipt'])
    seed=work/'seed.bin';seed.write_bytes(unpack(old['projected_seed']));env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'profile.exe'
    command=[COMPILER,'--edition=2021','--cfg','condensed','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/affine_predecessor_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(exe),str(seed),'16777216'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);assert last.returncode==0,last.stderr.decode(errors='replace')
        raw=last.stdout;g,_,f=parse(raw);control=unpack(old['profiles'][3]['stdout']);og,_,_=parse(control);r['comparison']=comparison(g,og,raw,control);r['measurement']=f;r['stdout']=packed(raw)
        numerical=lambda b:[s for s in b.splitlines() if s.startswith((b'GRID,',b'ROOT,',b'SOLVER,'))]
        assert numerical(raw)==numerical(control)
        v=list(map(int,next(s for s in raw.decode().splitlines() if s.startswith('CALLPROFILE,')).split(',')[1:]));assert len(v)==4
        r['timed_calls']=dict(reduced_s=v[0]*1e-9,original_s=v[1]*1e-9,reduced_calls=v[2],original_calls=v[3]);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/affine_newton_profile{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/affine_newton_profile{k:02d}.json',r);print('AFFINE_PREVIOUS_PROFILE',r['passed'],r.get('timed_calls'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
