"""Verify the selected facade and its complete trajectories before adoption."""
import json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_incidence_voice import OWN as BASE
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse,US
from profile_execution_cost import numerical,final_state
from check_hybrid_schur import comparison
OWN=list(dict.fromkeys(BASE+['crates/rf-d-circuit/src/active_nominal_voice.rs','tools/active_nominal_voice_probe.rs','tools/check_incidence_selection.py','docs/INCIDENCE_SELECTION_PROTOCOLO.md','tools/profile_execution_cost.py']))
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(OWN)
    control=json.loads((ROOT/'evidence/incidence_voice_native01.json').read_text(encoding='utf8'));assert control['passed'] and control['cost_ratio']<=.9
    audit=json.loads((ROOT/'evidence/incidence_voice_audit01.json').read_text(encoding='utf8'));assert audit['passed'] and audit['native_sha256']==sha(ROOT/'evidence/incidence_voice_native01.json')
    r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),control_receipt='evidence/incidence_voice_native01.json',control_receipt_sha256=sha(ROOT/'evidence/incidence_voice_native01.json'),audit_receipt_sha256=sha(ROOT/'evidence/incidence_voice_audit01.json'),profiles=[],physical_fidelity=False,real_time=False,new_audio=False)
    seed=work/'seed.bin';seed.write_bytes(unpack(control['projected_seed']));r['projected_seed']=control['projected_seed'];env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);last=None;command=[];phase='compile'
    try:
        for name,source in [('baseline','incidence_voice_probe.rs'),('selected','active_nominal_voice_probe.rs')]:
            command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools'/source),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/(name+'.exe'))]
            last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        for name,maximum,index in [('baseline',32*US,0),('selected',64*US,1),('selected',32*US,2)]:
            phase='trajectory';command=[str(work/(name+'.exe')),str(seed),str(maximum)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);assert last.returncode==0,last.stderr.decode(errors='replace')
            raw=last.stdout;reference=unpack(control['profiles'][index]['stdout']);g,_,f=parse(raw);og,_,_=parse(reference)
            item=dict(mode=name,maximum_full_ticks=maximum,stdout=packed(raw),measurement=f,comparison=comparison(g,og,raw,reference));r['profiles'].append(item)
            assert numerical(raw)==numerical(reference) and final_state(raw)==final_state(reference)
            assert f['exact_replays']==4 and f['atomic_rejections']==5 and f['heap_allocations']==0
            print('INCIDENCE_SELECTED_PROFILE',name,maximum,f['solve_s'],flush=True)
        phase='cost';r['cost_ratio']=r['profiles'][2]['measurement']['solve_s']/r['profiles'][0]['measurement']['solve_s'];assert r['cost_ratio']<=.9,r['cost_ratio'];r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/incidence_voice_selection{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/incidence_voice_selection{k:02d}.json',r);print('INCIDENCE_SELECTION',r['passed'],r.get('cost_ratio'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
