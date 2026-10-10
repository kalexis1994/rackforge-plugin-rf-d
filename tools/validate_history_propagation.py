"""Protect complete lineage and admit only measured fixed-calendar windows."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_history_propagation_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    previous='evidence/voice_history_tangent_tests01.json';old=read(previous);before=read('evidence/voice_history_propagation_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous admission')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base unchanged before commit');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,d in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==d,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,d in private.items():require(sha(ROOT/n)==d,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/joint_history_propagation.rs text eol=lf\n/tools/joint_history_propagation_runner.rs text eol=lf\n','only lab attributes')
    inputs=read('evidence/voice_history_propagation_inputs01.json');require(inputs['passed'] and len(inputs['windows'])==12 and sha(ROOT/inputs['path'])==inputs['sha256'],'frozen twelve calendars');private[inputs['path']]=inputs['sha256']
    for n,d in inputs['source_sha256'].items():require(sha(ROOT/n)==d,'preparation source')
    for n,d in inputs['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'protected calendar input')
    for window in inputs['windows']:require(len(window['half_ticks'])==64 and sum(window['half_ticks'])==window['end_ticks']-window['start_ticks'],'complete contiguous window')
    native=read('evidence/voice_history_propagation_native01.json');require(native['passed'] and native['source_sha256']==native['source_sha256_after'] and native['private_used_sha256']==native['private_used_sha256_after'],'passed unchanged native')
    require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'] and not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0,'frozen physical build')
    for n,d in native['source_sha256'].items():require(sha(ROOT/n)==d,'measured native source')
    for n,d in native['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'frozen native input')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'native output');private[o['path']]=o['sha256']
    require(native['minimum_free_bytes']>=native['reserve_bytes'] and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['wall_s']<=1200,'resource margins')
    require(len(native['commands'])==2 and not native['replays'],'exact two native commands')
    for k,c in enumerate(native['commands']):require(c['exit_code']==0 and not c['administrative_stop'] and c['wall_s']<=(120 if k==0 else 900),'command resource gates')
    reference=read('evidence/voice_history_propagation_reference01.json');require(reference['passed'] and reference['source_sha256']==reference['source_sha256_after'] and reference['wall_s']<=900,'passed independent response')
    for n,d in reference['source_sha256'].items():require(sha(ROOT/n)==d,'measured checker source')
    for n,d in reference['input_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'reference input')
    counts=dict(baseline_steps=768,response_directions=6912,response_stage_coordinates=2764800,perturbed_native_step_solves=27648,baseline_selected_bit_reproductions=24,baseline_trace_bit_reproductions=768,batched_scalar_bit_coordinates=172800,negative_controls=768)
    for k,v in counts.items():require(reference[k]==v,'declared coverage '+k)
    require(len(reference['records'])==768 and len(reference['windows'])==12,'complete checker coverage')
    for i,row in enumerate(reference['records']):
        require(row['window']==i//64 and row['step']==i%64 and len(row['responses'])==9,'ordered checked stage')
        for a in row['responses']:require(a['independent']['max_ratio']<=1 and len(a['nonlinear_fd'])==2 and all(b['max_ratio']<=1 for b in a['nonlinear_fd']),'unchanged response gates')
    require(reference['fixed_calendar_windows_admitted'] and not reference['adaptive_derivative_admitted'] and not reference['period_map_admitted'] and not reference['event_time_derivative_admitted'] and reference['independent_roots']==0 and not reference['physical_fidelity'] and not reference['real_time'],'scope of admission')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');links=local_links(sorted(n for n in staged if n.endswith('.md')));names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/history-propagation-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**counts,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,fixed_calendar_windows_admitted=True,adaptive_derivative_admitted=False,period_map_admitted=False,event_time_derivative_admitted=False,independent_roots=0,physical_cards_changed=False,new_library_compile=False,new_audio=False,new_spice_processes=0,physical_fidelity=False,real_time=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=links)
def main():
    try:report=audit()
    except Exception:
        report=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_history_propagation.py').read_text())
        try:audit();report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_history_propagation_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_history_propagation_qa_failure{k:02d}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('PROPAGATION_QA',report['passed'],len(report['source_sha256']),len(report['private_input_sha256']),flush=True)
if __name__=='__main__':main()
