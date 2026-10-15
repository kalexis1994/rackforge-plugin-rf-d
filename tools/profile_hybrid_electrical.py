"""Separate electrical graph costs in the admitted functional direct voice."""
import base64,json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse,US
from check_hybrid_schur import comparison
def derive():
    g=(ROOT/'crates/rf-d-circuit/src/prepared_voice_chain.rs').read_text(encoding='utf8')
    g+='''
std::thread_local!{static TIMINGS:std::cell::Cell<[u128;10]>=const{std::cell::Cell::new([0;10])};}
fn timing(k:usize,n:u128){TIMINGS.with(|x|{let mut a=x.get();a[k]+=n;x.set(a);});}
pub fn profile()->[u128;10]{TIMINGS.with(|x|x.get())}
'''
    g=once(g,'    if !old.valid()', '    let start=std::time::Instant::now();let offset=if FULL{0}else{4};timing(if FULL{8}else{9},1);\n    if !old.valid()')
    g=once(g,'    let audio=chain_charge::', '    timing(offset,start.elapsed().as_nanos());let start=std::time::Instant::now();\n    let audio=chain_charge::')
    g=once(g,'    let dual=contour::', '    timing(offset+1,start.elapsed().as_nanos());let start=std::time::Instant::now();\n    let dual=contour::')
    g=once(g,'    let mut s=Parts{', '    timing(offset+2,start.elapsed().as_nanos());let start=std::time::Instant::now();\n    let mut s=Parts{')
    g=once(g,'    Ok(s)\n}', '    timing(offset+3,start.elapsed().as_nanos());\n    Ok(s)\n}')
    v=(ROOT/'crates/rf-d-circuit/src/direct_hybrid_voice.rs').read_text(encoding='utf8').replace('prepared_voice_chain.rs','electrical_profile_graph.rs')
    v+='\npub fn profile()->[u128;10]{graph::profile()}\n'
    p=(ROOT/'tools/hybrid_direct_probe.rs').read_text(encoding='utf8').replace('direct_hybrid_voice.rs','electrical_profile_voice.rs')
    p=once(p,'    assert_eq!(heap,0);','    {write!(w,"ELECTRICAL").unwrap();for n in circuit::profile(){write!(w,",{n}").unwrap();}writeln!(w).unwrap();}\n    assert_eq!(heap,0);')
    return {'crates/rf-d-circuit/src/electrical_profile_graph.rs':g,'crates/rf-d-circuit/src/electrical_profile_voice.rs':v,'tools/hybrid_electrical_profile_probe.rs':p}
def main():
    out=ROOT/'evidence/hybrid_electrical_profile01.json';assert not out.exists();sources=derive();assert not any((ROOT/n).exists() for n in sources)
    for n,s in sources.items():(ROOT/n).write_text(s,encoding='utf8',newline='\n')
    names=['tools/profile_hybrid_electrical.py',*sources,'crates/rf-d-circuit/src/direct_hybrid_solver.rs','crates/rf-d-circuit/src/direct_hybrid_voice.rs','crates/rf-d-circuit/src/prepared_voice_chain.rs','crates/rf-d-circuit/src/prepared_chain_charge.rs','crates/rf-d-circuit/src/prepared_contour_residual.rs','evidence/hybrid_direct_native03.json']
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in names},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB));work=ROOT/'tmp/lab-current';assert not list(work.iterdir())
    old=json.loads((ROOT/'evidence/hybrid_direct_native03.json').read_text(encoding='utf8'));assert old['passed'];p=old['profiles'][2]
    seed=work/'seed.bin';seed.write_bytes(unpack(old['projected_seed']));env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code','--cfg','condensed',str(ROOT/'tools/hybrid_electrical_profile_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/'profile.exe')];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace');command=[str(work/'profile.exe'),str(seed),str(32*US)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
        r['stdout']=packed(last.stdout);r['stderr']=last.stderr.decode(errors='replace');assert last.returncode==0,r['stderr'];g,_,f=parse(last.stdout);raw=unpack(p['stdout']);og,_,_=parse(raw);r['comparison']=comparison(g,og,last.stdout,raw);r['measurement']=f
        z=next(x for x in last.stdout.decode().splitlines() if x.startswith('ELECTRICAL,'));x=list(map(int,z.split(',')[1:]));r['timed_sections_s']=dict(zip(['full_validation_projection','full_audio','full_contour','full_transfer','residual_validation_projection','residual_audio','residual_contour','residual_transfer'],[v/1e9 for v in x[:8]]));r['full_calls']=x[8];r['residual_calls']=x[9];r['timers_include_four_exact_replays']=True;r['instrumented_not_cost_admission']=True;r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_sources']=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names},sort_keys=True).encode());r['failed_command']=command
        if last:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    for p in work.iterdir():assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());write(out,r);print('ELECTRICAL_PROFILE',r['passed'],r.get('timed_sections_s'),r.get('failure',''),flush=True);assert r['passed']
if __name__=='__main__':main()
