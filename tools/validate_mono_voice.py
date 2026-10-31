"""Protect prior evidence and admit a bounded full-voice API, not RT."""
import base64,hashlib,json,subprocess,shutil,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from analyse_mono_voice import audit as analysis
from validate_joint_charge_seed import local_links
OUT='evidence/mono_voice_tests01.json'

def audit():
    b=json.loads((ROOT/'evidence/mono_voice_before01.json').read_text(encoding='utf8'));old=json.loads((ROOT/b['previous_qa']).read_text(encoding='utf8'));assert old['passed']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==b['base_commit']
    saved={n:base64.b64decode(v) for n,v in b['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,v in saved.items():assert(ROOT/n).read_bytes().startswith(v),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    native=json.loads((ROOT/'evidence/mono_voice_native01.json').read_text(encoding='utf8'));assert native['passed'];recover(native)
    for n,v in recover(native).items():assert(ROOT/n).read_bytes()==v,n
    assert native['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
    lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';assert native['library_sha256']==private[lib]==sha(ROOT/lib)
    assert native['unit']['exit_code']==0 and '4 passed' in unpack(native['unit']['stdout']).decode() and native['temporary_area_empty'] and native['wav_unchanged']
    result=analysis();receipt=json.loads((ROOT/'evidence/mono_voice_analysis01.json').read_text(encoding='utf8'))
    for k,v in result.items():assert receipt[k]==v,k
    assert not result['real_time_admitted'] and result['observed_all_full_blocks_miss_deadline']
    assert result['audio_gates_pass'] and not result['strict_all_node_admission'] and result['zero_audio_negative_control_rejected']
    failure=json.loads((ROOT/'evidence/mono_voice_analysis_failure02.json').read_text(encoding='utf8'));recover(failure);assert not failure['passed'] and 'AssertionError' in failure['unchanged_replay']
    assert all(c['heap_allocations']==0 for c in result['costs']) and len(native['profiles'])==4
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256'] and not list((ROOT/'tmp/lab-current').iterdir())
    assert shutil.disk_usage(ROOT).free>1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('mono_voice*') if p!=ROOT/OUT);assert size<=8*1024**2
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{b['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and(not k.startswith('new_') or k=='new_listening')}
    r.update(schema='rf-d/experimental-mono-voice-and-measured-deadline/v1',passed=True,base_commit=b['base_commit'],previous_qa=b['previous_qa'],previous_qa_sha256=sha(ROOT/b['previous_qa']),source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_family_filter_origin_commit=b['base_commit'],experimental_family_filter_origin_commit_pending_self_commit=False,experimental_mono_origin_commit=None,experimental_mono_origin_commit_pending_self_commit=True,experimental_mono_scope='One nominal transposed VCO, own DC, low-note single trigger, full physical contours/filter/two VCAs/J7/FIR, fixed patch, 48 kHz blocks and bounded MIDI domain; experimental offline voice, not complete three-VCO plugin or H128/CV admission; strict 1uV final-node comparison rejected',experimental_mono_tested_samples=480,experimental_mono_tested_events=6,experimental_mono_native_trajectories=4,experimental_mono_latency_samples=48,experimental_mono_costs=result['costs'],experimental_mono_comparisons=result['numerical_comparisons'],experimental_mono_strict_all_nodes_admitted=False,experimental_mono_audio_comparison_admitted=True,experimental_mono_deadline_admitted=False,experimental_mono_receipt_bytes=size,experimental_mono_reference={n:sha(ROOT/n) for n in ['evidence/mono_voice_native01.json','evidence/mono_voice_analysis01.json']},new_unit_test_definitions=4,new_unit_tests_executed=4,new_unit_test_invocations=4,inherited_test_count=old['covered_test_count'],covered_test_count=old['covered_test_count']+4,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,new_library_compile=False,new_cargo_cache=False,new_spice_processes=0,new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,new_native_trajectory_count=4,real_time=False,physical_fidelity=False,physical_cv_general=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    return r

if __name__=='__main__':
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_mono_voice.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        write(ROOT/'evidence/mono_voice_qa_failure01.json',r);raise
    write(ROOT/OUT,r);print('MONO_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['covered_test_count'],r['experimental_mono_receipt_bytes'])
