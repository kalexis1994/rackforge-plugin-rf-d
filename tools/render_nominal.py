"""Render the admitted 300 ms scene, then atomically publish its single current WAV."""
import argparse,hashlib,json,os,stat,struct,subprocess,sys,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from check_vco_phase import COMPILER,LIB
from affine_evidence import Sources
from check_hybrid_voice import packed
ARTIFACT=ROOT/'artifacts/rf-d-nominal-current.wav'
AREA=ROOT/'tmp/lab-current'
REFERENCE='evidence/long_note_aa_listening01.json'
RECEIPT=ROOT/'tmp/nominal-render-current.json'
NAMES=['render.lock','renderer.exe','render.wav.part','cancel.request']

def safe(path):
    path=Path(path);relative=path.relative_to(ROOT);cursor=ROOT
    for part in relative.parts:
        cursor=cursor/part
        if cursor.is_symlink() or (hasattr(cursor,'is_junction') and cursor.is_junction()):raise RuntimeError('linked render path: '+str(cursor))
    if not path.resolve().is_relative_to(ROOT.resolve()):raise RuntimeError('render path outside workspace')
    return path

class Laboratory:
    def __enter__(self):
        safe(AREA);AREA.mkdir(parents=True,exist_ok=True)
        if list(AREA.iterdir()):raise RuntimeError('tmp/lab-current is occupied; no files removed')
        self.lock=safe(AREA/NAMES[0]);self.lock.open('xb').close();self.owned=[self.lock];return self
    def own(self,name):
        assert name in NAMES and name!=NAMES[0];p=safe(AREA/name)
        if p.exists():raise RuntimeError('unexpected existing render file: '+str(p))
        self.owned.append(p);return p
    def __exit__(self,*exc):
        # Known files only, under the checked area; never enumerate-and-delete.
        for p in reversed(self.owned):
            safe(p)
            if p.exists():
                if not p.is_file():raise RuntimeError('render file became a directory')
                p.unlink()
        if list(AREA.iterdir()):raise RuntimeError('foreign file left in laboratory; preserved')

def compile_native(exe):
    baseline=json.loads((ROOT/'evidence/offline_producer_tests01.json').read_text())
    assert sha(Path(COMPILER))==baseline['compiler']['sha256'] and sha(LIB)==baseline['public_assembly_library_sha256']
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/nominal_render_main.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    with subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)) as p:
        try:stdout,stderr=p.communicate(timeout=120)
        except BaseException:p.kill();p.wait();raise
        if p.returncode:raise RuntimeError(stderr.decode(errors='replace'))
    return [str(exe)],dict(command=command,compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB))

def validate_wav(path):
    data=safe(path).read_bytes();reference=json.loads((ROOT/REFERENCE).read_text());assert reference['passed']
    # Validate container independently of the Rust writer before the exact SHA gate.
    assert len(data)==57656 and data[:4]==b'RIFF' and data[8:16]==b'WAVEfmt '
    assert struct.unpack('<I',data[4:8])[0]==len(data)-8 and struct.unpack('<IHHIIHH',data[16:36])==(16,3,1,48000,192000,4,32)
    assert data[36:40]==b'fact' and struct.unpack('<II',data[40:48])==(4,14400) and data[48:52]==b'data' and struct.unpack('<I',data[52:56])[0]==57600
    h=hashlib.sha256(data).hexdigest();assert h==reference['sha256'],'WAV differs from admitted fine-profile listening reference'
    return dict(path=str(ARTIFACT.relative_to(ROOT)),sha256=h,bytes=len(data),frames=14400,rate_hz=48000,reference=REFERENCE,reference_sha256=sha(ROOT/REFERENCE))

def promote(stage):
    metadata=validate_wav(stage);safe(ARTIFACT.parent);ARTIFACT.parent.mkdir(exist_ok=True);safe(ARTIFACT)
    assert stage.stat().st_dev==ARTIFACT.parent.stat().st_dev,'atomic promotion requires the same volume'
    os.replace(stage,ARTIFACT);assert sha(ARTIFACT)==metadata['sha256'];return metadata

