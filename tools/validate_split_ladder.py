"""Close both split-parent experiments, profile and transfer proof without promotion."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_split_ladder import derive
from check_hybrid_voice import unpack,parse,compare
from check_hybrid_schur import comparison
from check_split_ladder import LOCAL_KEYS,SPLIT_KEYS
from compact_split_sources import images as source_images,expanded_bytes,TARGET
from validate_joint_charge_seed import local_links
OUT='evidence/split_ladder_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def main():
    before=read('evidence/split_ladder_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=['evidence/split_ladder_native01.json','evidence/split_ladder_native02.json','evidence/split_ladder_profile01.json','evidence/split_ladder_transfer01.json','evidence/split_ladder_audit01.json']
    first,last,profile,transfer,audit=[read(n) for n in names];attempts=[first,last]
    images=[source_images(r) for r in attempts]
    compaction=read('evidence/split_ladder_compaction01.json');restored=expanded_bytes(last)
    assert compaction['passed'] and compaction['original_byte_reconstruction_exact'] and compaction['target']==TARGET
    assert compaction['original_sha256']==hashlib.sha256(restored).hexdigest() and compaction['original_bytes']==len(restored)
    assert compaction['compact_sha256']==sha(ROOT/TARGET) and compaction['compact_bytes']==(ROOT/TARGET).stat().st_size
    assert compaction['base_receipt_sha256']==sha(ROOT/compaction['base_receipt']) and compaction['budget_bytes']==8*1024*1024
    for n,h in compaction['source_sha256'].items():assert sha(ROOT/n)==h,n
    qa_failure=read('evidence/split_ladder_qa_failed01.json');assert not qa_failure['passed'] and qa_failure['failed_phase']=='receipt_storage_budget'
    assert qa_failure['actual_receipt_bytes']>qa_failure['budget_bytes']==8*1024*1024
    assert hashlib.sha256(unpack(qa_failure['failed_source'])).hexdigest()==qa_failure['source_sha256']['tools/validate_split_ladder.py']
    a=qa_failure['failed_process'];b=qa_failure['unchanged_replay'];assert a['exit_code']==b['exit_code']!=0 and unpack(a['stdout'])==unpack(b['stdout']) and a['stderr']==b['stderr']
    assert qa_failure['receipt_before'][TARGET]['sha256']==compaction['original_sha256']
    for r in[*attempts,profile,transfer,audit]:
        for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h or n==TARGET and hashlib.sha256(restored).hexdigest()==h or any(n in image and hashlib.sha256(base64.b64decode(image[n])).hexdigest()==h for image in images),n
    previous=read('evidence/hybrid_direct_native03.json');baseline=[p for p in previous['profiles'] if p['mode']=='direct'];union=read('evidence/ladder_voice_native01.json');reference=[p for p in union['profiles'] if p['mode']=='ladder'];expected=[]
    for p in baseline:
        _,roots,_=parse(unpack(p['stdout']));expected.extend(','.join(map(str,row)) for row in roots)
    ratios=[];previous_ratios=[]
    for r in attempts:
        assert not r['passed'] and r['failed_phase']=='cost' and r['numerical_integration_verified']
        assert len(r['compiles'])==4 and all(p['exit_code']==0 for p in r['compiles'])
        assert unpack(r['local_input'])==('\n'.join(expected)+'\n').encode()
        for image in images:
            if all(n in image for n in r['source_sha256']) and all(hashlib.sha256(base64.b64decode(image[n])).hexdigest()==h for n,h in r['source_sha256'].items()):break
        else:raise AssertionError('missing complete failed source image')
        a=r['failed_process'];b=r['unchanged_replay'];assert a['exit_code']==b['exit_code']==0 and a['stderr']==b['stderr']==''
        assert unpack(a['stdout']).split(b'FINAL,')[0]==unpack(b['stdout']).split(b'FINAL,')[0]
        ratio=r['profiles'][3]['measurement']['solve_s']/r['profiles'][0]['measurement']['solve_s'];assert ratio==r['cost_ratio'] and ratio>.9;ratios.append(ratio)
        prior=r['profiles'][3]['measurement']['solve_s']/r['profiles'][1]['measurement']['solve_s'];assert prior==r['previous_cost_ratio'];previous_ratios.append(prior)
        lines=unpack(r['local_stdout']).decode().splitlines();values=list(map(float,next(s for s in lines if s.startswith('LOCAL,')).split(',')[1:]));assert r['local']==dict(zip(LOCAL_KEYS,values))
        values=list(map(float,next(s for s in lines if s.startswith('SPLIT,')).split(',')[1:]));assert r['split']==dict(zip(SPLIT_KEYS,values))
        x=r['local'];assert x['pairs']==24 and x['stages']==48 and x['directions']==144 and x['fd_columns']==222 and x['invalid_cases']==36
        assert x['reconstructed_error_v']<=2e-9 and x['original_residual_a']<=20e-12 and x['charge_error_a']==0
        assert max(x[k] for k in ['direction_fraction','fd_fraction'])<=1 and x['max_final_backward']<=1e-11
        x=r['split'];assert x['physical_dc_error_a']==x['physical_j_error_s']==x['reduced_j_fraction']==x['kernel_error_v']==0
        assert x['maximum_transfer_offset_v']<=128*(2**-52)**2*40 and x['kernel_seeds']==96 and x['transfer_invalid_cases']==48
        assert x['full_residual_checks']==48 and x['congruence_entries']==2048 and x['legal_parent_edges']==1
        grids=[]
        for p in r['profiles']:
            raw=unpack(p['stdout']);g,roots,f=parse(raw);assert f==p['measurement'] and p['exit_code']==0
            i=0 if p['maximum_full_ticks']==33554432 else 1;control=unpack(baseline[i]['stdout']);og,_,_=parse(control)
            assert comparison(g,og,raw,control)==p['direct_comparison']
            control=unpack(reference[i]['stdout']);og,_,_=parse(control);assert comparison(g,og,raw,control)==p['previous_comparison']
            y=p['full_voice_comparison'];assert y['j7_rms_relative']<=.03 and y['j7_peak_relative']<=.06 and y['j7_mean_error_v']<=1e-5 and max(y['contour_fraction'],y['bus_fraction'],y['load_fraction'])<=1
            assert p['solver']['max_final_backward']<=1e-11
            if p['mode']=='split':
                assert raw.split(b'FINAL,')[0]==control.split(b'FINAL,')[0]
                final=lambda data:next(line for line in data.decode().splitlines() if line.startswith('FINAL,')).split(',')[12:]
                assert final(raw)==final(control)
                assert f['heap_allocations']==0 and f['exact_replays']==4 and f['atomic_rejections']==5;grids.append(g)
        assert len(grids)==2 and json.dumps(compare(grids[0],grids[1],True),sort_keys=True)==json.dumps(r['refinement'],sort_keys=True)
        for n,h in r['private_used_sha256'].items():assert private[n]==h==sha(ROOT/n),n
    assert profile['passed'] and profile['timing_includes_exact_replays'] and profile['timers_end_before_stage_return'] and not profile['admission_benchmark']
    raw=unpack(profile['stdout']);g,_,f=parse(raw);control=unpack(first['profiles'][3]['stdout']);og,_,_=parse(control);assert comparison(g,og,raw,control)==profile['comparison']
    assert f==profile['measurement'] and all(v>0 for v in profile['timed_sections_s'].values()) and profile['evaluations']==167864
    v=list(map(int,next(line for line in raw.decode().splitlines() if line.startswith('PROFILE,')).split(',')[1:]));assert list(profile['timed_sections_s'].values())==[n*1e-9 for n in v[:7]]
    # Instrumentation changes only these explicit timing lines; current voice body is unchanged.
    s=(ROOT/'crates/rf-d-circuit/src/profiled_split_ladder_voice.rs').read_text(encoding='utf8')
    block='use std::{time::Instant,sync::atomic::{AtomicU64,Ordering}};\nstatic PROFILE:[AtomicU64;8]=[const{AtomicU64::new(0)};8];\npub fn profile()->[u64;8]{std::array::from_fn(|k|PROFILE[k].load(Ordering::Relaxed))}\nfn record(k:usize,t:Instant)->Instant{let now=Instant::now();PROFILE[k].fetch_add(now.duration_since(t).as_nanos() as u64,Ordering::Relaxed);now}\n'
    assert block+'\n' in s;s=s.replace(block+'\n','',1).replace('    let started=Instant::now();PROFILE[7].fetch_add(1,Ordering::Relaxed);\n','',1).replace('    let clock=record(0,started);\n','',1)
    for k in range(1,6):s=s.replace(f'    let clock=record({k},clock);\n','',1)
    s=s.replace('    record(6,clock);\n','',1);assert s==(ROOT/'crates/rf-d-circuit/src/split_ladder_voice.rs').read_text(encoding='utf8')
    assert transfer['passed'] and unpack(transfer['input'])==unpack(last['local_input']).splitlines(keepends=True)[0]
    assert transfer['local']==dict(invalid_cases=30,exact_retries=30,atomic_rejections=30,finite_overflow_cases=2,other_low_point_cases=1)
    assert list(map(int,unpack(transfer['stdout']).decode().strip().split(',')[1:]))==list(transfer['local'].values())
    assert audit['passed'] and audit['native']==names[1] and audit['original_rows']==5712 and len(audit['profiles'])==2
    assert all(p['pairs']==12 and p['max_residual_a']<=20e-12 and p['max_correction_v']<=2e-9 for p in audit['profiles'])
    for r in[*attempts,profile,transfer]:
        assert r['temporary_area_empty'] and r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
        assert r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    assert not list((ROOT/'tmp/lab-current').iterdir())
    receipt_bytes=sum(p.stat().st_size for p in (ROOT/'evidence').glob('split_ladder*.json') if p!=ROOT/OUT);assert receipt_bytes<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for r in[*attempts,profile,transfer,audit]:assert set(r['source_sha256'])<=set(sources)
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    result.update(schema='rf-d/nominal-split-ladder-final-stamp/rejected-cost-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),split_ladder_numerically_verified=True,split_ladder_optimization_admitted=False,global_ladder_reduction_admitted=False,split_ladder_cost_gate_passed=False,split_ladder_cost_ratios=ratios,split_ladder_previous_cost_ratios=previous_ratios,split_ladder_cost_gate=.9,split_ladder_local=last['local'],split_ladder_transfer=last['split'],split_ladder_metadata_guards=transfer['local'],split_ladder_parent_rejections=48,split_ladder_parent_exact_retries=38,split_ladder_paired_parent_rejections=10,split_ladder_original_rows=5712,split_ladder_heap_allocations=0,split_ladder_exact_replays=8,split_ladder_atomic_rejections=10,split_ladder_profile_measures_old_type_adapter=True,split_ladder_profile=profile['timed_sections_s'],split_ladder_reference={n:sha(ROOT/n) for n in names},inherited_tests_reexecuted=False,inherited_global_trajectories_reexecuted=True,inherited_global_trajectory_reexecutions=4,inherited_global_trajectory_suite_reexecuted=False,new_original_250_node_trajectories=0,inherited_private_hashes_recomputed=False,new_candidate_trajectories=4,new_fresh_control_trajectories=4,new_candidate_instrumented_trajectories=1,new_unit_test_definitions=0,new_audio=False,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,split_ladder_receipt_bytes_before_qa=receipt_bytes,split_ladder_receipt_budget_bytes=8*1024*1024,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    result['split_ladder_source_archive_compaction']=compaction
    for k in['active_solver','active_voice','cost_ratio','inherited_test_count','private_input_sha256']:assert result[k]==old[k],k
    write(ROOT/OUT,result);print('SPLIT_LADDER_QA',len(sources),len(private),'precision verified; both cost gates rejected; active=direct',ratios,receipt_bytes)
if __name__=='__main__':main()
