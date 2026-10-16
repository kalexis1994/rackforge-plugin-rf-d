"""Lifecycle admission: bounded prefix, complete native render, cancellation and publication."""
import hashlib,json,os,struct,subprocess,sys,traceback
from pathlib import Path
from unittest.mock import patch
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_long_note_aa import arrays
from check_offline_producer import OWN as BASE
from check_vco_phase import COMPILER,LIB
import render_nominal as cli
OWN=list(dict.fromkeys(BASE+['tools/check_nominal_render.py','tools/nominal_render_probe.rs','tools/nominal_render_main.rs','tools/render_nominal.py','crates/rf-d-circuit/src/nominal_render.rs','docs/NOMINAL_RENDER_PROTOCOLO.md']))
CONTROL='evidence/long_note_aa_native01.json'

def control():
    r=json.loads((ROOT/CONTROL).read_text());assert r['passed'];raw=unpack(r['profiles'][1]['stdout']);_,a,_,_=arrays(raw)
    final=[list(map(float,line.split(',')[-236:])) for line in raw.decode().splitlines() if line.startswith('FINAL,')];assert len(final)==1
    return a['AA8'],final[0]

def prefix_parse(raw):
    lines=raw.decode().splitlines();p=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('PREFIX,')];s=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('SIZES,')];c=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('CONTROL,')]
    assert len(p)==len(s)==len(c)==1 and len(p[0])==10 and len(s[0])==3 and len(c[0])==8
    p=p[0];s=s[0];c=c[0];assert c[:4]==[10000*524288,p[6],3841,433] and c[1]>10000 and 0<c[4]<=1e-6 and c[5]<=1e-12 and c[6]<=2e-9 and c[7]<=1
    assert p[0]>0 and p[1:4]==[432,0,1] and p[4]>0 and p[5:]==[10000*524288,int(c[1]),int(c[1]),433,3841];assert s[0]<=48*1024
    return dict(prefix=p,sizes=s,control=c)

def prefix_wav(samples):
    payload=samples[:432].astype('<f4').tobytes();fmt=struct.pack('<HHIIHH',3,1,48000,192000,4,32);chunks=b'fmt '+struct.pack('<I',16)+fmt+b'fact'+struct.pack('<II',4,432)+b'data'+struct.pack('<I',len(payload))+payload
    return b'RIFF'+struct.pack('<I',4+len(chunks))+b'WAVE'+chunks

