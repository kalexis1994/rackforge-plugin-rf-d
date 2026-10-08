"""Joint release audit: immutable lineage, physical helper identity and checks."""
import base64,hashlib,json,re,subprocess
from prepare_vco1_portable import ROOT,sha
from validate_mixer_on_native import native_source_identity
OUT='evidence/voice_joint_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,msg):
    if not ok:raise ValueError(msg)
def audit():
    previous='evidence/voice_chain_charge_tests01.json';old=read(previous);snap=read('evidence/voice_joint_before01.json')
    require(old['passed'] and sha(ROOT/previous)==snap['previous_qa_sha256'],'previous QA')
    prior={n:base64.b64decode(v) for n,v in snap['mutable_before_base64'].items()}
    amendment=read('evidence/voice_joint_bytes01.json');prior['.gitattributes']=base64.b64decode(amendment['before_base64']['.gitattributes'])
    for n,h in old['source_sha256'].items():require(hashlib.sha256(prior[n] if n in prior else (ROOT/n).read_bytes()).hexdigest()==h,'protected '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    lib='crates/rf-d-circuit/src/lib.rs'
    measured=base64.b64decode(amendment['before_base64'][lib])
    require(measured==prior[lib]+b'\n#[allow(dead_code)] mod joint_vco_fine;\npub mod joint_voice;\r\n','additive measured exports')
    require((ROOT/lib).read_bytes()==measured.replace(b'\r\n',b'\n'),'only final newline normalized')
    require((ROOT/'.gitattributes').read_bytes()==prior['.gitattributes']+b'\n# Joint BUS measured native sources.\n/crates/rf-d-circuit/src/joint_vco_fine.rs text eol=lf\n/crates/rf-d-circuit/src/joint_voice.rs text eol=lf\n/crates/rf-d-circuit/tests/joint_voice.rs text eol=lf\n','checkout identities')
    # Recreate only the declared representation edits; no physical helper changes.
    script=(ROOT/'tools/prepare_joint_voice.py').read_text();edits=script[script.index('    source=source.replace'):script.index('    target=ROOT/')]
    namespace=dict(source=(ROOT/'crates/rf-d-circuit/src/vco1_radau_fine.rs').read_text())
    exec('\n'.join(line[4:] for line in edits.splitlines()),namespace)
    require(namespace['source']==(ROOT/'crates/rf-d-circuit/src/joint_vco_fine.rs').read_text(),'exact additive increment helper')
    native1=read('evidence/voice_joint_native01.json');native2=read('evidence/voice_joint_native02.json');native=read('evidence/voice_joint_native03.json');ref1=read('evidence/voice_joint_reference01.json');ref=read('evidence/voice_joint_reference02.json')
    require(sha(ROOT/'evidence/voice_joint_native02.json')==amendment['native_receipt_sha256'] and native2['source_sha256'][lib]==hashlib.sha256(measured).hexdigest(),'original passing measured bytes')
    repairs=[read(f'evidence/voice_joint_repair{i:02d}.json') for i in [1,2]]
    for repair in repairs:
        failed=read(repair['failure_receipt']);require(not failed['passed'] and sha(ROOT/repair['failure_receipt'])==repair['failure_sha256'],'failure frozen')
        for n,b in repair['before_base64'].items():
            text=base64.b64decode(b).decode();saved=failed['failed_source_text'];require(text==(saved[n] if isinstance(saved,dict) else saved),'failed source retained')
    require(len(native1['replays'])==1 and '1 passed; 1 failed' in native1['replays'][0]['stdout'],'native replay')
    require('AssertionError' in ref1['failure'] and 'AssertionError' in ref1['replay'],'parser replay')
    for record in [native1,native2,native]:
        for o in record['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'binary frozen');private[o['path']]=o['sha256']
    require(native['passed'] and native['source_sha256']==native['source_sha256_after'] and not native['replays'],'native pass')
    tags=lambda record:[line[line.index('JOINT_ROOT,'):] if 'JOINT_ROOT,' in line else line for line in record['commands'][-1]['stdout'].splitlines() if 'JOINT_ROOT,' in line or line.startswith('JOINT_STATE,')]
    require(tags(native)==tags(native2),'byte-identical coupled candidate points after newline normalization')
    require(ref['passed'] and ref['source_sha256']==ref['source_sha256_after'] and ref['native_candidates_used'] and not ref['independent_root_solve'],'reference scope')
    for record in [native,ref]:
        for n,h in record['source_sha256'].items():require(sha(ROOT/n)==h,'final source '+n)
    stdout=native['commands'][-1]['stdout']
    for marker in ['2 passed; 0 failed','matrix_entries=640000','pairs=4,stages=8,fd_columns=40,fd_entries=16000','reject_preserved=4']:require(marker in stdout,'marker '+marker)
    require(len(ref['cases'])==4 and sum(c['rows'] for c in ref['cases'])==1600,'independent rows')
    for c in ref['cases']:require(c['residual_gate_ratio']<=1 and c['correction_gate_ratio']<=1,'oracle gates')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'complete staged release')
    names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    result=dict(schema='rf-d/joint-release/v1',passed=True,base_commit=snap['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,
        inherited_test_count=243,native_test_count=2,covered_test_count=245,inherited_tests_reexecuted=False,
        locally_admitted_coupled_pairs=4,locally_admitted_coupled_stages=8,unknowns=200,stage_rows=400,
        matrix_regression_entries=640000,fd_entries=16000,independent_residual_rows=1600,independent_roots=0,native_candidate_points_used=True,
        vco_active_coupling_admitted_locally=True,full_voice_radau_admitted=False,own_joint_startup=False,joint_trajectory=False,
        local_temporal_error_measured=False,heap_allocations_measured=None,lab_stack_bytes=33554432,physical_cards_changed=False,
        physical_fidelity=False,real_time=False,new_audio=False,new_spice_processes=0,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],long_note_admitted_locally=False,
        max_reference_correction_v=max(c['max_correction_v'] for c in ref['cases']),max_reference_correction_a=max(c['max_correction_a'] for c in ref['cases']))
    return result
def main():
    result=audit();(ROOT/OUT).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('JOINT_QA',result['passed'],len(result['source_sha256']),len(result['private_input_sha256']))
if __name__=='__main__':main()
