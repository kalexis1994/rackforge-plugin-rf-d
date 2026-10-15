"""Profile the rejected direct path before choosing another implementation."""
import base64,json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse,US
from check_hybrid_schur import comparison
def derive():
    s=(ROOT/'crates/rf-d-circuit/src/direct_hybrid_solver.rs').read_text(encoding='utf8')
    s=once(s,'pub struct Workspace{','pub struct Workspace{pub profile:[u128;6],')
    s=once(s,'Self{contour:Block::new()','Self{profile:[0;6],contour:Block::new()')
    s=once(s,'        self.contour.lu.a=[[0.;108];108];','        let start=std::time::Instant::now();\n        self.contour.lu.a=[[0.;108];108];')
    s=once(s,'self.contour.factor(&mut self.outer.a)?;self.audio.factor(&mut self.outer.a)?;self.outer.factor()', '''self.profile[0]+=start.elapsed().as_nanos();let start=std::time::Instant::now();
        self.contour.factor(&mut self.outer.a)?;self.audio.factor(&mut self.outer.a)?;self.outer.factor()?;
        self.profile[1]+=start.elapsed().as_nanos();Ok(())''')
    s=once(s,'let mut d=self.correction(b)?;let(mut r,mut metric)=self.sparse.residual(&b,&d)?;let initial=metric;', '''let start=std::time::Instant::now();let mut d=self.correction(b)?;self.profile[2]+=start.elapsed().as_nanos();
        let start=std::time::Instant::now();let(mut r,mut metric)=self.sparse.residual(&b,&d)?;let initial=metric;self.profile[3]+=start.elapsed().as_nanos();''')
    s=once(s,'let e=self.correction(r)?;', 'let start=std::time::Instant::now();let e=self.correction(r)?;')
    s=once(s,'let(rr,next)=self.sparse.residual(&b,&d)?;', 'let(rr,next)=self.sparse.residual(&b,&d)?;self.profile[4]+=start.elapsed().as_nanos();')
    v=(ROOT/'crates/rf-d-circuit/src/direct_hybrid_voice.rs').read_text(encoding='utf8').replace('direct_hybrid_solver.rs','profiled_direct_solver.rs')
    v=once(v,'let s=evaluate(d)?;let r=residual(&s);','let start=std::time::Instant::now();let s=evaluate(d)?;w.profile[5]+=start.elapsed().as_nanos();let r=residual(&s);')
    p=(ROOT/'tools/hybrid_direct_probe.rs').read_text(encoding='utf8').replace('direct_hybrid_voice.rs','profiled_direct_voice.rs')
    p=once(p,'    assert_eq!(heap,0);','    {write!(w,"PROFILE").unwrap();for n in workspace.profile{write!(w,",{n}").unwrap();}writeln!(w).unwrap();}\n    assert_eq!(heap,0);')
    return {'crates/rf-d-circuit/src/profiled_direct_solver.rs':s,'crates/rf-d-circuit/src/profiled_direct_voice.rs':v,'tools/hybrid_direct_profile_probe.rs':p}
def main():
    out=ROOT/'evidence/hybrid_direct_profile01.json';assert not out.exists();sources=derive()
    for n,s in sources.items():assert not (ROOT/n).exists();(ROOT/n).write_text(s,encoding='utf8',newline='\n')
    names=['tools/profile_hybrid_direct.py',*sources,'crates/rf-d-circuit/src/direct_hybrid_solver.rs','crates/rf-d-circuit/src/direct_hybrid_voice.rs','tools/hybrid_direct_probe.rs','evidence/hybrid_direct_native02.json']
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in names},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB));work=ROOT/'tmp/lab-current';assert not list(work.iterdir())
    old=json.loads((ROOT/'evidence/hybrid_direct_native02.json').read_text(encoding='utf8'));assert not old['passed'] and old['failed_phase']=='cost';p=old['profiles'][2]
    seed=work/'seed.bin';seed.write_bytes(unpack(old['projected_seed']));env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code','--cfg','condensed',str(ROOT/'tools/hybrid_direct_profile_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/'profile.exe')];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace');command=[str(work/'profile.exe'),str(seed),str(32*US)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
        r['stdout']=packed(last.stdout);r['stderr']=last.stderr.decode(errors='replace');assert last.returncode==0,r['stderr'];g,_,f=parse(last.stdout);raw=unpack(p['stdout']);og,_,_=parse(raw);r['comparison']=comparison(g,og,last.stdout,raw);r['measurement']=f
        z=next(x for x in last.stdout.decode().splitlines() if x.startswith('PROFILE,'));r['timed_sections_s']=dict(zip(['direct_assembly_validation','factorization','initial_triangular_solve','initial_backward','refinement','newton_full_electrical'],[int(x)/1e9 for x in z.split(',')[1:]]));r['timers_include_four_exact_replays']=True;r['unattributed_includes_line_search_and_failed_solves']=True;r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_sources']=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names},sort_keys=True).encode());r['failed_command']=command
        if last:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    for p in work.iterdir():assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());write(out,r);print('DIRECT_PROFILE_SECTIONS',r['passed'],r.get('timed_sections_s'),r.get('failure',''),flush=True);assert r['passed']
if __name__=='__main__':main()