def run():
    work=cli.AREA;assert not list(work.iterdir());sources=Sources(OWN);samples,final=control();blob=samples[:433].astype('<f8').tobytes();fixture=work/'expected.bin';fixture.write_bytes(blob);exe=work/'prefix.exe';wav=work/'prefix.wav.part';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    r=dict(passed=False,**sources.fields(),control=CONTROL,control_sha256=sha(ROOT/CONTROL),prefix_input=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest()),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),real_time=False,physical_fidelity=False,new_original_equation_rows=0);phase='compile';command=[];last=None
    flags=['--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/nominal_render_probe.rs'),'--extern','rf_d_circuit='+str(LIB)]
    try:
        command=[COMPILER,'--test',*flags,'-o',str(work/'guards.exe')];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='unit';command=[str(work/'guards.exe'),'render::tests::','--test-threads=1'];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unit_tests']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'));assert last.returncode==0,last.stdout.decode(errors='replace')
        phase='compile';command=[COMPILER,*flags,'-C','strip=symbols','-o',str(exe)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='prefix';command=[str(exe),str(fixture),str(wav)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=180);r['prefix_stdout']=packed(last.stdout);assert last.returncode==0,last.stderr.decode(errors='replace')
        phase='prefix_parse';r['prefix_measurements']=prefix_parse(last.stdout);data=wav.read_bytes();assert data==prefix_wav(samples);r['prefix_wav']=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),matches_independent_header_and_f32_payload=True)
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        if phase=='prefix_parse':
            try:prefix_parse(last.stdout);assert wav.read_bytes()==prefix_wav(samples);r['unchanged_replay']='unexpected pass'
            except Exception:r['unchanged_replay']=traceback.format_exc()
        else:
            if phase=='prefix' and wav.exists():wav.unlink()
            retry=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=180);r['unchanged_replay']=dict(exit_code=retry.returncode,stdout=packed(retry.stdout),stderr=retry.stderr.decode(errors='replace'))
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    if 'failure' not in r:
        phase='wrapper';original=sha(cli.ARTIFACT)
        try:
            cancelled=cli.render(pre_cancel=True,quiet=True);assert cancelled['passed'] and cancelled['cancelled'] and not cancelled['published'] and cancelled['temporary_area_empty'];r['cancel_before_dc']=cancelled
            def cancel_after(line,path):
                if line.startswith('PROGRESS,'):path.write_bytes(b'cancel\n')
            cancelled=cli.render(on_line=cancel_after,quiet=True);assert cancelled['passed'] and cancelled['cancelled'] and not cancelled['published'] and cancelled['temporary_area_empty'];r['cancel_after_progress']=cancelled
            with patch.object(cli,'compile_native',return_value=([sys.executable,'-c','import sys;print("INJECTED_CHILD_FAILURE");sys.exit(7)'],dict(injected=True))):
                try:cli.render(quiet=True);raise AssertionError('expected process failure')
                except RuntimeError:failed=json.loads(cli.RECEIPT.read_text());assert failed['exit_code']==7 and not failed['passed'] and not failed['published'] and failed['temporary_area_empty'];r['injected_process_failure']=failed
            with cli.Laboratory() as lab:
                stage=lab.own('render.wav.part');stage.write_bytes(cli.ARTIFACT.read_bytes());validated=cli.validate_wav(stage)
                with patch.object(cli.os,'replace',side_effect=PermissionError('injected publication failure')):
                    try:cli.promote(stage);raise AssertionError('expected publication failure')
                    except PermissionError:assert stage.exists() and sha(cli.ARTIFACT)==original
                r['injected_publication_failure']=dict(validated=validated,previous_wav_preserved=True)
            occupied=work/'foreign.txt';occupied.write_bytes(b'foreign')
            try:
                try:
                    with cli.Laboratory():raise AssertionError('occupied area accepted')
                except RuntimeError:assert occupied.read_bytes()==b'foreign'
            finally:occupied.unlink()
            for quota in[0,-1,4097,True]:
                try:cli.render(quota);raise AssertionError('invalid quota accepted')
                except ValueError:pass
            r['preflight_guards']=dict(occupied_area_preserved=True,invalid_quotas_rejected=4)
            assert sha(cli.ARTIFACT)==original and not list(work.iterdir())
            print('NOMINAL_RENDER_PREFIX_AND_LIFECYCLE_PASS; starting complete fine-profile render',flush=True)
            phase='full';full=cli.render(quiet=False);r['full_render']=full;assert full['passed'] and full['published'] and full['temporary_area_empty']
            phase='full_parse';m=cli.parse_complete(unpack(full['stdout']));assert m==full['measurements'];assert struct.pack('<236d',*m['state'])==struct.pack('<236d',*final);assert full['output']['sha256']==original==sha(cli.ARTIFACT)
            r['full_final_state_bitwise_identical']=True;r['passed']=True
        except Exception:
            r.update(failure=traceback.format_exc(),failed_phase=phase)
            if cli.RECEIPT.exists():r['wrapper_last_receipt']=json.loads(cli.RECEIPT.read_text())
            if phase=='full_parse':
                try:
                    m=cli.parse_complete(unpack(full['stdout']));assert m==full['measurements'];assert struct.pack('<236d',*m['state'])==struct.pack('<236d',*final);assert full['output']['sha256']==original==sha(cli.ARTIFACT);r['unchanged_replay']='unexpected pass'
                except Exception:r['unchanged_replay']=traceback.format_exc()
            else:
                try:r['unchanged_replay']=cli.render(quiet=True)
                except Exception:r['unchanged_replay']=dict(failure=traceback.format_exc(),receipt=json.loads(cli.RECEIPT.read_text()))
    sources.unchanged();r['temporary_area_empty']=not list(work.iterdir());k=1
    while(ROOT/f'evidence/nominal_render_native{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/nominal_render_native{k:02d}.json',r);print('NOMINAL_RENDER',r['passed'],r.get('prefix_measurements'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':run()
