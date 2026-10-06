"""Inherited original control, new disabled/active controls, then four short scenes."""
from dataclasses import asdict
import json,shutil
from pathlib import Path
import numpy as np
import voice_six_runner as runner
import voice_six_build as build
import voice_union_refine_runner as prior
import voice_union_refine_metrics as metrics
import loudness_voice_probes as joint
import vco1_circuit_reference as vco

ROOT=vco.ROOT;WORK=runner.WORK
SUPPLEMENT='docs/VOZ_SEIS_CONTROLES_ADAPTACION_PROTOCOLO.md'

def write(path,x):path.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')

def reference():
    p=prior.WORK/'nominal-original.json';r=vco.read(p)
    bank=vco.read(ROOT/'evidence/voice_union_refine_runs01.json')
    audit=vco.read(ROOT/'evidence/voice_union_refine_validation01.json')
    if not audit['passed'] or not audit['joint_admitted_locally'] or audit['bank_sha256']!=vco.sha(ROOT/'evidence/voice_union_refine_runs01.json') or prior.canonical(r)!=prior.canonical(bank['records']['nominal-original']):raise ValueError('admitted original reference required')
    for key in ('current_source_sha256','helper_sha256','runtime_sha256'):
        if r[key]!=r[key+'_after']:raise ValueError('reference source stability')
        for n,h in r[key].items():
            if vco.sha(Path(n) if Path(n).is_absolute() else ROOT/n)!=h:raise ValueError('reference input changed')
    exe=ROOT/r['executable_path']
    if vco.sha(exe)!=prior.BINARIES['original'][2] or r['executable_sha256']!=vco.sha(exe) or not r['trajectory_complete']:raise ValueError('original pinned coverage')
    for ext,key in (('txt','raw_export_sha256'),('cir','deck_sha256'),('log','log_sha256')):
        if vco.sha(p.with_suffix('.'+ext))!=r[key]:raise ValueError('original reference bytes')
    return dict(receipt_path=p.relative_to(ROOT).as_posix(),receipt_sha256=vco.sha(p),
        raw_path=p.with_suffix('.txt').relative_to(ROOT).as_posix(),raw_sha256=r['raw_export_sha256'],
        source_audit_sha256=vco.sha(ROOT/'evidence/voice_union_refine_validation01.json'),
        original_executable_sha256=vco.sha(exe),new_spice_solves=0,execution='inherited')

def resources(ref):
    bank=vco.read(ROOT/'evidence/voice_union_refine_runs01.json');est={}
    for label in ('nominal-off','nominal-on'):
        est[label]=(ROOT/ref['raw_path']).stat().st_size
    for name in joint.scenes():
        r=bank['records']['joint-'+name];p=prior.WORK/('joint-'+name+'.txt')
        if vco.sha(p)!=r['raw_export_sha256']:raise ValueError('short estimate source changed')
        est['joint-'+name]=p.stat().st_size
    available=shutil.disk_usage(ROOT).free;required=sum(est.values())+2*1024**3
    return dict(passed=available>=required,estimated_export_bytes=est,required_free_bytes=required,
        available_free_bytes=available,margin_bytes=2*1024**3,estimates_are_not_bounds=True,
        wall_limit_s_per_process=900,new_spice_solves=0)

