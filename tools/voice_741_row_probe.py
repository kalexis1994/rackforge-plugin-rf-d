"""Sequential release gates: exact disabled build, active control, conditional BUS."""
import json,os
from pathlib import Path
import numpy as np
import voice_741_row_build as build
import voice_741_row_compare as metrics
import voice_kcl_budget_runner as runner
import voice_kcl_alias_instrument as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=build.WORK


def main():
    output=ROOT/'evidence/voice_741_row_runs01.json'
    if output.exists():raise ValueError('preserve previous experiment')
    helpers=(Path(__file__),Path(build.__file__),Path(metrics.__file__))
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    runner.WORK=WORK;records={};comparisons={};control=None;decision='disabled-build gate'
    env_prior=os.environ.pop('RF_D_741_REDUCE',None)
    try:
        for kind in ('constant','returned'):
            label='row-off-'+kind;r=runner.run(WORK/'bin/candidate.exe',kind,label,False);records[label]=r
            a=np.loadtxt(WORK/'runs'/(label+'.txt'),skiprows=1,ndmin=2)
            b=np.loadtxt(prior.WORK/'runs'/('kcl-alias-off-'+kind+'.txt'),skiprows=1,ndmin=2)
            comparisons[kind]=runner.exact(a,b)
            if not comparisons[kind]['passed']:return
        os.environ['RF_D_741_REDUCE']='1';decision='active positive control gate'
        r=runner.run(WORK/'bin/candidate.exe','constant','row-on-constant',False);records[r['label']]=r
        if not r['trajectory_complete']:return
        log=(WORK/'runs'/(r['label']+'.log')).read_text(encoding='utf-8')
        if 'RF741REDUCE,setup,l.xic3.l2,' not in log:raise ValueError('explicit activation required')
        a=np.loadtxt(WORK/'runs'/(r['label']+'.txt'),skiprows=1,ndmin=2)
        b=np.loadtxt(prior.WORK/'runs/kcl-alias-off-constant.txt',skiprows=1,ndmin=2)
        control=metrics.compare(a,b)
        if not control['passed']:return
        decision='active variable BUS full trajectory'
        r=runner.run(WORK/'bin/candidate.exe','returned','row-on-returned',False);records[r['label']]=r
        decision='variable BUS complete' if r['trajectory_complete'] else 'variable BUS rejected'
    finally:
        os.environ.pop('RF_D_741_REDUCE',None)
        if env_prior is not None:os.environ['RF_D_741_REDUCE']=env_prior
        after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
        report=dict(schema='rf-d/741-equivalent-row-runs/v1',records=records,disabled_comparisons=comparisons,
                    active_control=control,decision=decision,wrapper_sha256=before,wrapper_sha256_after=after,
                    environment_flag='RF_D_741_REDUCE=1 only for active runs',new_solves=len(records),
                    coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
        print('741 row experiment:',decision,'control:',None if control is None else control['passed'],flush=True)


if __name__=='__main__':main()
