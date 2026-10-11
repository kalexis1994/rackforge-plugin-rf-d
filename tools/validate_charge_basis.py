"""Frozen lineage and release gate for the corrected initial charge basis."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from prepare_charge_basis import adapter
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links
OUT='evidence/voice_charge_basis_tests01.json'
COUNTS=dict(base_bit_roots=2,base_bit_steps=4,basis_columns=36,basis_entries=7848,augmented_root_count=146,augmented_rows=31828,independent_dynamic_rows=1600,independent_step_directions=72,independent_step_coordinates=28800,batch9_bit_coordinates=28800,zero_history_controls=4,injection_positive_controls=2,perturbed_native_steps=288,own_prefix_histories=144,charge_incidence_rank=18)

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    previous='evidence/voice_return_interval_tests01.json';old=read(previous);before=read('evidence/voice_charge_basis_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous QA');require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit'],'base unchanged');saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,d in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==d,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,d in private.items():require(sha(ROOT/n)==d,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/charge_basis_tail.rs text eol=lf\n/tools/joint_charge_basis_runner.rs text eol=lf\n/tools/joint_charge_basis_propagation.rs text eol=lf\n','only new caller attributes');header=(ROOT/'tools/joint_charge_corrected_runner.rs').read_text();header=header[:header.index('fn run()->Result<(),String>')]
    require((ROOT/'tools/joint_charge_basis_runner.rs').read_bytes()==(header+(ROOT/'tools/charge_basis_tail.rs').read_text()).encode() and (ROOT/'tools/joint_charge_basis_propagation.rs').read_bytes()==adapter().encode(),'unchanged conditioner and declared RHS width adaptation')
    inputs=read('evidence/voice_charge_basis_inputs01.json');require(inputs['passed'] and len(inputs['profiles'])==2 and sha(ROOT/inputs['path'])==inputs['sha256'],'frozen input');private[inputs['path']]=inputs['sha256']
    for n,d in inputs['source_sha256'].items():require(sha(ROOT/n)==d,'preparation source')
    for n,d in inputs['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'protected fixtures')
    native=read('evidence/voice_charge_basis_native01.json');require(native['passed'] and native['source_sha256']==native['source_sha256_after'] and native['private_used_sha256']==native['private_used_sha256_after'],'stable native');require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'] and not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0,'frozen library/compiler')
    for n,d in native['source_sha256'].items():require(sha(ROOT/n)==d,'native source')
    for n,d in native['private_used_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'native input')
    for o in native['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'native output');private[o['path']]=o['sha256']
    require(native['reserve_bytes']==1024**3 and native['estimated_output_bytes']==16*1024**2 and native['minimum_free_bytes']>=native['reserve_bytes'] and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['wall_s']<=760 and native['lab_stack_bytes']==33554432 and sum(o['bytes'] for o in native['outputs'])<=native['estimated_output_bytes'],'resource gates');require(len(native['commands'])==2 and not native['replays'],'exact commands')
    for k,c in enumerate(native['commands']):require(c['exit_code']==0 and not c['administrative_stop'] and c['wall_s']<=(120 if k==0 else 600),'command budget')
    ref=read('evidence/voice_charge_basis_reference01.json');require(ref['passed'] and ref['source_sha256']==ref['source_sha256_after'] and ref['wall_s']<=300,'passed stable reference')
    for n,d in ref['source_sha256'].items():require(sha(ROOT/n)==d,'reference source')
    for n,d in ref['input_sha256'].items():require(private[n]==d and sha(ROOT/n)==d,'reference input')
    for k,v in COUNTS.items():require(ref[k]==v,'coverage '+k)
    require(ref['corrected_initial_basis_admitted'] and ref['two_step_conditioned_release_admitted'] and ref['independent_all_step_prefix'] and ref['independent_roots']==0 and not any(ref[k] for k in ['full_return_from_conditioned_root_admitted','period_map_admitted','steady_periodicity_admitted','adaptive_derivative_admitted','new_audio','physical_fidelity','real_time']),'scope')
    require(len(ref['records'])==2 and len(ref['root_checks'])==146,'complete coverage')
    for root in ref['root_checks']:require(root['rows']==218 and float(root['residual_gate_ratio'])<=1 and root['correction_gate_ratio']<=1 and float(root['max_charge_voltage_error_v'])<=1e-11 and float(root['phase_error_v'])<=1e-11,'root gates')
    for row in ref['records']:
        require(row['base_response']['max_gate_ratio']<=1 and row['incidence_identity_error']<=1e-9 and row['C27_injection_difference_max_v']>1e-8 and len(row['ledger'])==18,'basis and positive control');require(len(row['stage_reports'])==2 and len(row['root_fd'])==2 and len(row['prefix_fd'])==36,'derivative coverage')
        for stage in row['stage_reports']:require(len(stage['comparisons'])==18 and all(a['max_ratio']<=1 for a in stage['comparisons']) and stage['nonlinear_candidate']['rows']==400 and stage['nonlinear_candidate']['residual_gate_ratio']<=1 and stage['nonlinear_candidate']['correction_gate_ratio']<=1,'stage gates')
        for fd in row['root_fd']:require(fd['max_gate_ratio']<=1,'root FD')
        for fd in row['prefix_fd']:require(len(fd['steps'])==2 and all(a['max_ratio']<=1 for a in fd['steps']),'own prefix FD')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA');links=local_links(sorted(n for n in staged if n.endswith('.md')));names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/charge-basis-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,**COUNTS,corrected_initial_basis_admitted=True,two_step_conditioned_release_admitted=True,independent_all_step_prefix=True,independent_roots=0,full_return_from_conditioned_root_admitted=False,period_map_admitted=False,steady_periodicity_admitted=False,adaptive_derivative_admitted=False,covered_test_count=248,inherited_test_count=248,native_test_count=0,inherited_tests_reexecuted=False,physical_cards_changed=False,new_library_compile=False,new_audio=False,new_spice_processes=0,physical_fidelity=False,real_time=False,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],local_markdown_links=links)

def main():
    try:report=audit()
    except Exception:
        report=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_charge_basis.py').read_text())
        try:audit();report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_charge_basis_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_charge_basis_qa_failure{k:02d}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('BASIS_QA',report['passed'],len(report['source_sha256']),len(report['private_input_sha256']),flush=True)
if __name__=='__main__':main()
