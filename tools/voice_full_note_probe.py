"""Four independent fresh-DC long notes, resource preflight and fixed gates."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,math,os,shutil,sys
from pathlib import Path
import numpy as np
import voice_full_note as note
import voice_full_note_runner as runner
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def write(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8',newline='\n')

def preflight():
    output=ROOT/'evidence/voice_full_note_preflight01.json'
    if output.exists():raise ValueError('preserve resource preflight')
    bank_path=ROOT/'evidence/voice_union_refine_runs01.json';audit_path=ROOT/'evidence/voice_union_refine_validation01.json'
    bank=vco.read(bank_path);audit=vco.read(audit_path);estimate={}
    if not audit['passed'] or not audit['joint_admitted_locally'] or audit['bank_sha256']!=vco.sha(bank_path):raise ValueError('admitted short bank required')
    for source in (bank['wrapper_sha256'],audit['analysis_source_sha256']):
        for name,digest in source.items():
            if vco.sha(ROOT/name)!=digest:raise ValueError('short source changed')
    for name in note.scenes():
        r=bank['records']['joint-'+name];path=note.prior.WORK/('joint-'+name+'.txt')
        if not r['trajectory_complete'] or vco.sha(path)!=r['raw_export_sha256']:raise ValueError('short export identity')
        estimate[name]=dict(short_rows=r['rows'],short_export_bytes=path.stat().st_size,
            duration_ratio=8.75,estimated_long_rows=math.ceil(r['rows']*8.75),
            estimated_long_export_bytes=math.ceil(path.stat().st_size*8.75),short_wall_s=r['wall_s'])
    expected=sum(x['estimated_long_export_bytes'] for x in estimate.values());margin=2*1024**3
    free=shutil.disk_usage(ROOT).free
    report=dict(schema='rf-d/full-note-preflight/v1',passed=free>=expected+margin,estimates=estimate,
        estimated_exports_bytes=expected,margin_bytes=margin,required_free_bytes=expected+margin,available_free_bytes=free,
        estimates_are_not_bounds=True,processes=4,logical_cpus=os.cpu_count(),wall_limit_s_per_process=7200,
        short_bank_sha256=vco.sha(bank_path),short_audit_sha256=vco.sha(audit_path),
        protocol_sha256=vco.sha(ROOT/note.PROTOCOL),new_solves=0,python_version=sys.version,numpy_version=np.__version__)
    write(output,report)
    if not report['passed']:raise ValueError('long exports plus 2 GiB margin unavailable')
    return report

def main():
    output=ROOT/'evidence/voice_full_note_runs01.json'
    if output.exists() or note.WORK.exists():raise ValueError('preserve long bank')
    resource=preflight();helpers=[Path(__file__),Path(note.__file__),Path(runner.__file__)]
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/full-note-bank/v1',records={},measurements={},comparisons={},errors={},
        gates=note.GATES,window_spans_s=note.WINDOWS,wrapper_sha256=before,resource_preflight=resource,
        protocol_sha256=vco.sha(ROOT/note.PROTOCOL),long_note_admitted_locally=False,new_audio=False,
        decision='measurements pending',physical_fidelity=False,real_time=False)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures={pool.submit(runner.run,name):name for name in note.scenes()}
            for future in as_completed(futures):
                name=futures[future]
                try:report['records'][name]=future.result()
                except Exception as e:report['errors'][name]='runner exception: '+str(e)
                write(output,report)
        ss=note.scenes()
        for name in ss:
            r=report['records'].get(name)
            if not r or not r['trajectory_complete']:
                report['errors'].setdefault(name,'trajectory incomplete; dependent comparisons not measured');continue
            try:
                raw=np.loadtxt(note.WORK/(name+'.txt'),skiprows=1,ndmin=2);m=note.measurement(raw,ss[name])
                report['measurements'][name]=m
                if max(m['timing_balance_max_c'],m['output_balance_max_c'])>note.GATES['charge_c']:report['errors'][name]='charge balance rejected'
            except Exception as e:report['errors'][name]='measurement: '+str(e)
        for a,b in note.short.PAIRS:
            if a not in report['measurements'] or b not in report['measurements']:
                report['comparisons'][a+'--'+b]=dict(measured=False,passed=False,reason='required complete scene missing');continue
            x=np.loadtxt(note.WORK/(a+'.txt'),skiprows=1,ndmin=2);y=np.loadtxt(note.WORK/(b+'.txt'),skiprows=1,ndmin=2)
            report['comparisons'][a+'--'+b]=note.contrast(x,y,ss[a],ss[b])
        report['long_note_admitted_locally']=len(report['measurements'])==4 and not report['errors'] and all(c['passed'] for c in report['comparisons'].values())
        report['decision']='long note admitted locally' if report['long_note_admitted_locally'] else 'long note rejected'
    finally:
        report['measured_solves']=sum(r['process_started'] for r in report['records'].values())
        report['wrapper_sha256_after']={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
        if before!=report['wrapper_sha256_after']:
            report['long_note_admitted_locally']=False;report['errors']['sources']='wrapper changed during runs';report['decision']='long note rejected'
        write(output,report)
    print('long-note bank:',report['decision'],flush=True)

if __name__=='__main__':main()
