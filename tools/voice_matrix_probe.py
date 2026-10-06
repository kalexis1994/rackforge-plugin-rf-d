"""Four frozen runs: independent matrix flag; no old verbose trace or row variant."""
import json, os
from pathlib import Path
import numpy as np
import voice_matrix_build_retry as build
import voice_kcl_budget_runner as runner
import voice_kcl_alias_instrument as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=build.WORK

def main():
    output=ROOT/'evidence/voice_matrix_runs01.json'
    if output.exists(): raise ValueError('preserve experiment')
    helpers=[Path(__file__),Path(build.__file__),Path(runner.__file__),ROOT/'tools/voice_matrix_trace.py']
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    runner.WORK=WORK;records={};comparisons={}
    saved={k:os.environ.pop(k,None) for k in ('RF_D_MATRIX_TRACE','RF_D_TRACE','RF_D_741_REDUCE')}
    try:
        for enabled in (False,True):
            if enabled:os.environ['RF_D_MATRIX_TRACE']='1'
            for kind in ('constant','returned'):
                label='matrix-'+('on' if enabled else 'off')+'-'+kind
                r=runner.run(WORK/'bin/observer.exe',kind,label,False);records[label]=r
                a=np.loadtxt(WORK/'runs'/(label+'.txt'),skiprows=1,ndmin=2)
                b=np.loadtxt(prior.WORK/'runs'/('kcl-alias-off-'+kind+'.txt'),skiprows=1,ndmin=2)
                comparisons[label]=runner.exact(a,b)
                print('exact original',label,comparisons[label]['passed'],flush=True)
                if not comparisons[label]['passed'] or (kind=='constant' and not r['trajectory_complete']):return
    finally:
        for k,v in saved.items():
            os.environ.pop(k,None)
            if v is not None:os.environ[k]=v
        after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
        report=dict(schema='rf-d/newton-matrix-runs/v1',records=records,comparisons=comparisons,
            wrapper_sha256=before,wrapper_sha256_after=after,new_solves=len(records),wall_limit_s=240,
            environment='only RF_D_MATRIX_TRACE=1 for on runs; old trace and equivalent row removed',
            coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
