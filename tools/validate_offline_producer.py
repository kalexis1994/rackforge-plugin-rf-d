"""Admit cooperative offline ownership without retagging electrical evidence."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from check_offline_producer import parse,inputs,CONTROLS
from validate_joint_charge_seed import local_links
OUT='evidence/offline_producer_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def audit():
    before=read('evidence/offline_producer_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,b in saved.items():assert(ROOT/n).read_bytes().startswith(b),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/offline_producer_native01.json'];native=read(names[0]);assert native['passed'] and native['temporary_area_empty'] and not native['real_time'] and not native['physical_fidelity'] and not native['new_audio'] and native['new_original_equation_rows']==0
    for n,b in recover(native).items():assert(ROOT/n).read_bytes()==b,n
    assert native['controls']=={n:sha(ROOT/n) for n in CONTROLS}
    expected={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in inputs().items()};assert canonical(expected)==canonical(native['input_images'])
    m=parse(unpack(native['stdout']));assert canonical(m)==canonical(native['measurements'])
    tests=native['unit_tests'];assert tests['exit_code']==0 and tests['stderr']=='' and '3 passed; 0 failed' in unpack(tests['stdout']).decode() and '4 filtered out' in unpack(tests['stdout']).decode()
    assert native['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path'])) and native['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    listening=old['new_listening'];assert sha(ROOT/listening['path'])==listening['sha256']
    assert not list((ROOT/'tmp/lab-current').iterdir());size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('offline_producer*.json') if p!=ROOT/OUT);assert size<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    assert set(native['source_sha256'])<=set(sources)
    # Old counters named new_* describe their own blocks, not this execution.
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and (not k.startswith('new_') or k=='new_listening')}
    result['inherited_legacy_new_fields_reference']=dict(path=before['previous_qa'],sha256=before['previous_qa_sha256'],fields=sorted(k for k in old if k.startswith('new_') and k!='new_listening'))
    path='crates/rf-d-circuit/src/nominal_offline_producer.rs';inherited=old['covered_test_count']
    result.update(schema='rf-d/cooperative-offline-producer/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),offline_producer_admitted=True,offline_producer_reference={n:sha(ROOT/n) for n in names},offline_producer_real_prefix_duration_s=.01,offline_producer_profiles=3,offline_producer_steps_per_profile=5170,offline_producer_control_pairs_compared=5170,offline_producer_frame_indices_values_states_bitwise_identical=True,offline_producer_resume_branches=sum(d['resume_branches'] for d in m['profiles']),offline_producer_quota_unit='voice::advance invocations including failures; internal iterations not separately budgeted',offline_producer_zero_quota_can_drain_pending=True,offline_producer_persistent_bytes=m['sizes'][0],offline_producer_pending_bytes=m['sizes'][1],offline_producer_workspace_bytes=m['sizes'][2],offline_producer_heap_allocations=0,offline_producer_receipt_bytes_before_qa=size,offline_producer_receipt_budget_bytes=8*1024*1024,active_offline_producer=path,active_offline_producer_source_sha256=sources[path],active_offline_producer_entry='Producer::pump',active_offline_producer_origin_commit=None,active_offline_producer_origin_commit_pending_self_commit=True,active_output_pipeline_origin_commit=before['base_commit'],active_output_pipeline_origin_commit_pending_self_commit=False,inherited_test_count=inherited,covered_test_count=inherited+3,native_test_count=3,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_global_trajectories_reexecuted=False,new_unit_test_definitions=3,new_unit_tests_executed=3,new_offline_producer_circuit_prefix_trajectories=3,new_control_circuit_prefix_trajectories=1,new_archived_output_replays=0,new_original_equation_rows=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,previous_listening_preserved_sha256=listening['sha256'],new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_solver','active_voice','active_voice_implementation','active_initializer','active_readout','active_antialias','active_antialias_coefficients','active_output_pipeline','cost_ratio','private_input_sha256']:assert result[k]==old[k],k
    return result

def main():
    try:r=audit()
    except Exception:
        s=Sources(['tools/validate_offline_producer.py']);r=dict(passed=False,**s.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/offline_producer_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/offline_producer_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('OFFLINE_PRODUCER_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['offline_producer_persistent_bytes'],r['offline_producer_receipt_bytes_before_qa'],flush=True)
if __name__=='__main__':main()
