"""Replay long-note provenance and gates, including preserved partial exports."""
from dataclasses import asdict
import json,math,sys
from pathlib import Path
import numpy as np
import voice_full_note as note
import voice_full_note_runner as runner
import vco1_circuit_reference as vco
from validate_voice_refine import sources

ROOT=vco.ROOT

def main():
    output=ROOT/'evidence/voice_full_note_validation01.json'
    if output.exists():raise ValueError('preserve long audit')
    path=ROOT/'evidence/voice_full_note_runs01.json';bank=vco.read(path)
    prior=vco.read(ROOT/'evidence/voice_union_refine_validation01.json');source_reports=sources()
    if not prior['passed'] or not prior['joint_admitted_locally'] or source_reports!=prior['source_reports']:raise ValueError('admitted short solver source identity')
    resource=vco.read(ROOT/'evidence/voice_full_note_preflight01.json')
    if note.prior.canonical(resource)!=note.prior.canonical(bank['resource_preflight']):raise ValueError('resource receipt identity')
    if resource['short_bank_sha256']!=vco.sha(ROOT/'evidence/voice_union_refine_runs01.json') or resource['short_audit_sha256']!=vco.sha(ROOT/'evidence/voice_union_refine_validation01.json'):raise ValueError('short bank identity')
    short=vco.read(ROOT/'evidence/voice_union_refine_runs01.json');estimate={}
    for name in note.scenes():
        r=short['records']['joint-'+name];p=note.prior.WORK/('joint-'+name+'.txt')
        if vco.sha(p)!=r['raw_export_sha256']:raise ValueError('short export changed')
        estimate[name]=dict(short_rows=r['rows'],short_export_bytes=p.stat().st_size,duration_ratio=8.75,
            estimated_long_rows=math.ceil(r['rows']*8.75),estimated_long_export_bytes=math.ceil(p.stat().st_size*8.75),short_wall_s=r['wall_s'])
    required=sum(x['estimated_long_export_bytes'] for x in estimate.values())+2*1024**3
    if resource['estimates']!=estimate or resource['required_free_bytes']!=required or resource['margin_bytes']!=2*1024**3 or not resource['passed'] or resource['available_free_bytes']<required or resource['processes']!=4 or resource['wall_limit_s_per_process']!=7200:raise ValueError('preflight arithmetic/scope')
    if bank['protocol_sha256']!=vco.sha(ROOT/note.PROTOCOL) or resource['protocol_sha256']!=bank['protocol_sha256'] or bank['gates']!=note.GATES or note.prior.canonical(bank['window_spans_s'])!=note.prior.canonical(note.WINDOWS):raise ValueError('frozen long protocol')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after']:raise ValueError('wrapper changed during runs')
    for name,digest in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('measured helper changed')
    if set(bank['records'])!=set(note.scenes()):raise ValueError('all four long receipts required')
    raw={};coverage={};summary=[]
    for name in note.scenes():
        r=bank['records'][name];work=note.WORK
        if note.prior.canonical(vco.read(work/(name+'.json')))!=note.prior.canonical(r):raise ValueError('private/public long receipt')
        source=note.prior.frozen('joint',name);s=note.scenes()[name]
        expected,patch=note.patch(source['deck'].read_bytes(),name,source['original_export'],(work/(name+'.txt')).as_posix())
        if (work/(name+'.cir')).read_bytes()!=expected or vco.sha(work/(name+'.cir'))!=r['deck_sha256'] or note.prior.canonical(patch)!=note.prior.canonical(r['patch']):raise ValueError('only declared deck anchors may change')
        expected_sources=dict(original_deck_path=source['deck'].relative_to(ROOT).as_posix(),original_deck_sha256=vco.sha(source['deck']),
            archive=source['archive'],archive_sha256=source['archive_sha256'],historical_commit=source['original_receipt']['git_commit'],
            historical_source_sha256=source['original_receipt']['source_sha256'],historical_source_modes=source['historical_source_modes'])
        for key,value in expected_sources.items():
            if r[key]!=value:raise ValueError('historical provenance mismatch')
        if note.prior.canonical(r['scenario'])!=note.prior.canonical(asdict(s)) or r['vectors']!=s.vectors:raise ValueError('long scene/vector identity')
        for key in ('current_source_sha256','helper_sha256','runtime_sha256'):
            if r[key]!=r[key+'_after']:raise ValueError('run inputs changed')
            for p,digest in r[key].items():
                if vco.sha(Path(p) if Path(p).is_absolute() else ROOT/p)!=digest:raise ValueError('run input current bytes')
        exe=ROOT/r['executable_path']
        if vco.sha(exe)!=note.prior.BINARIES['candidate'][2] or r['executable_sha256']!=vco.sha(exe) or r['executable_sha256_after']!=vco.sha(exe) or r['wall_limit_s']!=7200 or not r['refinement_enabled']:raise ValueError('pinned candidate and budget')
        log_path=work/(name+'.log');log=log_path.read_text(encoding='utf-8',errors='replace')
        if vco.sha(log_path)!=r['log_sha256']:raise ValueError('log identity')
        active='RFREFINE,active,three-corrections,pair-fma,all-real-NI' in log
        failed=any(x in log.lower() for x in ('aborted','timestep too small','error:','rfrefine,error,'))
        if active!=r['refinement_activation_confirmed'] or failed!=r['solver_failure_reported']:raise ValueError('activation/failure receipt')
        if any(x in log for x in ('RFMATRIX,','RFREFINE,replay,','RFTRACE,','RFLTRACE,','RFKTRACE,','RF741REDUCE,')):raise ValueError('old observers/replay disabled')
        info={};export_error=None
        if 'raw_export_sha256' in r:
            p=work/(name+'.txt')
            if vco.sha(p)!=r['raw_export_sha256'] or p.stat().st_size!=r['raw_export_bytes']:raise ValueError('raw export identity')
            try:
                a=np.loadtxt(p,skiprows=1,ndmin=2);info=note.prior.clock_info(a,s.vectors,.35,s.oscillator.max_step_s);raw[name]=a
            except Exception as e:export_error=str(e)
            for key,value in info.items():
                if r[key]!=value:raise ValueError('clock receipt replay')
            if export_error!=r.get('export_error'):raise ValueError('partial/invalid export receipt')
        complete=bool(info.get('endpoint_complete') and info.get('max_step_passed') and active and not failed and not r.get('timeout') and not r.get('launch_error') and r.get('exit_code')==0)
        if complete!=r['trajectory_complete']:raise ValueError('long coverage gate')
        coverage[name]=complete
        summary.append(dict(scene=name,rows=r.get('rows'),last_clock_s=r.get('last_clock_s'),trajectory_complete=complete,
            solver_failure_reported=failed,timeout=bool(r.get('timeout')),receipt_sha256=vco.sha(work/(name+'.json'))))
    ss=note.scenes();measurements={};errors={};comparisons={}
    for name,s in ss.items():
        if not coverage[name]:errors[name]='trajectory incomplete; dependent comparisons not measured';continue
        try:
            m=note.measurement(raw[name],s);measurements[name]=m
            if max(m['timing_balance_max_c'],m['output_balance_max_c'])>note.GATES['charge_c']:errors[name]='charge balance rejected'
        except Exception as e:errors[name]='measurement: '+str(e)
    for a,b in note.short.PAIRS:
        comparisons[a+'--'+b]=note.contrast(raw[a],raw[b],ss[a],ss[b]) if a in measurements and b in measurements else dict(measured=False,passed=False,reason='required complete scene missing')
    if note.prior.canonical(measurements)!=note.prior.canonical(bank['measurements']) or comparisons!=bank['comparisons'] or errors!=bank['errors']:raise ValueError('long measurements/gates differ')
    admitted=len(measurements)==4 and not errors and all(c['passed'] for c in comparisons.values())
    if admitted!=bank['long_note_admitted_locally'] or bank['decision']!=('long note admitted locally' if admitted else 'long note rejected'):raise ValueError('bank decision')
    helpers=[Path(__file__),Path(note.__file__),Path(runner.__file__),ROOT/'tools/validate_voice_refine.py']
    report=dict(schema='rf-d/full-note-validation/v1',passed=True,bank_sha256=vco.sha(path),resource_preflight_sha256=vco.sha(ROOT/'evidence/voice_full_note_preflight01.json'),
        source_reports=source_reports,records_summary=summary,measurements=measurements,comparisons=comparisons,errors=errors,
        decision=bank['decision'],long_note_admitted_locally=admitted,measured_solves=sum(r['process_started'] for r in bank['records'].values()),
        new_solves_during_validation=0,analysis_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
        audit_environment=dict(python_version=sys.version,numpy_version=np.__version__),physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('long-note audit:',report['decision'],flush=True)

if __name__=='__main__':main()
