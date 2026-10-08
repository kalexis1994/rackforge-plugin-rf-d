"""Release audit: preserve old inputs, local charge roots and failed attempts."""
import base64,hashlib,json,re,subprocess
from prepare_vco1_portable import ROOT,sha
from validate_mixer_on_native import native_source_identity
OUT='evidence/voice_chain_charge_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,msg):
    if not ok:raise ValueError(msg)
def audit():
    previous='evidence/voice_vco1_portable_tests01.json';old=read(previous);snap=read('evidence/voice_chain_charge_before01.json')
    require(old['passed'] and sha(ROOT/previous)==snap['previous_qa_sha256'],'previous QA')
    prior={n:base64.b64decode(v) for n,v in snap['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(prior[n] if n in prior else (ROOT/n).read_bytes()).hexdigest()==h,'protected '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    lib='crates/rf-d-circuit/src/lib.rs';require((ROOT/lib).read_bytes()==prior[lib]+b'\npub mod chain_charge;\npub mod chain_radau;\n','additive library exports')
    for i in [1,2,3]:
        repair=read(f'evidence/voice_chain_charge_repair{i:02d}.json');failed=read(repair['failure_receipt'])
        require(not failed['passed'] and 'failure' in failed and 'replay' in failed,'reference failure/replay retained')
        require(sha(ROOT/repair['failure_receipt'])==repair['failure_sha256'],'repair failure hash')
        for n,b in repair['before_base64'].items():require(base64.b64decode(b).decode()==failed['failed_source_text'][n],'failed adapter preserved')
    amendment=read('evidence/voice_chain_charge_increment01.json');failed=read(amendment['failure_receipt'])
    require(not failed['passed'] and 'line search' in failed['failure'] and 'line search' in failed['replay'],'increment floor/replay')
    require(sha(ROOT/amendment['failure_receipt'])==amendment['failure_sha256'],'increment amendment identity')
    native1=read('evidence/voice_chain_charge_native01.json');native2=read('evidence/voice_chain_charge_native02.json');final=read('evidence/voice_chain_charge_native04.json')
    require(not native1['passed'] and len(native1['commands'])==2 and len(native1['replays'])==1,'compile failure retained')
    require('float literals' in native1['commands'][-1]['stderr'] and 'float literals' in native1['replays'][0]['stderr'],'same syntax rejection')
    require(not native2['passed'] and '3 passed; 1 failed' in native2['commands'][-1]['stdout'] and '3 passed; 1 failed' in native2['replays'][0]['stdout'],'comparison failure/replay')
    sign=read('evidence/voice_chain_charge_sign01.json')
    for n,h in sign['inputs_sha256'].items():require(sha(ROOT/n)==h,'sign repair frozen '+n)
    initial=base64.b64decode(sign['before_base64']['tools/chain_charge_reference.py'])
    corrected=initial.replace(b'r[:66]=fcore(x[:66].tolist())[0];r[66]',b'r[:66]=fcore(x[:66].tolist())[0];r[:48]*=-1.;r[66]').replace(b'reference05.json',b'reference06.json').replace(b'vectors05.txt',b'vectors06.txt')
    require((ROOT/'tools/chain_charge_reference.py').read_bytes()==corrected,'only row orientation and output names changed after comparison failure')
    ref=read('evidence/voice_chain_charge_reference06.json')
    require(ref['passed'] and len(ref['cases'])==12 and not ref['native_seeds_used'] and ref['source_sha256']==ref['source_sha256_after'],'independent reference')
    for n,h in ref['source_sha256'].items():require(sha(ROOT/n)==h,'reference source '+n)
    require(sha(ROOT/'evidence/voice_chain_charge_vectors06.txt')==ref['vectors_sha256'],'fixture hash')
    for c in ref['cases']:
        require(c['error_ratio']<=1,'independent temporal gate')
        for name in ['full','mid','end']:
            require(c[name]['residual_ratio']<=1 and c[name]['correction_ratio']<=1 and len(c[name]['stage_decimal'])==68,'independent root gates')
    require(final['passed'] and len(final['commands'])==3 and not final['replays'] and final['source_sha256']==final['source_sha256_after'],'four native tests final')
    for n,h in final['source_sha256'].items():require(sha(ROOT/n)==h,'native source '+n)
    require(sha(__import__('pathlib').Path(final['compiler']['path']))==final['compiler']['sha256'],'compiler')
    stdout=final['commands'][-1]['stdout'];require('4 passed; 0 failed' in stdout,'four tests executed')
    for marker in ['scenes=12,stages=72,currents=180','physical_rows=264','columns=1632,entries=221952','contact_cases=8','accepted_and_rejected_allocations=0']:require(marker in stdout,'marker '+marker)
    metrics=re.search(r'max_v=([^,]+),max_i=([^,]+),max_lte=([^\s]+)',stdout);require(metrics is not None,'metrics')
    v,i,lte=map(float,metrics.groups());require(v<=1e-6 and i<=1e-9 and lte<=1.,'numerical gates')
    series=read('evidence/voice_chain_charge_series01.json');require(sha(ROOT/'evidence/voice_chain_charge_native03.json')==series['previous_native_sha256'],'previous passing series bank retained')
    for record in [native1,native2,read('evidence/voice_chain_charge_native03.json'),final]:
        for o in record['outputs']:
            require(sha(ROOT/o['path'])==o['sha256'],'preserved native output');private[o['path']]=o['sha256']
    # Compare capacitor incidence against the independently inherited Python graph.
    from circuit66_vca_release_probes import CAPS
    expected=[(a,b if isinstance(b,int) else 66 if b=='BUS' else 68,c) for a,b,c in CAPS]
    text=(ROOT/'crates/rf-d-circuit/src/chain_charge.rs').read_text()
    array=text.split('pub const CAPACITORS:')[1].split('];')[0].split('=[')[1].replace('GROUND','68').replace('BUS','66')
    tuples=[(int(a),int(b),float(c)) for a,b,c in re.findall(r'\((\d+),(\d+),([0-9.e-]+)\)',array)]
    require(tuples==expected,'all 17 capacitor incidences match independent graph')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'complete staged release')
    names=set(old['source_sha256'])|{previous}|set(staged)-{OUT}
    sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/chain-charge-release/v1',passed=True,base_commit=snap['base_commit'],previous_qa_sha256=sha(ROOT/previous),
        source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,inherited_test_count=239,native_test_count=4,covered_test_count=243,
        inherited_tests_reexecuted=False,independent_final_stage_roots=72,independent_final_pairs=36,independent_counts_exclude_rejected_attempts=True,
        source_current_comparisons=180,jacobian_entries=221952,contact_structural_cases=8,euler_physical_rows=264,
        max_node_error_v=v,max_source_current_error_a=i,max_local_error_ratio=lte,new_chain_radau_locally_admitted=True,
        min_admitted_half_step_s=chain_min(),vco_active_coupling_admitted=False,full_voice_radau_admitted=False,
        physical_cards_changed=False,normalized_stage_increments=True,heap_allocations_measured=0,lab_stack_bytes=8388608,
        physical_fidelity=False,real_time=False,new_spice_processes=0,new_audio=False,previous_audio=old['previous_audio'],
        native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'],long_note_admitted_locally=False)
def chain_min():return 4*(125e-9/65536)
def main():
    report=audit();(ROOT/OUT).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('CHAIN_QA',report['passed'],'sources',len(report['source_sha256']),'private',len(report['private_input_sha256']),'covered',report['covered_test_count'])
if __name__=='__main__':main()
