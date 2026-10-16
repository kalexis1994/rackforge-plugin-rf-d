"""Promote bounded output history without changing admitted electrical or sound inputs."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from check_long_note_aa import arrays
from check_stream_output import parse
from validate_joint_charge_seed import local_links
OUT='evidence/stream_output_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def audit():
    before=read('evidence/stream_output_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,b in saved.items():assert(ROOT/n).read_bytes().startswith(b),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/stream_output_native01.json'];native=read(names[0]);assert native['passed'] and native['temporary_area_empty'] and not native['real_time'] and not native['physical_fidelity'] and not native['new_audio'] and native['new_original_equation_rows']==0
    for n,b in recover(native).items():assert(ROOT/n).read_bytes()==b,n
    assert native['control']=='evidence/long_note_aa_native01.json' and native['control_sha256']==sha(ROOT/native['control']);control=read(native['control']);assert control['passed']
    expected={}
    for index,p in enumerate(control['profiles']):
        d,a,seam,guards=arrays(unpack(p['stdout']))
        for tag,values in [('raw',a['RAW']),('expected',a['AA8'])]:
            blob=values.astype('<f8').tobytes();expected[f'{tag}-{index}']=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
    assert canonical(expected)==canonical(native['input_images'])
    m=parse(unpack(native['stdout']));assert canonical(m)==canonical(native['measurements'])
    tests=native['unit_tests'];assert tests['exit_code']==0 and tests['stderr']=='' and '2 passed; 0 failed' in unpack(tests['stdout']).decode() and '2 filtered out' in unpack(tests['stdout']).decode()
    # Structural transfer of the same scalar polynomial, with a literal node index.
    old_text=(ROOT/'crates/rf-d-circuit/src/j7_oversampled_readout.rs').read_text();new_text=(ROOT/'crates/rf-d-circuit/src/j7_stream_output.rs').read_text()
    scalar=old_text[old_text.index('fn voltage('):old_text.index('/// Fixed storage')].strip().replace('[J7]','[115]')
    current=new_text[new_text.index('fn voltage('):new_text.index('#[derive(Clone,PartialEq)]\npub struct Pipeline')].strip();assert scalar==current
    assert native['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path'])) and native['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    listening=old['new_listening'];assert sha(ROOT/listening['path'])==listening['sha256']
    assert not list((ROOT/'tmp/lab-current').iterdir());size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('stream_output*.json') if p!=ROOT/OUT);assert size<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    assert set(native['source_sha256'])<=set(sources)
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    path='crates/rf-d-circuit/src/j7_stream_output.rs';inherited=old['covered_test_count']
    result.update(schema='rf-d/bounded-continuous-output/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),stream_output_admitted=True,stream_output_reference={n:sha(ROOT/n) for n in names},stream_output_archived_profiles=2,stream_output_partitions_per_profile=3,stream_output_frames_per_replay=14401,stream_output_latency_input_samples=384,stream_output_latency_output_samples=48,stream_output_latency_s=.001,stream_output_frame_indices_and_values_bitwise_identical=True,stream_output_real_prefix_duration_s=.01,stream_output_real_control_steps=int(m['live'][1]),stream_output_live_states_stages_bitwise_identical=True,stream_output_state_bytes=m['sizes'][1],stream_output_decimator_bytes=m['sizes'][0],stream_output_previous_buffer_bytes=m['sizes'][2],stream_output_heap_allocations=0,stream_output_receipt_bytes_before_qa=size,stream_output_receipt_budget_bytes=8*1024*1024,active_output_pipeline=path,active_output_pipeline_source_sha256=sources[path],active_output_pipeline_origin_commit=None,active_output_pipeline_origin_commit_pending_self_commit=True,active_readout_origin_commit=before['base_commit'],active_readout_origin_commit_pending_self_commit=False,active_antialias_origin_commit=before['base_commit'],active_antialias_origin_commit_pending_self_commit=False,inherited_test_count=inherited,covered_test_count=inherited+2,native_test_count=2,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_global_trajectories_reexecuted=False,new_unit_test_definitions=2,new_unit_tests_executed=2,new_stream_circuit_prefix_trajectories=2,new_archived_output_replays=6,new_original_equation_rows=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,previous_listening_preserved_sha256=listening['sha256'],new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_solver','active_voice','active_voice_implementation','active_initializer','active_readout','active_antialias','active_antialias_coefficients','cost_ratio','private_input_sha256']:assert result[k]==old[k],k
    return result
def main():
    try:r=audit()
    except Exception:
        s=Sources(['tools/validate_stream_output.py']);r=dict(passed=False,**s.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/stream_output_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/stream_output_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('STREAM_OUTPUT_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['stream_output_state_bytes'],r['stream_output_receipt_bytes_before_qa'],flush=True)
if __name__=='__main__':main()
