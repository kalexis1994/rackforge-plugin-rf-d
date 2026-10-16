"""Cooperative producer: real circuit quotas/backpressure with frozen prefix controls."""
import hashlib,json,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_long_note_aa import arrays
from check_stream_output import OWN as BASE,parse as stream_parse
from check_vco_phase import COMPILER,LIB
OWN=list(dict.fromkeys(BASE+['tools/check_offline_producer.py','tools/offline_producer_probe.rs','crates/rf-d-circuit/src/nominal_offline_producer.rs','docs/OFFLINE_PRODUCER_PROTOCOLO.md']))
CONTROLS=['evidence/long_note_aa_native01.json','evidence/stream_output_native01.json']

def inputs():
    import struct
    long,stream=[json.loads((ROOT/n).read_text()) for n in CONTROLS];assert long['passed'] and stream['passed']
    _,a,_,_=arrays(unpack(long['profiles'][0]['stdout']));s=stream_parse(unpack(stream['stdout']))['state']
    return {'raw':a['RAW'][:3841].astype('<f8').tobytes(),'expected':a['AA8'][:433].astype('<f8').tobytes(),'state':struct.pack('<236d',*s)}

def parse(raw):
    profiles=[];sizes=None
    for line in raw.decode().splitlines():
        z=line.split(',')
        if z[0]=='PROFILE':
            assert len(z)==20,z
            d=dict(zip(['mode','calls','frames','blocked','zero_quota_calls','resume_branches','heap','ticks','invocations','steps','consumed','produced','control_pairs'],map(int,z[1:14])))
            d.update(first_frame_at_key=z[14]=='true',pending_across_key=z[15]=='true',minimum_full_s=float(z[16]),max_residual_a=float(z[17]),max_correction_v=float(z[18]),max_estimator=float(z[19]));profiles.append(d)
        elif z[0]=='SIZES':sizes=list(map(int,z[1:]))
    assert [d['mode'] for d in profiles]==[0,1,2]
    for d in profiles:
        assert d['calls']>0 and d['frames']==433 and d['blocked']>=2 and d['zero_quota_calls']>=2 and d['resume_branches']==d['blocked'] and d['heap']==0
        assert [d[k] for k in ['ticks','invocations','steps','consumed','produced']]==[10000*524288,5170,5170,3841,433]
    d=profiles[0];assert d['control_pairs']==5170 and d['first_frame_at_key'] and d['pending_across_key'];assert 0<d['minimum_full_s']<=2e-6 and d['max_residual_a']<=1e-12 and d['max_correction_v']<=2e-9 and d['max_estimator']<=1
    assert all(d['control_pairs']==0 for d in profiles[1:]);assert sizes and sizes[0]<=48*1024 and sizes[1]>0 and sizes[2]>0
    return dict(profiles=profiles,sizes=sizes)

def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(OWN);blobs=inputs();files=[]
    for n,b in blobs.items():p=work/(n+'.bin');p.write_bytes(b);files.append(str(p))
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'producer.exe'
    r=dict(passed=False,**sources.fields(),controls={n:sha(ROOT/n) for n in CONTROLS},input_images={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in blobs.items()},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),real_time=False,physical_fidelity=False,new_audio=False,new_original_equation_rows=0)
    flags=['--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/offline_producer_probe.rs'),'--extern','rf_d_circuit='+str(LIB)];phase='compile';last=None;command=[COMPILER,'--test',*flags,'-o',str(work/'guards.exe')]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='unit';command=[str(work/'guards.exe'),'producer::tests::','--test-threads=1'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unit_tests']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));assert last.returncode==0,last.stdout.decode(errors='replace')
        phase='compile';command=[COMPILER,*flags,'-C','strip=symbols','-o',str(exe)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='native';command=[str(exe),*files];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['stdout']=packed(last.stdout);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='parse';r['measurements']=parse(last.stdout);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command)
        if phase=='parse':
            try:parse(last.stdout);r['unchanged_replay']='unexpected pass'
            except Exception:r['unchanged_replay']=traceback.format_exc()
        else:
            if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
            retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while(ROOT/f'evidence/offline_producer_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/offline_producer_native{k:02d}.json',r);print('OFFLINE_PRODUCER',r['passed'],r.get('measurements'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
