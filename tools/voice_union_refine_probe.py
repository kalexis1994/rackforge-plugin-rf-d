"""Sequential nominal control and the four frozen monolithic joint scenes."""
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
import voice_union_refine_runner as runner
import voice_union_refine_metrics as metrics
import loudness_voice_probes as joint
import vco1_circuit_reference as vco

ROOT=vco.ROOT;WORK=runner.WORK

def main():
    output=ROOT/'evidence/voice_union_refine_runs01.json'
    if output.exists():raise ValueError('preserve bank')
    prior=vco.read(ROOT/'evidence/voice_refine_validation01.json')
    if not prior['passed'] or not prior['candidate_admitted_locally']:raise ValueError('minimal VCO admission required')
    helpers=[Path(__file__),Path(runner.__file__),Path(metrics.__file__),Path(joint.__file__),ROOT/'tools/loudness_voice_circuit.py']
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    records={};identity=None;control=None;measurements={};comparisons={};errors={};decision='nominal disabled identity and coverage'
    try:
        vectors=runner.frozen('nominal','nominal500')['vectors']
        for label,binary in (('nominal-original','original'),('nominal-off','candidate')):
            records[label]=runner.run('nominal','nominal500',label,binary)
        a=np.loadtxt(WORK/'nominal-original.txt',skiprows=1,ndmin=2);b=np.loadtxt(WORK/'nominal-off.txt',skiprows=1,ndmin=2)
        identity=metrics.exact(a,b,vectors)
        if not identity['passed'] or not all(r['trajectory_complete'] for r in records.values()):return
        decision='nominal active control';records['nominal-on']=runner.run('nominal','nominal500','nominal-on','candidate',True)
        if not records['nominal-on']['trajectory_complete']:return
        c=np.loadtxt(WORK/'nominal-on.txt',skiprows=1,ndmin=2);control=metrics.control(c,a,vectors)
        if not control['passed']:return
        decision='monolithic joint scenes';kept={}
        for scene,s in joint.scenes().items():
            label='joint-'+scene;records[label]=runner.run('joint',scene,label,'candidate',True)
            if runner.canonical(records[label]['scenario'])!=runner.canonical(asdict(s)):raise ValueError('frozen scene identity')
            if not records[label]['trajectory_complete']:
                errors[scene]='trajectory incomplete; contrasts requiring this scene not measured';continue
            raw=np.loadtxt(WORK/(label+'.txt'),skiprows=1,ndmin=2)
            try:
                m=joint.c.measurement(raw,s);measurements[scene]=m
                if max(m['timing_balance_max_c'],m['output_balance_max_c'])>joint.GATES['charge_c']:errors[scene]='charge balance rejected'
                kept[scene]=raw
            except Exception as e:errors[scene]=str(e)
        ss=joint.scenes()
        for a,b in joint.PAIRS:
            key=a+'--'+b
            if a not in kept or b not in kept:comparisons[key]=dict(measured=False,passed=False,reason='required scene incomplete');continue
            try:comparisons[key]=dict(measured=True,passed=True,**joint.contrast(kept[a],kept[b],ss[a],ss[b]))
            except Exception as e:comparisons[key]=dict(measured=True,passed=False,error=str(e))
        admitted=not errors and len(measurements)==4 and all(x['passed'] for x in comparisons.values())
        decision='monolithic joint admitted locally' if admitted else 'monolithic joint rejected'
    finally:
        admitted=decision=='monolithic joint admitted locally'
        report=dict(schema='rf-d/union-refine-bank/v1',records=records,disabled_identity=identity,active_control=control,
            measurements=measurements,comparisons=comparisons,errors=errors,decision=decision,joint_admitted_locally=admitted,
            gates=joint.GATES,wrapper_sha256=before,wrapper_sha256_after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
            prior_admission_sha256=vco.sha(ROOT/'evidence/voice_refine_validation01.json'),
            protocol_sha256=vco.sha(ROOT/'docs/VOZ_REFINAMIENTO_UNION_PROTOCOLO.md'),measured_solves=len(records),
            physical_fidelity=False,real_time=False,new_audio=False)
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
        print('monolithic refinement:',decision,'control:',None if control is None else control['passed'],flush=True)

if __name__=='__main__':main()
