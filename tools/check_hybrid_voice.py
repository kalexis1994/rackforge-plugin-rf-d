"""Bounded hybrid trajectory and reserved complete-voice comparison."""
import base64,gzip,json,os,struct,subprocess,time,traceback
import numpy as np
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from check_vco_phase import COMPILER,LIB
from audit_observed_note import trace,absolute
TICK=125e-9/65536;US=524288
OWN=['tools/prepare_hybrid_voice.py','tools/hybrid_voice_probe.rs','tools/check_hybrid_voice.py','docs/HYBRID_VOZ_PROTOCOLO.md','crates/rf-d-circuit/src/hybrid_nominal_voice.rs','crates/rf-d-circuit/src/dual_voice_chain.rs','crates/rf-d-circuit/src/dual_chain.rs','crates/rf-d-circuit/src/vco_nominal_phase.rs','crates/rf-d-circuit/src/vco_output_port.rs','crates/rf-d-circuit/src/vco_phase_profile.rs','crates/rf-d-circuit/src/dual_contour_loaded.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/observed_note_native01.json','evidence/vco_phase_tests01.json']
OWN+=['tools/prepare_hybrid_profile.py','crates/rf-d-circuit/src/hybrid_phase_source.rs','crates/rf-d-circuit/src/hybrid_phase_profile.rs','evidence/hybrid_voice_profile01.json']

def packed(data):return dict(codec='gzip-base64-v1',raw_sha256=__import__('hashlib').sha256(data).hexdigest(),raw_bytes=len(data),payload_base64=base64.b64encode(gzip.compress(data,mtime=0)).decode())
def unpack(p):
    data=gzip.decompress(base64.b64decode(p['payload_base64']));assert len(data)==p['raw_bytes'] and __import__('hashlib').sha256(data).hexdigest()==p['raw_sha256'];return data
def parse(data):
    grid={};roots=[];final=None
    for line in data.decode().splitlines():
        tag,*z=line.split(',');x=list(map(float,z))
        if tag=='GRID':grid[int(z[0])]=x[1:]
        elif tag=='ROOT':roots.append(x)
        elif tag=='FINAL':final=dict(ticks=int(z[0]),steps=int(z[1]),selected_pairs=int(z[2]),exact_replays=int(z[3]),atomic_rejections=int(z[4]),heap_allocations=int(z[5]),solve_s=x[6],minimum_full_h_s=x[7],max_residual_a=x[8],max_correction_v=x[9],max_error=x[10])
    assert final and final['ticks']==100000*US and final['selected_pairs']==len(roots)==12
    assert len(grid)==481 and min(grid)==40000*US and max(grid)==100000*US
    assert final['heap_allocations']==0 and final['max_residual_a']<=1e-12 and final['max_correction_v']<=2e-9 and final['max_error']<=1
    return grid,roots,final
def compare(grid,ref,refine=False):
    assert grid.keys()==ref.keys();a=np.array(list(grid.values()));b=np.array(list(ref.values()));e=a-b
    rms=float(np.sqrt(np.mean(e[:,0]**2))/np.sqrt(np.mean(b[:,0]**2)));peak=float(max(abs(e[:,0]))/max(abs(b[:,0])));mean=float(abs(np.mean(e[:,0])))
    macro=float(np.max(abs(e[:,1:3])/((.0005 if refine else .002)+(.0001 if refine else .001)*abs(b[:,1:3]))))
    bus=float(np.max(abs(e[:,3])/((.0001 if refine else .0005)+(.0001 if refine else .002)*abs(b[:,3]))))
    load=float(np.max(abs(e[:,4:])/((2e-9 if refine else 20e-9)+(.002 if refine else .01)*abs(b[:,4:]))))
    result=dict(observations=len(a),j7_rms_relative=rms,j7_peak_relative=peak,j7_mean_error_v=mean,j7_max_error_v=float(max(abs(e[:,0]))),contour_fraction=macro,bus_fraction=bus,load_fraction=load,c2_max_error_v=float(max(abs(e[:,1]))),c5_max_error_v=float(max(abs(e[:,2]))))
    assert rms<=(.005 if refine else .03) and peak<=(.015 if refine else .06) and mean<=(5e-6 if refine else 1e-5) and max(macro,bus,load)<=1,result
    return result
def run():
    work=ROOT/'tmp/lab-current';work.mkdir(exist_ok=True);assert not list(work.iterdir())
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in OWN},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),new_private_sound_inputs=0,new_audio=False,physical_fidelity=False,real_time=False,general_cv=False,branch_start_s=.04,branch_end_s=.1,profiles=[])
    assert r['library_sha256']=='9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d'
    native=json.loads((ROOT/'evidence/observed_note_native01.json').read_text(encoding='utf8'));references=[];r['private_used_sha256']={}
    for maximum in [16777216,8388608]:
        path=ROOT/native['output_directory']/f'profile-{maximum}.stdout.gz';g,_,_=trace(path.with_suffix(''));references.append(g);r['private_used_sha256'][path.relative_to(ROOT).as_posix()]=sha(path)
    raw=references[1][40000*US][0];ids=[12 if k==116 else 249 if k==117 else 133+k for k in range(118)]
    seed=struct.pack('<236d',*[raw[k] for k in ids],*[raw[250+k] for k in ids]);seed_path=work/'seed.bin';seed_path.write_bytes(seed)
    r['projected_seed']=packed(seed);r['seed_mapping']='dual(k)=global(133+k), BUS116=12, C10left117=249; HIGH then LOW'
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'probe.exe'
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/hybrid_voice_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    phase='compile';last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile_exit_code']=last.returncode
        assert last.returncode==0,last.stderr.decode(errors='replace')
        grids=[]
        for i,maximum in enumerate([64*US,32*US]):
            phase='profile';command=[str(exe),str(seed_path),str(maximum)];start=time.monotonic()
            last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
            item=dict(maximum_full_ticks=maximum,exit_code=last.returncode,wall_s=time.monotonic()-start,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));r['profiles'].append(item)
            assert last.returncode==0,item['stderr'];grid,roots,final=parse(last.stdout);item['measurement']=final;grids.append(grid)
            ref={k:[absolute(v[0])[248],absolute(v[0])[138],absolute(v[0])[171],absolute(v[0])[12],*v[1]] for k,v in references[i].items() if k>=40000*US}
            item['reserved_comparison']=compare(grid,ref);print('HYBRID_PROFILE',maximum,final,item['reserved_comparison'],flush=True)
        phase='refinement';r['refinement']=compare(grids[0],grids[1],True);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN},sort_keys=True).encode()),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
        r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for item in list(work.iterdir()):assert item.is_file() and item.resolve().parent==work.resolve();item.unlink()
    r['temporary_area_empty']=not list(work.iterdir());return r
def main():
    k=1
    while (ROOT/f'evidence/hybrid_voice_native{k:02d}.json').exists():k+=1
    r=run();write(ROOT/f'evidence/hybrid_voice_native{k:02d}.json',r);print('HYBRID_NATIVE',r['passed'],r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
