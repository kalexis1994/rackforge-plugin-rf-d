"""Audit exact decks, pinned binaries and complete monolithic admission gates."""
from dataclasses import asdict
import json,sys
from pathlib import Path
import numpy as np
import voice_union_refine_runner as runner
import voice_union_refine_metrics as metrics
import loudness_voice_probes as joint
import vco1_circuit_reference as vco
from validate_voice_refine import sources

ROOT=vco.ROOT;WORK=runner.WORK

def main():
    output=ROOT/'evidence/voice_union_refine_validation01.json'
    if output.exists():raise ValueError('preserve audit')
    source_reports=sources();prior_path=ROOT/'evidence/voice_refine_validation01.json';prior=vco.read(prior_path)
    if not prior['passed'] or not prior['candidate_admitted_locally'] or source_reports!=prior['source_reports']:raise ValueError('frozen solver source identity')
    path=ROOT/'evidence/voice_union_refine_runs01.json';bank=vco.read(path)
    if bank['prior_admission_sha256']!=vco.sha(prior_path) or bank['protocol_sha256']!=vco.sha(ROOT/'docs/VOZ_REFINAMIENTO_UNION_PROTOCOLO.md') or bank['gates']!=joint.GATES:raise ValueError('protocol scope')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after']:raise ValueError('wrapper changed during solve')
    for name,digest in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('measured helper changed')
    raw={};coverage={};rows={};public=[];historical_divergences={}
    for label,r in bank['records'].items():
        if runner.canonical(vco.read(WORK/(label+'.json')))!=runner.canonical(r):raise ValueError('receipt identity')
        source=runner.frozen(r['kind'],r['scene'])
        if source['archive_sha256']!=r['archive_sha256'] or runner.canonical(source['original_receipt'])!=runner.canonical(r['original_receipt']):raise ValueError('historical bank identity')
        marker=('wrdata '+source['original_export']+' ').encode()
        expected=source['deck'].read_bytes().replace(marker,('wrdata '+(WORK/(label+'.txt')).as_posix()+' ').encode(),1)
        if (WORK/(label+'.cir')).read_bytes()!=expected or vco.sha(WORK/(label+'.cir'))!=r['deck_sha256']:raise ValueError('unchanged physical deck')
        for key in ('current_source_sha256','helper_sha256','runtime_sha256'):
            if r[key]!=r[key+'_after']:raise ValueError('run inputs changed')
            for name,digest in r[key].items():
                p=Path(name) if Path(name).is_absolute() else ROOT/name
                if vco.sha(p)!=digest:raise ValueError('input identity')
        executable=ROOT/r['executable_path']
        if vco.sha(executable)!=r['executable_sha256'] or r['executable_sha256']!=r['executable_sha256_after']:raise ValueError('binary identity')
        pinned=runner.BINARIES['original' if label=='nominal-original' else 'candidate'][2]
        if r['executable_sha256']!=pinned:raise ValueError('binary scope')
        if r['wall_limit_s']!=900:raise ValueError('frozen process budget')
        log_path=WORK/(label+'.log');log=log_path.read_text(encoding='utf-8')
        if vco.sha(log_path)!=r['log_sha256']:raise ValueError('log identity')
        enabled=label=='nominal-on' or label.startswith('joint-')
        if enabled!=r['refinement_enabled'] or enabled!=('RFREFINE,active,three-corrections,pair-fma,all-real-NI' in log):raise ValueError('flag activation scope')
        if any(s in log for s in ('RFMATRIX,','RFREFINE,replay,','RFTRACE,','RFLTRACE,','RFKTRACE,','RF741REDUCE,')):raise ValueError('old instrumentation disabled')
        failed=any(s in log.lower() for s in ('aborted','timestep too small','error:','rfrefine,error,'))
        complete=False
        if 'raw_export_sha256' in r:
            raw_path=WORK/(label+'.txt')
            if vco.sha(raw_path)!=r['raw_export_sha256']:raise ValueError('export identity')
            a=np.loadtxt(raw_path,skiprows=1,ndmin=2);clock=r['scenario']['oscillator'] if r['kind']=='nominal' else r['scenario']['board']['oscillator']
            info=runner.clock_info(a,r['vectors'],clock['duration_s'],clock['max_step_s']);rows[label]=len(a);raw[label]=a
            for name,value in info.items():
                if r[name]!=value:raise ValueError('clock receipt mismatch')
            complete=info['endpoint_complete'] and info['max_step_passed'] and not failed and not r.get('timeout') and r.get('exit_code')==0
        if bool(complete)!=r['trajectory_complete'] or failed!=r['solver_failure_reported']:raise ValueError('complete trajectory receipt mismatch')
        coverage[label]=bool(complete)
        for name,digest in source['current_source_sha256'].items():
            old=r['original_receipt']['source_sha256'][name]
            if digest!=old:historical_divergences[name]=dict(historical_sha256=old,current_sha256=digest,scope='frozen deck reused; current helper used only for measurements',historical_git_commit=r['original_receipt']['git_commit'])
        public.append(dict(label=label,rows=rows.get(label),trajectory_complete=bool(complete),last_clock_s=r.get('last_clock_s'),receipt_sha256=vco.sha(WORK/(label+'.json'))))
    vectors=runner.frozen('nominal','nominal500')['vectors']
    identity=metrics.exact(raw['nominal-original'],raw['nominal-off'],vectors)
    if identity!=bank['disabled_identity']:raise ValueError('disabled identity replay')
    control=None
    if coverage.get('nominal-on'):control=metrics.control(raw['nominal-on'],raw['nominal-original'],vectors)
    if control!=bank['active_control']:raise ValueError('active nominal control replay')
    if not (identity['passed'] and coverage['nominal-original'] and coverage['nominal-off']) and 'nominal-on' in bank['records']:raise ValueError('control measured before identity gate')
    if (control is None or not control['passed']) and any(k.startswith('joint-') for k in bank['records']):raise ValueError('joint measured after rejected control')
    measurements={};comparisons={};errors={};ss=joint.scenes();kept={}
    for scene,s in ss.items():
        label='joint-'+scene
        if label not in bank['records']:continue
        if runner.canonical(bank['records'][label]['scenario'])!=runner.canonical(asdict(s)):raise ValueError('joint scene identity')
        if not coverage[label]:errors[scene]='trajectory incomplete; contrasts requiring this scene not measured';continue
        try:
            m=joint.c.measurement(raw[label],s);measurements[scene]=m
            if max(m['timing_balance_max_c'],m['output_balance_max_c'])>joint.GATES['charge_c']:errors[scene]='charge balance rejected'
            kept[scene]=raw[label]
        except Exception as e:errors[scene]=str(e)
    if any(k.startswith('joint-') for k in bank['records']):
        for a,b in joint.PAIRS:
            key=a+'--'+b
            if a not in kept or b not in kept:comparisons[key]=dict(measured=False,passed=False,reason='required scene incomplete');continue
            try:comparisons[key]=dict(measured=True,passed=True,**joint.contrast(kept[a],kept[b],ss[a],ss[b]))
            except Exception as e:comparisons[key]=dict(measured=True,passed=False,error=str(e))
    if runner.canonical(measurements)!=runner.canonical(bank['measurements']) or comparisons!=bank['comparisons'] or errors!=bank['errors']:raise ValueError('joint gates replay differs')
    admitted=bool(control and control['passed'] and len(measurements)==4 and not errors and all(c['passed'] for c in comparisons.values()))
    if admitted!=bank['joint_admitted_locally']:raise ValueError('admission mismatch')
    helpers=[Path(__file__),Path(metrics.__file__),Path(joint.__file__),ROOT/'tools/loudness_voice_circuit.py',ROOT/'tools/validate_voice_refine.py']
    report=dict(schema='rf-d/union-refine-validation/v1',passed=True,source_reports=source_reports,records=bank['records'],records_summary=public,
        bank_sha256=vco.sha(path),disabled_identity=identity,active_control=control,measurements=measurements,comparisons=comparisons,
        errors=errors,decision=bank['decision'],joint_admitted_locally=admitted,measured_solves=len(bank['records']),new_solves_during_validation=0,
        historical_source_divergences=historical_divergences,analysis_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
        audit_environment=dict(python_version=sys.version,python_executable=sys.executable,numpy_version=np.__version__),
        old_port_iteration_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('monolithic audit:',bank['decision'],'joint locally admitted:',admitted,flush=True)

if __name__=='__main__':main()
