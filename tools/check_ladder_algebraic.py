"""Bounded local ladder reconstruction; no new full trajectory or sound inputs."""
import base64,json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_ladder_algebraic import derive
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,parse
OWN=['tools/prepare_ladder_algebraic.py','tools/check_ladder_algebraic.py','tools/ladder_algebraic_local.rs',
     'crates/rf-d-circuit/src/ladder_algebraic.rs',*derive(),'docs/LADDER_ALGEBRAICO_PROTOCOLO.md',
     'crates/rf-d-circuit/src/prepared_audio_stamp.rs','crates/rf-d-circuit/src/prepared_chain_charge.rs',
     'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/hybrid_direct_native03.json',
     'tools/check_hybrid_voice.py','tools/check_vco_phase.py','tools/prepare_dual_chain.py','tools/prepare_hybrid_stamp.py']
KEYS=['stages','solves','fd_columns','maximum_iterations','invalid_cases','invalid_parameters','heap_allocations',
      'dc_fraction','jacobian_fraction','coordinate_error_v','reconstructed_error_v','reaction_error_a',
      'reaction_fd_fraction','reconstruction_fd_fraction','source_fd_fraction','source_conservation_a',
      'source_conservation_s','charge_error_a','mass_error_s','maximum_residual_a','maximum_correction_v',
      'parent_charge_checks','direct_fd_columns','direct_fd_fraction','parent_charge_error_a','parent_mass_error_s',
      'low_cancellation_probes','factor_rhs_fixtures','h_endpoint_checks']
def run():
    work=ROOT/'tmp/lab-current';work.mkdir(exist_ok=True);assert not list(work.iterdir())
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in OWN},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),new_audio=False,new_private_sound_inputs=0,real_time=False,physical_fidelity=False,global_ladder_reduction_admitted=False)
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    previous=json.loads((ROOT/'evidence/hybrid_direct_native03.json').read_text(encoding='utf8'));assert previous['passed']
    rows=[]
    for p in previous['profiles']:
        if p['mode']=='direct':
            _,roots,_=parse(unpack(p['stdout']));rows.extend(','.join(map(str,row)) for row in roots)
    assert len(rows)==24;input_data=('\n'.join(rows)+'\n').encode();r['local_input']=packed(input_data)
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'ladder.exe'
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/ladder_algebraic_local.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    last=None;phase='compile';stdin=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile_exit_code']=last.returncode;assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='local';command=[str(exe)];stdin=input_data
        last=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        values=list(map(float,last.stdout.decode().strip().split(',')[1:]));assert len(values)==len(KEYS)
        integers=set(KEYS[:7]+['parent_charge_checks','direct_fd_columns','low_cancellation_probes','factor_rhs_fixtures','h_endpoint_checks'])
        r['local']={k:int(v) if k in integers else v for k,v in zip(KEYS,values)};r['local_stdout']=packed(last.stdout);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_sources=packed(json.dumps({n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN},sort_keys=True).encode()),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=120);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());return r
def main():
    k=1
    while (ROOT/f'evidence/ladder_algebraic_native{k:02d}.json').exists():k+=1
    r=run();write(ROOT/f'evidence/ladder_algebraic_native{k:02d}.json',r);print('LADDER_LOCAL',r['passed'],r.get('local'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
