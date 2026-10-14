"""Preserve the admitted voice and promote only the measured sparse-solver scope."""
import base64,hashlib,json,shutil,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from validate_joint_charge_seed import local_links
OUT='evidence/voice_cost_tests01.json'
NEW_RS=['crates/rf-d-circuit/src/ordered_voice.rs','crates/rf-d-circuit/src/ordered_voice_solver.rs','crates/rf-d-circuit/src/sparse_ordered_voice.rs','crates/rf-d-circuit/src/sparse_ordered_voice_solver.rs','tools/voice_cost_bench.rs','tools/voice_order_bench.rs','tools/voice_sparse_bench.rs','tools/voice_sparse_reuse.rs','tools/voice_sparse_trajectory.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in NEW_RS)+'/evidence/voice_cost*.json text eol=lf\n/evidence/voice_order*.json text eol=lf\n/evidence/voice_sparse*.json text eol=lf\n').encode()
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit():
    before=read('evidence/voice_cost_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    assert (ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+ATTR
    for n in ['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']:assert (ROOT/n).read_bytes().startswith(saved[n]),n
    private=dict(old['private_input_sha256'])
    for n,h in private.items():assert sha(ROOT/n)==h,n
    records=['evidence/voice_cost_inputs01.json','evidence/voice_cost_profile01.json','evidence/voice_order_recipe01.json','evidence/voice_order_bench01.json','evidence/voice_sparse_recipe01.json','evidence/voice_sparse_bench01.json','evidence/voice_sparse_reuse01.json','evidence/voice_sparse_native01.json','evidence/voice_sparse_reference01.json','evidence/voice_cost_prefix01.json','evidence/voice_cost_listening01.json']
    for name in records:
        r=read(name);assert r['passed'],name
        for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
        for field in ['private_sha256','private_used_sha256']:
            for n,h in r.get(field,{}).items():assert sha(ROOT/n)==h,n;private[n]=h
    bench=read('evidence/voice_sparse_bench01.json');assert len(bench['checks'])==24 and len(bench['rounds'])==120 and bench['median_ratio']<1
    assert max(c['direction_fraction'] for c in bench['checks'])<=1 and max(c['stage_fraction'] for c in bench['checks'])<=1
    reuse=read('evidence/voice_sparse_reuse01.json');assert reuse['rejected_matrices']==reuse['exact_valid_direction_replays']==5
    native=read('evidence/voice_sparse_native01.json');ref=read('evidence/voice_sparse_reference01.json');prefix=read('evidence/voice_cost_prefix01.json');audio=read('evidence/voice_cost_listening01.json')
    assert native['source_unchanged'] and native['library_unchanged'] and len(native['profiles'])==2 and all(p['exit_code']==0 and p['wall_s']<=600 for p in native['profiles'])
    assert ref['wall_s']<=300 and ref['original_rows']==12550 and ref['common_clocks']==192 and ref['max_node_fraction']<=1 and ref['max_load_fraction']<=1
    assert all(p['ticks']==24000*524288 and p['selected_pairs']==12 and p['max_bus_kcl_a']<=2e-11 for p in ref['profiles'])
    assert len(prefix['profiles'])==2 and all(p['common_clocks']==64 and p['node_fraction']<=1 and p['load_fraction']<=1 for p in prefix['profiles'])
    assert all(p['original_tangent_fraction']<=1 and p['dense_difference_fraction']<=1 and p['backward_fraction']<=1e-11 for p in ref['linear_directions'])
    assert audio['duration_s']==audio['simulation_duration_s']==.024 and audio['frames']==1152 and not audio['repeated_cycles'] and not audio['concatenated'] and not audio['peak_normalization'] and not audio['dc_removed']
    assert audio['monitor_samples_per_v']==4 and audio['peak_sample']<.98
    for pattern in ['voice-cost*/*','voice-order*/*','voice-sparse*/*']:
        for p in (ROOT/'references-local').glob(pattern):
            if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256'];assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==native['library_sha256']
    size=sum((ROOT/n).stat().st_size for n in set(private)-set(old['private_input_sha256']));assert size<=32*1024**2 and shutil.disk_usage(ROOT).free>=1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    names=set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r=dict(schema='rf-d/voice-cost/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,new_private_bytes=size,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(old['private_input_sha256']),native_nodes=250,original_nodes=251,profiles=2,duration_per_profile_s=.024,accepted_steps=sum(p['accepted_steps'] for p in ref['profiles']),fine_endpoints=2*sum(p['accepted_steps'] for p in ref['profiles']),new_independent_nonlinear_rows=12550,compared_effective_tangent_entries=500000,common_clocks=192,baseline_prefix_clocks=128,parts_bit_comparisons=6048000,selected_pairs=24,linear_benchmark_rounds=120,median_solver_ratio=bench['median_ratio'],worst_solver_ratio=bench['worst_ratio'],solver_after_rejection_replays=5,atomic_rollbacks=6,integrated_vco_voice=True,both_contours_loaded=True,shared_bus=True,imposed_audio_source=False,conditioned_dc_ramp_zero=True,fixed_panel_scene=True,physical_circuit_changed=False,numerical_gates_changed=False,new_audio=True,new_continuous_history_duration_s=.024,old_history_extended=False,reference={'path':'evidence/voice_sparse_reference01.json','sha256':sha(ROOT/'evidence/voice_sparse_reference01.json')},cost_listening={'path':'evidence/voice_cost_listening01.json','sha256':sha(ROOT/'evidence/voice_cost_listening01.json')},new_library_compile=False,new_cargo_cache=False,inherited_test_count=255,inherited_tests_reexecuted=False,inherited_python_test_definitions=2,new_unit_test_definitions=0,physical_fidelity=False,real_time=False,heap_measured=False,deadline_measured=False,compiler=old['compiler'],local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for key in ['previous_audio','native_listening','native_chain_listening','official_executable_sha256','conditioned_transient_listening','sustained_listening','sustained_diagnostic','release_listening','release_reference','release_review','decay_listening','decay_reference','extended_reference','extended_listening','public_block_library_sha256','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted','tail_reference','tail_listening','retrigger_reference','retrigger_listening','cutoff_reference','cutoff_listening','cutoff_ab_reference','cutoff_ab_listening']:r[key]=old[key]
    return r
def main():
    try:r=audit()
    except Exception:
        error=traceback.format_exc()
        try:audit();replay='unexpected pass'
        except Exception:replay=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_cost_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/voice_cost_qa_failure{k:02d}.json',dict(passed=False,failure=error,unchanged_replay=replay,source_base64=base64.b64encode(Path(__file__).read_bytes()).decode()));raise
    write(ROOT/OUT,r);print('VOICE_COST_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['new_private_bytes'])
if __name__=='__main__':main()
