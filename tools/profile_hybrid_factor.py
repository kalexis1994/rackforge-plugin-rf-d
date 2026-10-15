"""Profile the rejected direct path before choosing another implementation."""
import base64,json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse,US
from check_hybrid_schur import comparison
def derive():
    from profile_hybrid_direct import derive as current
    sources={n.replace('profiled_direct','factor_control').replace('hybrid_direct_profile_probe','hybrid_factor_profile_probe'):v.replace('profiled_direct','factor_control') for n,v in current().items()}
    name='crates/rf-d-circuit/src/factor_control_solver.rs';s=sources[name]
    s=once(s,'struct Block<const N:usize>{','struct Block<const N:usize>{operations:[usize;2],')
    s=once(s,'Self{scale:[0.;N],','Self{operations:[0;2],scale:[0.;N],')
    s=once(s,'self.lu.perm=std::array::from_fn(|i|i);let mut scale=self.scale;','self.operations=[0;2];self.lu.perm=std::array::from_fn(|i|i);let mut scale=self.scale;')
    s=once(s,'let row=&head[col];let upper=self.border[col];','let row=&head[col];let upper=self.border[col];let active=row[col+1..end].iter().filter(|v|**v!=0.).count();')
    s=once(s,'let factor=current[col]/diagonal;current[col]=factor;','let factor=current[col]/diagonal;current[col]=factor;self.operations[0]+=end-col-1;self.operations[1]+=active;')
    s=once(s,'for p in 0..4{let factor=self.cross[p][col]/diagonal;','self.operations[0]+=4*(end-col-1);self.operations[1]+=4*active;for p in 0..4{let factor=self.cross[p][col]/diagonal;')
    s=once(s,'pub struct Workspace{','pub struct Workspace{pub operations:[usize;2],')
    s=once(s,'Self{profile:[0;6],','Self{operations:[0;2],profile:[0;6],')
    s=once(s,'self.profile[1]+=start.elapsed().as_nanos();Ok(())','self.profile[1]+=start.elapsed().as_nanos();for k in 0..2{self.operations[k]+=self.contour.operations[k]+self.audio.operations[k];}Ok(())')
    sources[name]=s
    name='tools/hybrid_factor_profile_probe.rs';s=sources[name];s=once(s,'    assert_eq!(heap,0);','    writeln!(w,"OPERATIONS,{},{}",workspace.operations[0],workspace.operations[1]).unwrap();\n    assert_eq!(heap,0);');sources[name]=s
    return sources

def main():
    out=ROOT/'evidence/hybrid_factor_profile01.json';assert not out.exists();sources=derive()
    for n,s in sources.items():assert not (ROOT/n).exists();(ROOT/n).write_text(s,encoding='utf8',newline='\n')
    names=['tools/profile_hybrid_factor.py','tools/profile_hybrid_direct.py',*sources,'crates/rf-d-circuit/src/direct_hybrid_solver.rs','crates/rf-d-circuit/src/direct_hybrid_voice.rs','tools/hybrid_direct_probe.rs','evidence/hybrid_direct_native03.json']
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in names},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB));work=ROOT/'tmp/lab-current';assert not list(work.iterdir())
    old=json.loads((ROOT/'evidence/hybrid_direct_native03.json').read_text(encoding='utf8'));assert old['passed'];p=old['profiles'][2]
    seed=work/'seed.bin';seed.write_bytes(unpack(old['projected_seed']));env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code','--cfg','condensed',str(ROOT/'tools/hybrid_factor_profile_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/'profile.exe')];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace');command=[str(work/'profile.exe'),str(seed),str(32*US)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
        r['stdout']=packed(last.stdout);r['stderr']=last.stderr.decode(errors='replace');assert last.returncode==0,r['stderr'];g,_,f=parse(last.stdout);raw=unpack(p['stdout']);og,_,_=parse(raw);r['comparison']=comparison(g,og,last.stdout,raw);r['measurement']=f
        z=next(x for x in last.stdout.decode().splitlines() if x.startswith('PROFILE,'));r['timed_sections_s']=dict(zip(['direct_assembly_validation','factorization','initial_triangular_solve','initial_backward','refinement','newton_full_electrical'],[int(x)/1e9 for x in z.split(',')[1:]]));r['timers_include_four_exact_replays']=True;r['unattributed_includes_line_search_and_failed_solves']=True;r['operations']=list(map(int,next(x for x in last.stdout.decode().splitlines() if x.startswith('OPERATIONS,')).split(',')[1:]));r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_sources']=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names},sort_keys=True).encode());r['failed_command']=command
        if last:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    for p in work.iterdir():assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());write(out,r);print('FACTOR_PROFILE_SECTIONS',r['passed'],r.get('timed_sections_s'),r.get('failure',''),flush=True);assert r['passed']
if __name__=='__main__':main()