def main():
    output=ROOT/'evidence/voice_six_short_runs01.json'
    if output.exists() or WORK.exists():raise ValueError('preserve six short bank')
    compiled,_=runner.candidate()
    shadowp=ROOT/'evidence/voice_full_note_shadow_analysis01.json';shadow=vco.read(shadowp)
    replayp=ROOT/'evidence/voice_full_note_shadow_analysis_validation01.json';replay=vco.read(replayp)
    if not shadow['passed'] or not shadow['six_correction_gate_passed'] or not replay['passed'] or replay['analysis_sha256']!=vco.sha(shadowp):raise ValueError('scratch gate prerequisite')
    ref=reference();resource=resources(ref);write(ROOT/'evidence/voice_six_short_preflight01.json',resource)
    if not resource['passed']:raise ValueError('short export estimate plus margin unavailable')
    helpers=(Path(__file__),Path(runner.__file__),Path(metrics.__file__),Path(joint.__file__),Path(joint.c.__file__))
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/active-six-short-bank/v1',reference=ref,records={},disabled_identity=None,active_control=None,
        measurements={},comparisons={},errors={},gates=joint.GATES,decision='measurements pending',joint_admitted_locally=False,
        wrapper_sha256=before,build_sha256=vco.sha(build.WORK/'build.json'),protocol_sha256=vco.sha(ROOT/build.PROTOCOL),
        supplement_sha256=vco.sha(ROOT/SUPPLEMENT),resource_preflight=resource,
        prerequisite_shadow_sha256=vco.sha(shadowp),prerequisite_shadow_replay_sha256=vco.sha(replayp),
        physical_fidelity=False,real_time=False,new_audio=False,published_corrections=6)
    records=report['records'];measurements=report['measurements'];errors=report['errors'];comparisons=report['comparisons']
    try:
        a=np.loadtxt(ROOT/ref['raw_path'],skiprows=1,ndmin=2);vectors=runner.frozen('nominal','nominal500')['vectors']
        r=runner.run('nominal','nominal500','nominal-off');records['nominal-off']=r;write(output,report)
        report['decision']='disabled identity rejected'
        if not r['trajectory_complete']:return
        b=np.loadtxt(WORK/'nominal-off.txt',skiprows=1,ndmin=2);report['disabled_identity']=metrics.exact(a,b,vectors)
        if not report['disabled_identity']['passed']:return
        report['decision']='active control pending'
        r=runner.run('nominal','nominal500','nominal-on',True);records['nominal-on']=r;write(output,report)
        report['decision']='active control rejected'
        if not r['trajectory_complete']:return
        c=np.loadtxt(WORK/'nominal-on.txt',skiprows=1,ndmin=2);report['active_control']=metrics.control(c,a,vectors)
        if not report['active_control']['passed']:return
        report['decision']='joint scenes pending'
        kept={};ss=joint.scenes()
        for name,s in ss.items():
            label='joint-'+name;r=runner.run('joint',name,label,True);records[label]=r;write(output,report)
            if runner.canonical(r['scenario'])!=runner.canonical(asdict(s)):raise ValueError('frozen short scene identity')
            if not r['trajectory_complete']:errors[name]='trajectory incomplete; contrasts requiring this scene not measured';continue
            raw=np.loadtxt(WORK/(label+'.txt'),skiprows=1,ndmin=2)
            try:
                m=joint.c.measurement(raw,s);measurements[name]=m;kept[name]=raw
                if max(m['timing_balance_max_c'],m['output_balance_max_c'])>joint.GATES['charge_c']:errors[name]='charge balance rejected'
            except Exception as e:errors[name]=str(e)
        for a,b in joint.PAIRS:
            key=a+'--'+b
            if a not in kept or b not in kept:comparisons[key]=dict(measured=False,passed=False,reason='required scene incomplete');continue
            try:comparisons[key]=dict(measured=True,passed=True,**joint.contrast(kept[a],kept[b],ss[a],ss[b]))
            except Exception as e:comparisons[key]=dict(measured=True,passed=False,error=str(e))
        report['joint_admitted_locally']=not errors and len(measurements)==4 and all(c['passed'] for c in comparisons.values())
        report['decision']='six short admitted locally' if report['joint_admitted_locally'] else 'six short rejected'
    except Exception as e:
        errors['probe']=str(e);report['decision']='six short rejected'
    finally:
        report['wrapper_sha256_after']={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
        if before!=report['wrapper_sha256_after']:errors['sources']='measured wrapper changed';report['joint_admitted_locally']=False;report['decision']='six short rejected'
        report['new_spice_solves']=sum(r['process_started'] for r in records.values());report['inherited_reference_solves']=1
        write(output,report);print('six short bank:',report['decision'],flush=True)

if __name__=='__main__':main()