def parse_complete(raw):
    lines=raw.decode().splitlines();done=[x for x in lines if x.startswith('COMPLETE,')];assert len(done)==1
    values=list(map(int,done[0].split(',')[1:]));assert values[:9]==[301000*524288,301000*524288,301151,301151,14401,14400,115585,14400,115584]
    progress=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('PROGRESS,')];assert progress and all(len(p)==8 for p in progress)
    assert all(a[0]<=b[0] and a[1]<=b[1] and a[3]<=b[3] and a[5]<=b[5] for a,b in zip(progress,progress[1:]))
    assert all(p[1]<=p[0]<=p[2]==301000*524288 and p[6]==min(p[5],14400) for p in progress)
    states=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('STATE,')];assert len(states)==1 and len(states[0])==236
    return dict(complete=values,progress=progress,state=states[0])

def render(quota=128,*,on_line=None,pre_cancel=False,quiet=False):
    if not isinstance(quota,int) or isinstance(quota,bool) or not 1<=quota<=4096:raise ValueError('quota must be 1..4096')
    names=['tools/render_nominal.py','tools/nominal_render_main.rs','crates/rf-d-circuit/src/nominal_render.rs','docs/NOMINAL_RENDER_PROTOCOLO.md']
    sources=Sources(names);result=dict(passed=False,published=False,cancelled=False,quota=quota,**sources.fields(),previous_wav_sha256=sha(ARTIFACT) if ARTIFACT.exists() else None,real_time=False,physical_fidelity=False);process=None;lines=[];error=None
    try:
        with Laboratory() as lab:
            exe=lab.own('renderer.exe');stage=lab.own('render.wav.part');cancel=lab.own('cancel.request')
            command,result['compile']=compile_native(exe)
            if pre_cancel:cancel.write_bytes(b'cancel\n')
            command=[*command,str(stage),str(cancel),str(quota),'300'];result['command']=command
            process=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
            try:
                while True:
                    try:
                        line=process.stdout.readline()
                        if not line:break
                        lines.append(line)
                        if not quiet and not line.startswith('STATE,'):print(line.rstrip(),flush=True)
                        if on_line:on_line(line,cancel)
                    except KeyboardInterrupt:
                        cancel.write_bytes(b'cancel\n')
                        if not quiet:print('Cancelacion solicitada; esperando frontera de cuota.',flush=True)
                result['exit_code']=process.wait();result['stderr']=process.stderr.read();raw=''.join(lines).encode();result['stdout']=packed(raw)
            finally:
                if process.poll() is None:process.terminate();process.wait()
            if result['exit_code']==130:
                assert 'CANCELLED,' in raw.decode() and not any(x.startswith('COMPLETE,') for x in lines);result['cancelled']=True;result['passed']=True
            else:
                assert result['exit_code']==0,result['stderr'];result['measurements']=parse_complete(raw)
                result['output']=promote(stage);result['published']=True;result['passed']=True
    except KeyboardInterrupt:
        error='KeyboardInterrupt during initialization/compile';result['cancelled']=True;result['failure']=error
    except Exception:
        error=traceback.format_exc();result['failure']=error
    finally:
        if process is not None:
            if process.poll() is None:process.terminate();process.wait()
            if process.stdout:process.stdout.close()
            if process.stderr:process.stderr.close()
    sources.unchanged();result['temporary_area_empty']=not list(AREA.iterdir());result['final_wav_sha256']=sha(ARTIFACT) if ARTIFACT.exists() else None
    if not result['published']:assert result['final_wav_sha256']==result['previous_wav_sha256'],'failed/cancelled render changed current WAV'
    write(RECEIPT,result)
    if error:raise RuntimeError(error)
    return result

def main():
    parser=argparse.ArgumentParser(description='Render nominal de 300 ms, perfil fino 1 us; un unico WAV actual. Ctrl+C cancela entre cuotas.')
    parser.add_argument('--quota',type=int,default=128,help='Invocaciones adaptativas por cuota (1..4096), no tiempo de CPU.')
    args=parser.parse_args();r=render(args.quota)
    if r['cancelled']:print('Cancelado; WAV anterior conservado.');return 130
    print('Publicado:',ARTIFACT);return 0
if __name__=='__main__':raise SystemExit(main())
