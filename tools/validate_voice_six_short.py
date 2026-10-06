"""Audit exact decks, pinned binaries and complete monolithic admission gates."""
from dataclasses import asdict
import json,sys
from pathlib import Path
import numpy as np
import voice_six_runner as runner
import voice_six_probe as probe
import voice_six_build as build
import voice_union_refine_metrics as metrics
import loudness_voice_probes as joint
import vco1_circuit_reference as vco

ROOT=vco.ROOT;WORK=runner.WORK

def main():
    output=ROOT/'evidence/voice_six_short_validation01.json'
    if output.exists():raise ValueError('preserve audit')
    compiled_path=ROOT/'evidence/voice_six_build_validation01.json';compiled=vco.read(compiled_path)
    if not compiled['passed'] or compiled['build_sha256']!=vco.sha(ROOT/'evidence/voice_six_build01.json'):raise ValueError('audited six build required')
    for n,h in compiled['source_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('compiled audit input changed')
    source_reports=compiled['inherited_build09']
    path=ROOT/'evidence/voice_six_short_runs01.json';bank=vco.read(path)
    if bank['build_sha256']!=compiled['build_sha256'] or bank['protocol_sha256']!=vco.sha(ROOT/build.PROTOCOL) or bank['supplement_sha256']!=vco.sha(ROOT/probe.SUPPLEMENT) or bank['gates']!=joint.GATES or bank['published_corrections']!=6:raise ValueError('protocol scope')
    ref=probe.reference()
    if runner.canonical(ref)!=runner.canonical(bank['reference']):raise ValueError('inherited reference identity')
    resource=probe.resources(ref)
    stored=vco.read(ROOT/'evidence/voice_six_short_preflight01.json')
    if runner.canonical(stored)!=runner.canonical(bank['resource_preflight']) or any(stored[k]!=resource[k] for k in resource if k not in ('available_free_bytes','passed')) or not stored['passed'] or stored['available_free_bytes']<stored['required_free_bytes']:raise ValueError('resource preflight arithmetic')
    shadowp=ROOT/'evidence/voice_full_note_shadow_analysis01.json';replayp=ROOT/'evidence/voice_full_note_shadow_analysis_validation01.json'
    if bank['prerequisite_shadow_sha256']!=vco.sha(shadowp) or bank['prerequisite_shadow_replay_sha256']!=vco.sha(replayp) or not vco.read(shadowp)['six_correction_gate_passed']:raise ValueError('scratch gate binding')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after']:raise ValueError('wrapper changed during solve')
    for name,digest in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('measured helper changed')
    raw={'nominal-original':np.loadtxt(ROOT/ref['raw_path'],skiprows=1,ndmin=2)};coverage={'nominal-original':True};rows={};public=[];historical_divergences={}
    original_info=runner.clock_info(raw['nominal-original'],runner.frozen('nominal','nominal500')['vectors'],.04,.5e-6)
    if original_info['rows']!=218786 or not original_info['endpoint_complete'] or not original_info['max_step_passed']:raise ValueError('original coverage')
    run_helpers=[Path(runner.__file__),Path(build.__file__),Path(runner.prior.__file__),ROOT/'tools/vco1_circuit_reference.py',ROOT/'tools/validate_loudness_board4_bank.py']
    expected_helpers={p.relative_to(ROOT).as_posix():vco.sha(p) for p in run_helpers}
    libraries=[build.WORK/'init02/spinit',build.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm',Path('C:/msys64/ucrt64/bin/libwinpthread-1.dll'),Path('C:/msys64/ucrt64/bin/libstdc++-6.dll'),Path('C:/msys64/ucrt64/bin/libgcc_s_seh-1.dll')]
    expected_runtime={(p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()):vco.sha(p) for p in libraries}
    for label,r in bank['records'].items():
        expected_kind='joint' if label.startswith('joint-') else 'nominal'
        expected_scene=label.removeprefix('joint-') if expected_kind=='joint' else 'nominal500'
        if label not in ('nominal-off','nominal-on',*('joint-'+n for n in joint.scenes())) or r['label']!=label or r['kind']!=expected_kind or r['scene']!=expected_scene:raise ValueError('fixed run identity')
        if runner.canonical(vco.read(WORK/(label+'.json')))!=runner.canonical(r):raise ValueError('receipt identity')
        source=runner.frozen(r['kind'],r['scene'])
        if source['archive_sha256']!=r['archive_sha256'] or runner.canonical(source['original_receipt'])!=runner.canonical(r['original_receipt']):raise ValueError('historical bank identity')
        for key in ('archive','vectors','historical_source_modes','current_source_sha256'):
            if runner.canonical(source[key])!=runner.canonical(r[key]):raise ValueError('historical source scope')
        if runner.canonical(r['scenario'])!=runner.canonical(source['original_receipt']['scenario']):raise ValueError('fixed scenario')
        marker=('wrdata '+source['original_export']+' ').encode()
        expected=source['deck'].read_bytes().replace(marker,('wrdata '+(WORK/(label+'.txt')).as_posix()+' ').encode(),1)
        if (WORK/(label+'.cir')).read_bytes()!=expected or vco.sha(WORK/(label+'.cir'))!=r['deck_sha256']:raise ValueError('unchanged physical deck')
        for key in ('current_source_sha256','helper_sha256','runtime_sha256'):
            if r[key]!=r[key+'_after']:raise ValueError('run inputs changed')
            for name,digest in r[key].items():
                p=Path(name) if Path(name).is_absolute() else ROOT/name
                if vco.sha(p)!=digest:raise ValueError('input identity')
        if r['helper_sha256']!=expected_helpers or r['runtime_sha256']!=expected_runtime:raise ValueError('complete helper/runtime scope')
        executable=ROOT/r['executable_path']
        if vco.sha(executable)!=r['executable_sha256'] or r['executable_sha256']!=r['executable_sha256_after']:raise ValueError('binary identity')
        pinned=compiled['executable_sha256']
        if r['executable_sha256']!=pinned:raise ValueError('binary scope')
        if executable!=build.WORK/'bin/candidate.exe' or r['command']!=[str(executable),'-n','-b',str(WORK/(label+'.cir'))]:raise ValueError('pinned launch command')
        if r['wall_limit_s']!=900:raise ValueError('frozen process budget')
        log_path=WORK/(label+'.log');log=log_path.read_text(encoding='utf-8')
        if vco.sha(log_path)!=r['log_sha256']:raise ValueError('log identity')
        enabled=label=='nominal-on' or label.startswith('joint-')
        if enabled!=r['refinement_enabled']:raise ValueError('flag activation scope')
        status=runner.log_status(log,enabled)
        for k,v in status.items():
            if r[k]!=v:raise ValueError('explicit six activation/failure receipt')
        if r['controlled_environment']!={f:('1' if f=='RF_D_LINEAR_REFINE' and enabled else None) for f in runner.FLAGS}:raise ValueError('controlled environment')
        if r['published_corrections']!=6 or r['build_sha256']!=compiled['build_sha256'] or r['compiled_source_sha256']!=r['compiled_source_sha256_after']:raise ValueError('compiled source scope')
        if r['compiled_source_sha256']!={build.NAME:vco.sha(build.TREE/build.NAME)}:raise ValueError('complete compiled source scope')
        for n,h in r['compiled_source_sha256'].items():
            if vco.sha(build.TREE/n)!=h:raise ValueError('compiled source bytes')
        failed=any(s in log.lower() for s in ('aborted','timestep too small','error:','rfrefine,error,'))
        complete=False;export_error=None
        if 'raw_export_sha256' in r:
            raw_path=WORK/(label+'.txt')
            if vco.sha(raw_path)!=r['raw_export_sha256']:raise ValueError('export identity')
            if raw_path.stat().st_size!=r['raw_export_bytes']:raise ValueError('export size')
            info={}
            try:
                a=np.loadtxt(raw_path,skiprows=1,ndmin=2);clock=r['scenario']['oscillator'] if r['kind']=='nominal' else r['scenario']['board']['oscillator']
                info=runner.clock_info(a,r['vectors'],clock['duration_s'],clock['max_step_s']);rows[label]=len(a);raw[label]=a
            except Exception as e:export_error=str(e)
            if export_error!=r.get('export_error'):raise ValueError('invalid export receipt')
            for name,value in info.items():
                if r[name]!=value:raise ValueError('clock receipt mismatch')
            complete=bool(info.get('endpoint_complete') and info.get('max_step_passed') and status['activation_gate_passed'] and not r.get('launch_error') and not r.get('timeout') and r.get('exit_code')==0)
        if bool(complete)!=r['trajectory_complete'] or failed!=r['solver_failure_reported']:raise ValueError('complete trajectory receipt mismatch')
        coverage[label]=bool(complete)
        for name,digest in source['current_source_sha256'].items():
            old=r['original_receipt']['source_sha256'][name]
            if digest!=old:historical_divergences[name]=dict(historical_sha256=old,current_sha256=digest,scope='frozen deck reused; current helper used only for measurements',historical_git_commit=r['original_receipt']['git_commit'])
        public.append(dict(label=label,rows=rows.get(label),trajectory_complete=bool(complete),last_clock_s=r.get('last_clock_s'),receipt_sha256=vco.sha(WORK/(label+'.json'))))
    vectors=runner.frozen('nominal','nominal500')['vectors']
    identity=metrics.exact(raw['nominal-original'],raw['nominal-off'],vectors) if coverage.get('nominal-off') else None
    if identity!=bank['disabled_identity']:raise ValueError('disabled identity replay')
    control=None
    if coverage.get('nominal-on'):control=metrics.control(raw['nominal-on'],raw['nominal-original'],vectors)
    if control!=bank['active_control']:raise ValueError('active nominal control replay')
    if not (identity and identity['passed'] and coverage['nominal-original'] and coverage['nominal-off']) and 'nominal-on' in bank['records']:raise ValueError('control measured before identity gate')
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
    expected='six short admitted locally' if admitted else ('disabled identity rejected' if not identity or not identity['passed'] else 'active control rejected' if not control or not control['passed'] else 'six short rejected')
    if bank['decision']!=expected or bank['new_spice_solves']!=sum(r['process_started'] for r in bank['records'].values()) or bank['inherited_reference_solves']!=1:raise ValueError('decision/count scope')
    helpers=[Path(__file__),Path(probe.__file__),Path(runner.__file__),Path(metrics.__file__),Path(joint.__file__),ROOT/'tools/loudness_voice_circuit.py',ROOT/'tools/validate_voice_refine.py']
    report=dict(schema='rf-d/active-six-short-validation/v1',passed=True,source_reports=source_reports,records=bank['records'],records_summary=public,
        bank_sha256=vco.sha(path),disabled_identity=identity,active_control=control,measurements=measurements,comparisons=comparisons,
        errors=errors,decision=bank['decision'],joint_admitted_locally=admitted,new_spice_solves=bank['new_spice_solves'],inherited_reference_solves=1,build_audit_sha256=vco.sha(compiled_path),new_solves_during_validation=0,
        historical_source_divergences=historical_divergences,analysis_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
        audit_environment=dict(python_version=sys.version,python_executable=sys.executable,numpy_version=np.__version__),
        old_port_iteration_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('active six short audit:',bank['decision'],'joint locally admitted:',admitted,flush=True)

if __name__=='__main__':main()
