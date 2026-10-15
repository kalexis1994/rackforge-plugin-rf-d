"""Promote the extended nominal note, independent FIR evidence and one listening view."""
import base64,hashlib,json,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from check_long_note_aa import analyse,arrays
from check_long_note_aa_design import audit as design_audit
from check_long_note_aa_filter import audit as filter_audit
from prepare_long_note_aa import images
from export_long_note_aa import wav_bytes,ARTIFACT
from validate_joint_charge_seed import local_links
OUT='evidence/long_note_aa_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def audit():
    before=read('evidence/long_note_aa_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert(ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private) and ARTIFACT not in private
    for n,s in images().items():assert(ROOT/n).read_bytes()==s.encode(),n
    names=['evidence/long_note_aa_design01.json','evidence/long_note_aa_native01.json','evidence/long_note_aa_filter01.json','evidence/long_note_aa_audit01.json','evidence/long_note_aa_listening01.json']
    design,native,filtered,original,listening=[read(n) for n in names]
    for r in [design,native,filtered,original,listening]:
        assert r['passed']
        for n,data in recover(r).items():assert(ROOT/n).read_bytes()==data,n
    assert canonical(design_audit())==canonical(design['filters'])
    assert native['control']==before['previous_qa'].replace('tests01','native03') and native['control_sha256']==sha(ROOT/native['control'])
    assert len(native['profiles'])==2 and native['temporary_area_empty'] and canonical(analyse(native['profiles']))==canonical(native['analysis'])
    tests=native['unit_tests'];assert tests['exit_code']==0 and tests['stderr']=='' and '2 passed; 0 failed' in unpack(tests['stdout']).decode()
    assert filtered['native']==names[1] and filtered['native_sha256']==sha(ROOT/names[1]) and filtered['design']==names[0] and filtered['design_sha256']==sha(ROOT/names[0]) and filtered['temporary_area_empty']
    report=filter_audit(unpack(filtered['stdout']),names[1]);assert all(canonical(filtered[k])==canonical(v) for k,v in report.items())
    assert original['native']==names[1] and original['native_sha256']==sha(ROOT/names[1]) and original['dc_rows']==238 and original['dynamic_rows']==11424 and original['original_rows']==11662
    assert not original['independent_original_trajectory'] and len(original['dc'])==2 and len(original['initial_and_key_seams'])==4
    assert all(d['rows']==119 and d['residual_a']<=20e-12 and d['correction_v']<=2e-9 for d in original['dc'])
    assert all(p['pairs']==24 and p['original_rows']==5712 and p['max_residual_a']<=20e-12 and p['max_correction_v']<=2e-9 for p in original['profiles']) and all(s['state_bits_preserved'] for s in original['initial_and_key_seams'])
    for n,h in original['used_private_sha256'].items():assert private[n]==h==sha(ROOT/n),n
    assert listening['inputs']=={n:sha(ROOT/n) for n in names[:4]} and listening['temporary_area_empty'] and listening['regenerable'] and not listening['required_private_input'] and listening['new_private_input_ids']==0
    d,a,seam,g=arrays(unpack(native['profiles'][1]['stdout']));wav=wav_bytes(a['AA8'][:14400]);assert hashlib.sha256(wav).hexdigest()==listening['sha256']==sha(ROOT/ARTIFACT) and len(wav)==listening['bytes']==57656
    assert listening['frames']==14400 and listening['rate_hz']==48000 and listening['duration_s']==.3 and listening['channels']==1 and listening['v_per_full_scale']==1. and not listening['normalized'] and not listening['faded'] and not listening['dithered'] and listening['float32_roundtrip_max_error_v']<=1e-9
    for r in [native,filtered]:
        assert r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path'])) and r['library_sha256']==old['public_assembly_library_sha256']==sha(ROOT/old['public_assembly_library_path'])
    assert not list((ROOT/'tmp/lab-current').iterdir());size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('long_note_aa*.json') if p!=ROOT/OUT);assert size<=8*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    for r in [design,native,filtered,original,listening]:assert set(r['source_sha256'])<=set(sources)
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    readout='crates/rf-d-circuit/src/j7_oversampled_readout.rs';antialias='crates/rf-d-circuit/src/j7_antialias.rs';coeff='crates/rf-d-circuit/src/j7_antialias_coefficients.rs'
    result.update(schema='rf-d/long-nominal-note-and-antialias/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),long_note_aa_admitted=True,long_note_aa_duration_s=.3,long_note_aa_key_on_s=.001,long_note_aa_key_off_s=.2,long_note_aa_electrical_end_s=.301,long_note_aa_raw_rate_hz=384000,long_note_aa_output_rate_hz=48000,long_note_aa_frames=14400,long_note_aa_anchor_samples=1,long_note_aa_dc_gain=1.,long_note_aa_causal_latency_s=.001,long_note_aa_offline_latency_compensated=True,long_note_aa_real_right_support=True,long_note_aa_left_prehistory='constant own DC J7',long_note_aa_temporal_refinement=native['analysis']['temporal_refinement'],long_note_aa_rate_refinement=[p['rate_refinement'] for p in native['analysis']['profiles']],long_note_aa_filters=design['filters'],long_note_aa_original_rows=11662,long_note_aa_reference={n:sha(ROOT/n) for n in names},long_note_aa_receipt_bytes_before_qa=size,long_note_aa_receipt_budget_bytes=8*1024*1024,previous_active_readout=old['active_readout'],previous_active_readout_origin_commit=before['base_commit'],active_readout=readout,active_readout_source_sha256=sources[readout],active_readout_rate_hz=384000,active_readout_origin_commit=None,active_readout_origin_commit_pending_self_commit=True,active_antialias=antialias,active_antialias_source_sha256=sources[antialias],active_antialias_coefficients=coeff,active_antialias_coefficients_source_sha256=sources[coeff],active_antialias_decimation=8,active_antialias_origin_commit=None,active_antialias_origin_commit_pending_self_commit=True,inherited_test_count=old['inherited_test_count']+old['new_unit_test_definitions'],inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_global_trajectories_reexecuted=False,new_long_note_trajectories=2,new_original_equation_rows=11662,new_unit_test_definitions=2,new_unit_tests_executed=2,new_audio=True,new_audio_voltage_buffer=True,new_audio_export=True,new_audio_export_count=1,new_listening=listening,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,antialias_nominal_rate_convergence=True,bandlimited=False,universal_alias_free_claim=False,real_time=False,physical_fidelity=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    result.update(covered_test_count=result['inherited_test_count']+2,native_test_count=2,new_used_private_sha256=original['used_private_sha256'])
    for k in ['active_solver','active_voice','active_voice_implementation','active_initializer','cost_ratio','private_input_sha256']:assert result[k]==old[k],k
    return result
def main():
    try:r=audit()
    except Exception:
        sources=Sources(['tools/validate_long_note_aa.py']);r=dict(passed=False,**sources.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/long_note_aa_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/long_note_aa_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('LONG_NOTE_AA_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['long_note_aa_receipt_bytes_before_qa'],flush=True)
if __name__=='__main__':main()
