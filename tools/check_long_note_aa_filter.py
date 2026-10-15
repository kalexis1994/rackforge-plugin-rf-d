"""Native FIR versus independent convolution, analytic tones and alias bypass."""
import json,math,os,subprocess,traceback
import numpy as np
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_long_note_aa import arrays
from check_long_note_aa_design import coefficients
from check_vco_phase import COMPILER,LIB
def convolution(x,h,factor,count):
    return np.convolve(np.pad(x,(len(h)//2,0),constant_values=float(x[0])),h,'valid')[::factor][:count]
def audit(raw,native):
    tones={};heap=None
    for line in raw.decode().splitlines():
        z=line.split(',')
        if z[0]=='TONE':
            key=(int(z[1]),int(z[2]));a=tones.setdefault(key,[]);assert int(z[3])==len(a);a.append(float(z[4]))
        elif z[0]=='FILTER_HEAP':heap=int(z[1])
    assert heap==0 and len(tones)==20
    fixtures=[];notes=[]
    for (factor,hz),y in tones.items():
        fs=48000*factor;h=coefficients(fs);M=len(h)//2
        # Same argument operation order, independent scalar libm versus native std.
        x=np.array([math.cos(math.tau*hz*i/fs) for i in range(3073)]);a=np.array(y);b=convolution(x,h,factor,257)
        err=float(max(abs(a-b)));assert err<=1e-14,(factor,hz,err)
        response=float(np.dot(h,np.cos(2*np.pi*hz*(np.arange(len(h))-M)/fs)))
        expected=np.array([response*math.cos(math.tau*hz*n/48000) for n in range(257)])
        transfer=float(max(abs(a[48:]-expected[48:])));assert transfer<=1e-11,(factor,hz,transfer)
        if hz>=24000 and hz<fs/2:assert max(abs(a[48:]))<=10**(-90/20)
        fixtures.append(dict(factor=factor,input_hz=hz,convolution_max_error_v=err,analytic_max_error_v=transfer,steady_max=float(max(abs(a[48:])))))
    bypass=np.cos(2*np.pi*30000*np.arange(48,257)/48000);alias=np.cos(2*np.pi*18000*np.arange(48,257)/48000)
    assert max(abs(bypass-alias))<1e-11 and max(abs(bypass))>.99 and max(abs(bypass))>10**(-90/20)
    assert max(abs(np.array(tones[(4,180000)])[48:]))>.99
    assert max(abs(np.array(tones[(8,180000)])[48:]))<=10**(-90/20)
    r=json.loads((ROOT/native).read_text());assert r['passed']
    for p in r['profiles']:
        d,a,seam,guards=arrays(unpack(p['stdout']));errors={}
        for factor,tag,stride in[(4,'AA4',2),(8,'AA8',1)]:
            b=convolution(a['RAW'][::stride],coefficients(48000*factor),factor,14401);error=float(max(abs(a[tag]-b)));assert error<=1e-14,error;errors[tag]=error
        notes.append(dict(maximum_full_ticks=p['maximum_full_ticks'],convolution_max_error_v=errors))
    return dict(fixtures=fixtures,notes=notes,heap_allocations=heap,bypass_30khz_alias_18khz_confirmed=True,bypass_rejected_by_90db_gate=True,undersampled_180khz_alias_at_192k_confirmed=True,oversampled_180khz_rejected_at_384k=True,independent_convolution=True)
def main():
    native='evidence/long_note_aa_native01.json';design='evidence/long_note_aa_design01.json';assert json.loads((ROOT/design).read_text())['passed']
    names=['tools/check_long_note_aa_filter.py','tools/long_note_aa_filter_probe.rs','tools/check_long_note_aa.py','tools/check_long_note_aa_design.py','crates/rf-d-circuit/src/j7_antialias.rs','crates/rf-d-circuit/src/j7_antialias_coefficients.rs','docs/LONG_NOTE_AA_PROTOCOLO.md','docs/LONG_NOTE_AA_AUDITORIA.md'];sources=Sources(names)
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());exe=work/'filter.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    r=dict(passed=False,**sources.fields(),native=native,native_sha256=sha(ROOT/native),design=design,design_sha256=sha(ROOT/design),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB));command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/long_note_aa_filter_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];last=None;phase='compile'
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='native';command=[str(exe)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['stdout']=packed(last.stdout);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='audit';r.update(audit(last.stdout,native));r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase)
        if phase=='audit':
            try:audit(last.stdout,native);r['unchanged_replay']='unexpected pass'
            except Exception:r['unchanged_replay']=traceback.format_exc()
        else:
            r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
            retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while(ROOT/f'evidence/long_note_aa_filter{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/long_note_aa_filter{k:02d}.json',r);print('LONG_NOTE_AA_FILTER',r['passed'],r.get('notes'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
