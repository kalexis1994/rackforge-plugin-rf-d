"""Bounded streaming readout: archived whole-note equivalence and real circuit prefix."""
import hashlib,json,os,struct,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_long_note_aa import OWN as BASE,arrays
from check_vco_phase import COMPILER,LIB
OWN=list(dict.fromkeys(BASE+['tools/check_stream_output.py','tools/stream_output_probe.rs','crates/rf-d-circuit/src/j7_stream_output.rs','docs/STREAM_OUTPUT_PROTOCOLO.md']))
def parse(raw):
    replays=[];live=None;sizes=None;state=None
    for line in raw.decode().splitlines():
        z=line.split(',')
        if z[0]=='REPLAY':replays.append(list(map(int,z[1:])))
        elif z[0]=='LIVE':live=list(map(float,z[1:]))
        elif z[0]=='SIZES':sizes=list(map(int,z[1:]))
        elif z[0]=='STATE':state=list(map(float,z[1:]))
    assert len(replays)==6 and [(x[0],x[1]) for x in replays]==[(p,m) for p in range(2) for m in range(3)]
    assert all(x[2]>0 and x[3]>=2 and x[4]>=5 and x[6]==0 and x[7:]==[115585,14401] for x in replays)
    assert all(x[5]>0 for x in replays if x[1]==1)
    assert len(live)==12 and live[0]==10000*524288 and live[2:4]==[433,3841] and live[4]>=3 and live[5]==3 and live[6]==live[4] and live[7]==0
    assert live[8]>0 and live[9]<=1e-12 and live[10]<=2e-9 and live[11]<=1
    assert sizes[0]<=12*1024 and sizes[1]<=16*1024 and sizes[2]>sizes[1] and len(state)==236
    return dict(replays=replays,live=live,sizes=sizes,state=state)
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(OWN)
    control='evidence/long_note_aa_native01.json';prior=json.loads((ROOT/control).read_text());assert prior['passed'];files=[];inputs={}
    for index,p in enumerate(prior['profiles']):
        d,a,seam,guards=arrays(unpack(p['stdout']))
        for name,data in [('raw',a['RAW']),('expected',a['AA8'])]:
            blob=data.astype('<f8').tobytes();path=work/f'{name}-{index}.bin';path.write_bytes(blob);files.append(str(path));inputs[f'{name}-{index}']=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'stream.exe'
    r=dict(passed=False,**sources.fields(),control=control,control_sha256=sha(ROOT/control),input_images=inputs,compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),real_time=False,physical_fidelity=False,new_audio=False,new_original_equation_rows=0)
    flags=['--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/stream_output_probe.rs'),'--extern','rf_d_circuit='+str(LIB)];phase='compile';last=None;command=[COMPILER,'--test',*flags,'-o',str(work/'guards.exe')]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='unit';command=[str(work/'guards.exe'),'stream::tests::','--test-threads=1'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unit_tests']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));assert last.returncode==0,last.stdout.decode(errors='replace')
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
    while(ROOT/f'evidence/stream_output_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/stream_output_native{k:02d}.json',r);print('STREAM_OUTPUT',r['passed'],r.get('measurements'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
