"""Ordering, duplicate accumulation and representation size on the real facade."""
import os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_incidence_selection import OWN as BASE
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed
def main():
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(BASE+['tools/check_incidence_packet.py','tools/incidence_packet_contract.rs'])
    r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),real_time=False);exe=work/'packet.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);last=None
    command=[COMPILER,'--edition=2021','--cfg','laboratory','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/incidence_packet_contract.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(exe)];last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        v=list(map(int,last.stdout.decode().strip().split(',')[1:]));assert len(v)==4;r['stdout']=packed(last.stdout);r['measurements']=dict(zip(['contracts','previous_parts_bytes','selected_parts_bytes','tangent_bytes'],v));r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());path=ROOT/'evidence/incidence_voice_packet01.json';assert not path.exists();write(path,r);print('INCIDENCE_PACKET',r['passed'],r.get('measurements'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
