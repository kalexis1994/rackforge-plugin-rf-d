"""Numerical qualification of a nominal-cycle Hz adapter; no physical CV claim."""
import argparse,hashlib,json,os,subprocess,traceback
from decimal import Decimal,localcontext,ROUND_FLOOR
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_long_note_aa import arrays,difference
from check_nominal_render import OWN as BASE
from check_vco_phase import COMPILER,LIB
from prepare_pitch_program import images
EXTRA=['tools/check_pitch_program.py','tools/prepare_pitch_program.py','tools/pitch_program_probe.rs','crates/rf-d-circuit/src/pitch_phase_source.rs','crates/rf-d-circuit/src/pitch_program_schedule.rs','docs/PITCH_PROGRAM_PROTOCOLO.md']
OWN=list(dict.fromkeys(BASE+EXTRA+list(images())))
CONTROL='evidence/long_note_aa_native01.json'
US=524288;TICK=125e-9/65536.

def controls():
    r=json.loads((ROOT/CONTROL).read_text(encoding='utf8'));assert r['passed'];_,a,_,_=arrays(unpack(r['profiles'][1]['stdout']))
    return {n:values[:length].astype('<f8').tobytes() for n,values,length in [('raw',a['RAW'],3841),('expected',a['AA8'],433)]}

def parse(raw):
    d=dict(source=None,clock=None,phase=[],negative=None,nominal=None,sequences=[],events=[],sizes=None)
    values={i:{k:[] for k in ['RAW','AA4','AA8']} for i in range(2)}
    for line in raw.decode().splitlines():
        z=line.split(',');tag=z[0]
        if tag in ['SOURCE','CLOCK','NEGATIVE','NOMINAL','SIZES']:d[dict(SOURCE='source',CLOCK='clock',NEGATIVE='negative',NOMINAL='nominal',SIZES='sizes')[tag]]=list(map(float,z[1:]))
        elif tag=='PHASE':d['phase'].append(list(map(float,z[1:])))
        elif tag=='SEQUENCE':d['sequences'].append(list(map(float,z[1:])))
        elif tag=='EVENT':d['events'].append(list(map(float,z[1:])))
        elif tag in ['RAW','AA4','AA8']:
            i=int(z[1]);assert int(z[2])==len(values[i][tag]);values[i][tag].append(float(z[3]))
    assert d['source'][:2]==[4097,0] and d['source'][2]<=2e-15 and d['source'][3]<=1e-12
    assert len(d['clock'])==2 and len(d['phase'])==99 and d['negative'][0]>1e-3
    assert d['nominal']==[10000*US,10109,433,0,3841]
    assert len(d['sequences'])==2 and len(d['events'])==8 and len(d['sizes'])==3 and d['sizes'][0]<=48*1024
    for i,s in enumerate(d['sequences']):
        assert len(s)==12 and s[0]==i and s[1] in [2*US,US,US/2] and s[2]>0 and s[3]>0 and s[4]>=4 and s[5:8]==[0,1105,9217] and 0<s[8]<=s[1]*TICK and s[9]<=1e-12 and s[10]<=2e-9 and s[11]<=1
        assert [e[1] for e in d['events'] if e[0]==i]==[1000*US,6250*US,12500*US,18750*US] and all(len(e)==238 for e in d['events'] if e[0]==i)
        assert all(len(values[i][k])==n for k,n in [('RAW',9217),('AA4',1105),('AA8',1105)])
    return d,{i:{k:np.array(v) for k,v in x.items()} for i,x in values.items()}

def phase_audit(d):
    with localcontext() as ctx:
        ctx.prec=100;D=Decimal.from_float;f0,epoch=d['clock'];f=[f0,1.5*f0,0.5*f0];times=[0.,6250*US*TICK,12500*US*TICK]
        anchors=[None,(D(times[1])-D(epoch))*D(f0),None];anchors[2]=anchors[1]+(D(times[2])-D(times[1]))*D(f[1]);maximum=Decimal(0);phase_maximum=Decimal(0)
        for segment,ticks,hz,u,p in d['phase']:
            i=int(segment);assert hz==f[i];t=D(int(ticks)*TICK)
            target=(t-D(epoch))*D(f0) if i==0 else anchors[i]+(t-D(times[i]))*D(f[i])
            maximum=max(maximum,abs(D(u)-target));fraction=target-target.to_integral_value(rounding=ROUND_FLOOR);delta=abs(D(p)-fraction);phase_maximum=max(phase_maximum,min(delta,abs(Decimal(1)-delta)))
        assert maximum<=Decimal('1e-12') and phase_maximum<=Decimal('1e-12')
        return dict(precision=100,unwrapped_max_error_cycles=float(maximum),phase_max_error_cycles=float(phase_maximum),gate_cycles=1e-12)

def windows(a,b,rate=False):
    gates=(.0001,.0003,1e-7) if rate else(.001,.003,1e-6)
    out={name:difference(a[lo:hi],b[lo:hi],*gates) for name,lo,hi in [('whole',0,1105),('first',48,300),('retune_up',300,600),('retune_down',600,900),('release',900,1105)]}
    pre=float(max(abs(a[:48]-b[:48])));assert pre<=1e-6;out['pre_key_max_error_v']=pre;return out

def analyse(raw):
    d,a=parse(raw);return dict(measurements=d,decimal_phase=phase_audit(d),temporal_refinement=windows(a[0]['AA8'],a[1]['AA8']),rate_refinement=[windows(a[i]['AA4'],a[i]['AA8'],True) for i in range(2)])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refined',action='store_true');args=ap.parse_args()
    for n,s in images().items():assert(ROOT/n).read_bytes()==s.encode(),n
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(OWN);blobs=controls();files=[]
    for n,b in blobs.items():p=work/(n+'.bin');p.write_bytes(b);files.append(str(p))
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);exe=work/'pitch.exe';r=dict(passed=False,**sources.fields(),control=CONTROL,control_sha256=sha(ROOT/CONTROL),input_images={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in blobs.items()},compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),profiles_ticks=[US,US/2] if args.refined else[2*US,US],refined=args.refined,real_time=False,physical_fidelity=False,physical_cv_model=False,new_audio=False,new_original_equation_rows=0)
    flags=['--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/pitch_program_probe.rs'),'--extern','rf_d_circuit='+str(LIB)];phase='compile';last=None;command=[COMPILER,'--test',*flags,'-o',str(work/'guards.exe')]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='unit';command=[str(work/'guards.exe'),'pitch_tests::','--test-threads=1'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unit_tests']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));assert last.returncode==0,last.stdout.decode(errors='replace')
        phase='compile';command=[COMPILER,*flags,'-C','strip=symbols','-o',str(exe)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='native';command=[str(exe),*files,'1' if args.refined else '0'];print('PITCH_NATIVE_START',r['profiles_ticks'],flush=True);last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=600);r['stdout']=packed(last.stdout);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='analysis';r['analysis']=analyse(last.stdout);r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command)
        if phase=='analysis':
            try:analyse(last.stdout);r['unchanged_gate_replay']='unexpected pass'
            except Exception:r['unchanged_gate_replay']=traceback.format_exc()
        else:
            if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
            retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=600);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while(ROOT/f'evidence/pitch_program_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/pitch_program_native{k:02d}.json',r);print('PITCH_PROGRAM',r['passed'],r.get('analysis',{}).get('temporal_refinement'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
