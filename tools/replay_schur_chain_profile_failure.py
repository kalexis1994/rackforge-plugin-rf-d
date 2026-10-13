"""Preserve unchanged profile replay before repairing short-circuit call accounting."""
import base64,json,os,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from profile_schur_chain_cost import validate

def main():
    name='evidence/voice_schur_refined_chainprofile01.json';old=json.loads((ROOT/name).read_text(encoding='utf8'));require(not old['passed'] and old['commands'][-1]['exit_code']==0,'auditor failure only')
    for n,h in old['source_sha256'].items():require(sha(ROOT/n)==h,'unchanged failed profile source')
    cmd=old['commands'][-1]['command'];env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=600,creationflags=subprocess.CREATE_NO_WINDOW)
    q=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
    calls=lambda s:[(int(x.split(',')[1]),int(x.split(',')[3])) for x in s.splitlines() if x.startswith('PROFILE,')]
    require(p.returncode==0 and calls(p.stdout)==calls(old['commands'][-1]['stdout']) and p.stdout.splitlines()[-1]=='PROFILED_PASSED,84,1834','identical call counts and root bits')
    try:validate(Path(cmd[0]).parent,q)
    except ValueError as e:require(str(e)=='exact profile calls','same auditor rejection');failure=str(e)
    else:raise ValueError('unexpected auditor pass')
    write('evidence/voice_schur_chain_profile_replay01.json',dict(passed=True,failed_receipt_sha256=sha(ROOT/name),source_sha256={n:sha(ROOT/n) for n in ['tools/replay_schur_chain_profile_failure.py','tools/profile_schur_chain_cost.py',name]},private_used_sha256={Path(cmd[0]).relative_to(ROOT).as_posix():sha(Path(cmd[0]))},identical_call_counts=True,exact_root_fields_preserved=True,failure=failure,command=q,failed_profile_source_base64=base64.b64encode((ROOT/'tools/profile_schur_chain_cost.py').read_bytes()).decode(),numerical_gates_changed=False))
    print('CHAIN_PROFILE_FAILURE_REPLAY',failure)
if __name__=='__main__':main()
