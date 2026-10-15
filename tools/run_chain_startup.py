"""Own cold DC and attack; preserve any incomplete trajectory without weakening gates."""
import json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_incidence_selection import OWN as BASE
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,compare,US
OWN=list(dict.fromkeys(BASE+['tools/run_chain_startup.py','tools/chain_startup_probe.rs','crates/rf-d-circuit/src/nominal_chain_startup.rs','docs/CHAIN_STARTUP_PROTOCOLO.md','crates/rf-d-circuit/src/circuit66.rs','tools/loudness_contour_reference.py','tools/c5_trigger_reference.py']))
def parse(raw,complete=True):
    grid={};roots=[];dc=[];events=[];final=None
    for line in raw.decode().splitlines():
        tag,*z=line.split(',');x=list(map(float,z))
        if tag=='GRID':grid[int(z[0])]=x[1:]
        elif tag=='ROOT':assert len(x)==1185;roots.append(x)
        elif tag=='DC':assert len(x)==240;dc.append(dict(mode=int(z[0]),iterations=int(z[1]),residual_a=x[2],correction_v=x[3],state=x[4:]))
        elif tag=='EVENT':events.append(x)
        elif tag=='FINAL':final=dict(ticks=int(z[0]),steps=int(z[1]),selected_pairs=int(z[2]),exact_replays=int(z[3]),atomic_rejections=int(z[4]),heap_allocations=int(z[5]),solve_s=x[6],minimum_full_h_s=x[7],max_residual_a=x[8],max_correction_v=x[9],max_error=x[10])
    assert len(dc)==2 and all(d['residual_a']<=1e-12 and d['correction_v']<=2e-9 for d in dc)
    if complete:
        assert final and final['ticks']==100000*US and len(grid)==801 and len(roots)==final['selected_pairs']==18 and final['exact_replays']==6 and final['atomic_rejections']==5 and final['heap_allocations']==0
        assert final['max_residual_a']<=1e-12 and final['max_correction_v']<=2e-9 and final['max_error']<=1
        assert [int(e[0]) for e in events]==[1000*US,75000*US]
    return dict(grid=grid,roots=roots,dc=dc,events=events,measurement=final)
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(OWN)
    r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles=[],new_private_sound_inputs=0,new_audio=False,physical_fidelity=False,real_time=False,uses_40ms_projected_seed=False)
    exe=work/'startup.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);last=None;phase='compile'
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/chain_startup_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        grids=[]
        for maximum in [64*US,32*US]:
            phase='trajectory';command=[str(exe),str(maximum)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
            item=dict(maximum_full_ticks=maximum,exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));r['profiles'].append(item);assert last.returncode==0,item['stderr'];data=parse(last.stdout);item['measurement']=data['measurement'];item['dc']=data['dc'];grids.append(data['grid']);print('CHAIN_STARTUP_PROFILE',maximum,item['measurement'],flush=True)
        phase='refinement';r['refinement']=compare(grids[0],grids[1],True);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/chain_startup_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/chain_startup_native{k:02d}.json',r);print('CHAIN_STARTUP',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
