"""Four independent fresh-DC six-correction notes with admitted native storage."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import math,os,shutil
from pathlib import Path
import voice_binary_runner as runner
import voice_native_raw as native
import voice_full_note as note
import voice_six_runner as six
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def estimate():
    controlp=ROOT/'evidence/voice_native_control01.json';auditp=ROOT/'evidence/voice_native_control_validation01.json'
    proof=vco.read(auditp);control=vco.read(controlp)
    if not proof['passed'] or not proof['control_admitted'] or proof['control_sha256']!=vco.sha(controlp):raise ValueError('native control audit required')
    for scope in (control['wrapper_sha256'],proof['analysis_source_sha256']):
        for n,h in scope.items():
            if vco.sha(ROOT/n)!=h:raise ValueError('native control helper changed')
    header=proof['native_layout']['header_bytes'];estimates={}
    for name,s in note.scenes().items():
        r,p=runner.source(name);rows=math.ceil(r['rows']*8.75)
        if len(s.vectors)+1!=proof['columns']:raise ValueError('same admitted scalar columns required')
        estimates[name]=dict(short_rows=r['rows'],short_receipt_sha256=vco.sha(p),duration_ratio=8.75,
            estimated_long_rows=rows,columns=len(s.vectors)+1,bytes_per_scalar=8,
            observed_header_bytes=header,estimated_long_export_bytes=rows*(len(s.vectors)+1)*8+header)
    size=sum(x['estimated_long_export_bytes'] for x in estimates.values());margin=2*1024**3;free=shutil.disk_usage(ROOT).free
    return dict(schema='rf-d/native-long-preflight/v1',passed=free>=size+margin,estimates=estimates,
        estimated_exports_bytes=size,required_free_bytes=size+margin,available_free_bytes=free,margin_bytes=margin,
        wall_limit_s_per_process=7200,processes=4,max_workers=4,logical_cpus=os.cpu_count(),estimates_are_not_bounds=True,
        control_sha256=vco.sha(controlp),control_audit_sha256=vco.sha(auditp),
        protocol_sha256=vco.sha(ROOT/runner.PROTOCOL),long_protocol_sha256=vco.sha(ROOT/note.PROTOCOL),
        helper_sha256=vco.sha(Path(__file__)),new_spice_solves=0)

def preflight():
    path=ROOT/'evidence/voice_binary_long_preflight01.json'
    if path.exists():raise ValueError('preserve native long preflight')
    report=estimate();runner.write(path,report)
    print('native long resources:',report['passed'],'required:',report['required_free_bytes'],'available:',report['available_free_bytes'],flush=True)
    return report

def main():
    output=ROOT/'evidence/voice_binary_long_runs01.json'
    if output.exists() or runner.LONG.exists():raise ValueError('preserve native long bank')
    qa_path=ROOT/'evidence/voice_native_tests01.json';qa=vco.read(qa_path)
    if not qa['passed'] or qa['new_tests_count']!=10 or not qa['control_admitted'] or qa['control_audit_sha256']!=vco.sha(ROOT/'evidence/voice_native_control_validation01.json'):raise ValueError('native parser release QA required')
    for n in ('tools/voice_native_raw.py','tools/voice_binary_runner.py',Path(__file__).relative_to(ROOT).as_posix()):
        if qa['source_sha256'][n]!=vco.sha(ROOT/n):raise ValueError('native release source changed')
    resourcep=ROOT/'evidence/voice_binary_long_preflight01.json'
    resource=vco.read(resourcep) if resourcep.exists() else preflight()
    replay=estimate()
    if any(resource[k]!=replay[k] for k in replay if k not in ('available_free_bytes','passed')) or not resource['passed'] or not replay['passed']:raise ValueError('admitted current long resources required')
    helpers=[Path(__file__),Path(runner.__file__),Path(native.__file__),Path(note.__file__)]
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    bank=dict(schema='rf-d/native-six-long-bank/v1',resource_preflight_sha256=vco.sha(resourcep),native_qa_sha256=vco.sha(qa_path),records={},measurements={},comparisons={},errors={},
        gates=note.GATES,window_spans_s=note.WINDOWS,wrapper_sha256=before,decision='measurements pending',long_note_admitted_locally=False,
        physical_fidelity=False,real_time=False,new_audio=False)
    runner.write(output,bank)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures={pool.submit(runner.run,name,True):name for name in note.scenes()}
            for future in as_completed(futures):
                name=futures[future]
                try:bank['records'][name]=future.result()
                except Exception as e:bank['errors'][name]='runner exception: '+str(e)
                runner.write(output,bank)
        scenes=note.scenes()
        for name,s in scenes.items():
            r=bank['records'].get(name)
            if not r or not r['trajectory_complete']:
                bank['errors'].setdefault(name,'trajectory incomplete; dependent comparisons not measured');continue
            try:
                a,layout=native.read(runner.LONG/(name+'.raw'),s.vectors)
                m=note.measurement(a,s);bank['measurements'][name]=m
                if max(m['timing_balance_max_c'],m['output_balance_max_c'])>note.GATES['charge_c']:bank['errors'][name]='charge balance rejected'
            except Exception as e:bank['errors'][name]='measurement: '+str(e)
        for left,right in note.short.PAIRS:
            key=left+'--'+right
            if left not in bank['measurements'] or right not in bank['measurements']:
                bank['comparisons'][key]=dict(measured=False,passed=False,reason='required complete scene missing');continue
            a,_=native.read(runner.LONG/(left+'.raw'),scenes[left].vectors);b,_=native.read(runner.LONG/(right+'.raw'),scenes[right].vectors)
            bank['comparisons'][key]=note.contrast(a,b,scenes[left],scenes[right])
        bank['long_note_admitted_locally']=len(bank['measurements'])==4 and not bank['errors'] and all(c['passed'] for c in bank['comparisons'].values())
        bank['decision']='native long note admitted locally' if bank['long_note_admitted_locally'] else 'native long note rejected'
    finally:
        bank['wrapper_sha256_after']={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
        if before!=bank['wrapper_sha256_after']:bank['errors']['sources']='measured long wrapper changed';bank['long_note_admitted_locally']=False;bank['decision']='native long note rejected'
        bank['measured_spice_solves']=sum(r['process_started'] for r in bank['records'].values())
        runner.write(output,bank)
    print('native long bank:',bank['decision'],flush=True)

if __name__=='__main__':main()
