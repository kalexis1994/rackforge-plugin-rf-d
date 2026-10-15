"""Long continuous nominal note; preserve raw evidence and unchanged failed gates."""
import json,math,os,subprocess,threading,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack,US
from run_chain_startup import OWN as BASE,parse as startup_parse
from check_j7_readout import audio as old_audio
from prepare_long_note_aa import images
from check_vco_phase import COMPILER,LIB
from pathlib import Path
OWN=list(dict.fromkeys(BASE+['tools/check_long_note_aa.py','tools/prepare_long_note_aa.py','tools/long_note_aa_probe.rs','crates/rf-d-circuit/src/j7_audio_readout.rs','crates/rf-d-circuit/src/j7_oversampled_readout.rs','crates/rf-d-circuit/src/j7_antialias.rs','crates/rf-d-circuit/src/j7_antialias_coefficients.rs','docs/LONG_NOTE_AA_PROTOCOLO.md']))
def arrays(raw):
    d=startup_parse(raw,False);assert d['measurement']['ticks']==301000*US
    groups={tag:[] for tag in ['RAW','AA4','AA8']};seam=None;guard=None
    for line in raw.decode().splitlines():
        z=line.split(',');tag=z[0]
        if tag in groups:assert int(z[1])==len(groups[tag]);groups[tag].append(float(z[2]))
        elif tag=='SEAM':seam=list(map(float,z[2:]));assert int(z[1])==75000*US
        elif tag=='READOUT':guard=list(map(int,z[1:]))
    assert len(groups['RAW'])==115585 and len(groups['AA4'])==len(groups['AA8'])==14401
    a={k:np.array(v) for k,v in groups.items()};assert all(np.isfinite(v).all() for v in a.values())
    m=d['measurement'];assert m['heap_allocations']==0 and m['max_residual_a']<=1e-12 and m['max_correction_v']<=2e-9 and m['max_error']<=1 and m['selected_pairs']==24 and m['exact_replays']==8 and m['atomic_rejections']==5
    assert len(d['grid'])==2409 and len(d['roots'])==24 and len(seam)==236 and guard[0]==guard[1]>=4 and guard[2:]==[0,301000*US]
    assert [int(e[0]) for e in d['events']]==[1000*US,200000*US]
    return d,a,seam,guard
def difference(a,b,rms_gate=.001,peak_gate=.003,mean_gate=1e-6):
    e=a-b;peak=float(max(abs(b)));rms=float(np.sqrt(np.mean(e*e)));ref=float(np.sqrt(np.mean(b*b)))
    r=dict(samples=len(a),rms_error_v=rms,rms_relative=rms/ref,peak_error_v=float(max(abs(e))),peak_relative=float(max(abs(e)))/peak,mean_error_v=float(abs(np.mean(e))))
    assert r['rms_relative']<=rms_gate and r['peak_relative']<=peak_gate and r['mean_error_v']<=mean_gate,r
    return r
def windows(a,b,rate=False):
    gates=(.0001,.0003,1e-7) if rate else(.001,.003,1e-6)
    out={name:difference(a[lo:hi],b[lo:hi],*gates) for name,lo,hi in [('whole',0,14401),('attack',48,3601),('hold',3600,9601),('release',9600,14401)]}
    pre=float(max(abs(a[:48]-b[:48])));assert pre<=1e-6;out['pre_key_max_error_v']=pre;return out
def analyse(profiles):
    native=json.loads((ROOT/'evidence/j7_readout_native03.json').read_text());assert native['passed'];out=[];aa=[]
    for index,p in enumerate(profiles):
        raw=unpack(p['stdout']);d,a,seam,g=arrays(raw);reference=unpack(native['profiles'][index]['stdout']);old=startup_parse(reference);previous,_=old_audio(reference)
        assert p['maximum_full_ticks']==native['profiles'][index]['maximum_full_ticks']
        assert all(d['grid'][t]==v for t,v in old['grid'].items() if t<=75000*US)
        assert d['dc']==old['dc'] and seam==old['events'][1][2:]
        assert a['RAW'][::8][:3601].tobytes()==np.array(previous[:3601]).tobytes()
        out.append(dict(maximum_full_ticks=p['maximum_full_ticks'],measurement=d['measurement'],readout_guards=g,prefix_75ms_identical=True,rate_refinement=windows(a['AA4'],a['AA8'],True),raw_peak_v=float(max(abs(a['RAW']))),filtered_peak_v=float(max(abs(a['AA8'])))))
        aa.append(a['AA8'])
    return dict(profiles=out,temporal_refinement=windows(*aa),raw_rate_hz=384000,output_rate_hz=48000,frames=14400,anchor_samples=1,electrical_end_s=.301,output_end_s=.3)
def live(command,env,timeout):
    p=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE);timer=threading.Timer(timeout,p.kill);timer.daemon=True;timer.start();rows=[]
    try:
        for row in p.stdout:
            rows.append(row)
            if row.startswith(b'PROGRESS,'):print('LONG_NOTE',command[-1],row.decode().strip(),flush=True)
        code=p.wait();err=p.stderr.read();return subprocess.CompletedProcess(command,code,b''.join(rows),err)
    finally:timer.cancel()
def main():
    for n,s in images().items():assert (ROOT/n).read_bytes()==s.encode(),n
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(OWN);exe=work/'long-note.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),numpy_version=np.__version__,profiles=[],control='evidence/j7_readout_native03.json',control_sha256=sha(ROOT/'evidence/j7_readout_native03.json'),physical_fidelity=False,real_time=False);phase='compile';last=None
    flags=['--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/long_note_aa_probe.rs'),'--extern','rf_d_circuit='+str(LIB)];command=[COMPILER,'--test',*flags,'-o',str(work/'guards.exe')]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='unit';command=[str(work/'guards.exe'),'--test-threads=1'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unit_tests']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));assert last.returncode==0,last.stdout.decode(errors='replace')
        phase='compile';command=[COMPILER,*flags,'-C','strip=symbols','-o',str(exe)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        for maximum in[2*US,US]:
            phase='trajectory';command=[str(exe),str(maximum)];last=live(command,env,2400);item=dict(maximum_full_ticks=maximum,exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));r['profiles'].append(item);assert last.returncode==0,item['stderr'];d,a,s,g=arrays(last.stdout);item.update(measurement=d['measurement'],readout_guards=g);print('LONG_NOTE_COMPLETE',maximum,d['measurement'],flush=True)
        phase='analysis';r['analysis']=analyse(r['profiles']);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command)
        if phase=='analysis':
            try:analyse(r['profiles']);r['unchanged_gate_replay']='unexpected pass'
            except Exception:r['unchanged_gate_replay']=traceback.format_exc()
        else:
            if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
            replay=live(command,env,2400) if phase=='trajectory' else subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120)
            r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while(ROOT/f'evidence/long_note_aa_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/long_note_aa_native{k:02d}.json',r);print('LONG_NOTE_AA',r['passed'],r.get('analysis',{}).get('temporal_refinement'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
