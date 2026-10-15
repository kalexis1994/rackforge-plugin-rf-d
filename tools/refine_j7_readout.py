"""Reuse the archived 2 us run and execute only the missing 1 us reference."""
import json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_j7_readout import OWN,audio,difference
from check_hybrid_voice import packed,unpack,US
from check_vco_phase import COMPILER,LIB
from run_chain_startup import parse
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());parent='evidence/j7_readout_native02.json';previous=json.loads((ROOT/parent).read_text());assert not previous['passed']
    # Electrical model and production readout must be unchanged before reuse.
    for n,data in recover(previous).items():
        if n.startswith('crates/'):assert (ROOT/n).read_bytes()==data,n
    first=previous['profiles'][1];assert first['maximum_full_ticks']==2*US and first['exit_code']==0;parse(unpack(first['stdout']))
    sources=Sources(OWN+['tools/refine_j7_readout.py']);exe=work/'readout.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    r=dict(passed=False,**sources.fields(),control=previous['control'],control_sha256=previous['control_sha256'],identity_receipt=previous['identity_receipt'],identity_receipt_sha256=previous['identity_receipt_sha256'],electrical_identity=True,inherited_profile_receipt=parent,inherited_profile_receipt_sha256=sha(ROOT/parent),new_trajectories=1,compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles=[first],real_time=False,physical_fidelity=False,bandlimited=False)
    flags=['--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/j7_readout_probe.rs'),'--extern','rf_d_circuit='+str(LIB)]
    command=[COMPILER,'--test',*flags,'-o',str(work/'guards.exe')];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(work/'guards.exe'),'--test-threads=1'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unit_tests']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));assert last.returncode==0,last.stdout.decode(errors='replace')
        command=[COMPILER,*flags,'-C','strip=symbols','-o',str(exe)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(exe),str(US)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
        item=dict(maximum_full_ticks=US,exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));r['profiles'].append(item);assert last.returncode==0,item['stderr'];d=parse(last.stdout);a,g=audio(last.stdout);item.update(measurement=d['measurement'],readout_guards=g);print('J7_FINE_REFERENCE',d['measurement'],g,flush=True)
        assert d['measurement']['steps']>first['measurement']['steps'];r['refinement']=difference(audio(unpack(first['stdout']))[0],a);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/j7_readout_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/j7_readout_native{k:02d}.json',r);print('J7_REFINED_READOUT',r['passed'],r.get('failure',''),r.get('refinement'),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
