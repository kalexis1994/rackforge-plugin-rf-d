"""Sequential exact/off, real-factor replay, active control and conditional BUS."""
import json,os
from pathlib import Path
import numpy as np
import voice_refine_replay_build as build
import voice_refine_trace as trace
import voice_matrix_trace as matrix
import voice_matrix_build_retry as observed
import voice_741_row_compare as metrics
import voice_refine_runner as runner
import voice_kcl_alias_instrument as original
import vco1_circuit_reference as vco

ROOT=vco.ROOT;WORK=build.WORK

def main():
    output=ROOT/'evidence/voice_refine_runs01.json'
    if output.exists():raise ValueError('preserve experiment')
    arithmetic=vco.read(ROOT/'evidence/voice_refine_arithmetic02.json')
    if not arithmetic['passed'] or arithmetic['captured_rows']!=266:raise ValueError('compiled arithmetic precheck')
    old=(ROOT/'tools/voice_kcl_budget_runner.py').read_bytes()
    if Path(runner.__file__).read_bytes()!=old.replace(b'timeout=240',b'timeout=600',1):raise ValueError('budget-only runner')
    helpers=[Path(__file__),Path(build.__file__),Path(trace.__file__),Path(runner.__file__),Path(metrics.__file__),
        ROOT/'tools/voice_refine_dd.h',ROOT/'tools/voice_refine_function_replay.c']
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    runner.WORK=WORK;records={};disabled={};replay=[];control=None;decision='disabled-build gate'
    flags=('RF_D_LINEAR_REFINE','RF_D_REFINE_REPLAY','RF_D_MATRIX_TRACE','RF_D_TRACE','RF_D_741_REDUCE')
    saved={k:os.environ.pop(k,None) for k in flags}
    try:
        for kind in ('constant','returned'):
            label='refine-off-'+kind;r=runner.run(WORK/'bin/candidate.exe',kind,label,False);records[label]=r
            a=np.loadtxt(WORK/'runs'/(label+'.txt'),skiprows=1,ndmin=2)
            b=np.loadtxt(original.WORK/'runs'/('kcl-alias-off-'+kind+'.txt'),skiprows=1,ndmin=2)
            disabled[kind]=runner.exact(a,b)
            if not disabled[kind]['passed'] or (kind=='constant' and not r['trajectory_complete']):return
        decision='real-factor replay gate';os.environ['RF_D_REFINE_REPLAY']='1';os.environ['RF_D_MATRIX_TRACE']='1'
        label='refine-replay-returned';r=runner.run(WORK/'bin/candidate.exe','returned',label,False);records[label]=r
        a=np.loadtxt(WORK/'runs'/(label+'.txt'),skiprows=1,ndmin=2);b=np.loadtxt(original.WORK/'runs/kcl-alias-off-returned.txt',skiprows=1,ndmin=2)
        disabled['replay']=runner.exact(a,b)
        if not disabled['replay']['passed']:return
        text=(WORK/'runs'/(label+'.log')).read_text(encoding='utf-8');snapshots=matrix.parse(text);details=trace.parse(text)
        prior_text=(observed.WORK/'runs/matrix-on-returned.log').read_text(encoding='utf-8');prior_snapshots=matrix.parse(prior_text)
        audit=vco.read(ROOT/'evidence/voice_matrix_observation01.json')
        if snapshots!=prior_snapshots or len(details)!=2:raise ValueError('same original A/b/x and real factors required')
        replay=[trace.compare(s,d,a) for s,d,a in zip(snapshots,details,audit['analyses'])]
        if not all(r['passed'] for r in replay):return
        for flag in ('RF_D_REFINE_REPLAY','RF_D_MATRIX_TRACE'):os.environ.pop(flag,None)
        os.environ['RF_D_LINEAR_REFINE']='1';decision='active positive control gate'
        r=runner.run(WORK/'bin/candidate.exe','constant','refine-on-constant',False);records[r['label']]=r
        if not r['trajectory_complete']:return
        a=np.loadtxt(WORK/'runs/refine-on-constant.txt',skiprows=1,ndmin=2)
        b=np.loadtxt(original.WORK/'runs/kcl-alias-off-constant.txt',skiprows=1,ndmin=2)
        control=metrics.compare(a,b)
        if not control['passed']:return
        decision='active variable BUS full trajectory'
        r=runner.run(WORK/'bin/candidate.exe','returned','refine-on-returned',False);records[r['label']]=r
        decision='variable BUS complete' if r['trajectory_complete'] else 'variable BUS rejected'
    finally:
        for k,v in saved.items():
            os.environ.pop(k,None)
            if v is not None:os.environ[k]=v
        report=dict(schema='rf-d/linear-refine-runs/v1',records=records,disabled_comparisons=disabled,replay=replay,active_control=control,
            decision=decision,wrapper_sha256=before,wrapper_sha256_after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
            arithmetic_sha256=vco.sha(ROOT/'evidence/voice_refine_arithmetic02.json'),wall_limit_s=600,new_solves=len(records),
            coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
        print('linear refinement:',decision,'control:',None if control is None else control['passed'],flush=True)

if __name__=='__main__':main()
