"""Passive 48 kHz readout, exact electrical control and independent time refinement."""
import json,math,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from run_chain_startup import OWN as BASE,parse
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack,US
from profile_execution_cost import numerical,final_state
OWN=list(dict.fromkeys(BASE+['crates/rf-d-circuit/src/j7_audio_readout.rs','tools/j7_readout_probe.rs','tools/check_j7_readout.py','docs/J7_READOUT_PROTOCOLO.md']))
def audio(raw):
    rows=[line.split(',') for line in raw.decode().splitlines() if line.startswith('AUDIO,')]
    assert [int(r[1]) for r in rows]==list(range(4801))
    result=[float(r[2]) for r in rows];assert all(math.isfinite(v) for v in result)
    r=next(line for line in raw.decode().splitlines() if line.startswith('READOUT,')).split(',')
    guards=list(map(int,r[1:]));assert guards[0]==guards[1]>=6 and guards[2:]==[0,100000*US]
    return result,guards
def difference(a,b):
    delta=[x-y for x,y in zip(a,b)];assert len(a)==len(b)==4801
    rms=math.sqrt(sum(x*x for x in delta)/len(delta));reference_rms=math.sqrt(sum(x*x for x in b)/len(b));peak=max(map(abs,b))
    result=dict(samples=len(a),rms_error_v=rms,rms_relative=rms/reference_rms,peak_error_v=max(map(abs,delta)),peak_relative=max(map(abs,delta))/peak,mean_error_v=abs(sum(delta)/len(delta)),reference_rms_v=reference_rms,reference_peak_v=peak)
    assert result['rms_relative']<=.001 and result['peak_relative']<=.003 and result['mean_error_v']<=1e-6,result
    return result
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(OWN)
    native='evidence/chain_startup_selected01.json';control=json.loads((ROOT/native).read_text());assert control['passed'];exe=work/'readout.exe'
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    r=dict(passed=False,**sources.fields(),control=native,control_sha256=sha(ROOT/native),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles=[],physical_fidelity=False,real_time=False,bandlimited=False,identity_receipt='evidence/j7_readout_native01.json',identity_receipt_sha256=sha(ROOT/'evidence/j7_readout_native01.json'),electrical_identity=True)
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/j7_readout_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];last=None
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace');samples=[];measurements=[]
        for maximum in [4*US,2*US]:
            command=[str(exe),str(maximum)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
            item=dict(maximum_full_ticks=maximum,exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));r['profiles'].append(item);assert last.returncode==0,item['stderr']
            d=parse(last.stdout);a,g=audio(last.stdout);samples.append(a);measurements.append(d['measurement']);item.update(measurement=d['measurement'],readout_guards=g)
            if maximum==32*US:
                reference=unpack(control['profiles'][1]['stdout']);ref=parse(reference)
                assert numerical(last.stdout)==numerical(reference) and final_state(last.stdout)==final_state(reference) and d['dc']==ref['dc'] and d['events']==ref['events'];r['electrical_identity']=True
            print('J7_PROFILE',maximum,d['measurement'],g,flush=True)
        assert measurements[1]['steps']>measurements[0]['steps'];r['refinement']=difference(*samples)
        command=[COMPILER,'--test','--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/j7_readout_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/'guards.exe')]
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(work/'guards.exe'),'--test-threads=1'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unit_tests']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));assert last.returncode==0,last.stdout.decode(errors='replace')
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/j7_readout_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/j7_readout_native{k:02d}.json',r);print('J7_READOUT',r['passed'],r.get('failure',''),r.get('refinement'),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
