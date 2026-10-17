"""Admit exact CV/BUS scenes, independent roots and a loaded period; preserve prior domains."""
import base64,hashlib,json,math,re,subprocess,traceback,shutil,struct
from pathlib import Path
import numpy as np
from prepare_dual_chain import ROOT,write,sha
from affine_evidence import Sources,recover
from check_hybrid_voice import packed,unpack
from prepare_vco_cv_load import images,ORIGINS
from vco_cv_load_storage import legacy,decode
from vco_cv_load_analysis import check_capture,compare,config,decimal_audit,parse_roots
from validate_joint_charge_seed import local_links
OUT='evidence/vco_cv_load_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def check_cycle(x):
    m=check_capture(legacy(x));assert canonical(m)==canonical(x['measurements']);assert m['period_spread_relative']<=1e-5 and m['cycle_charge_check']['relative_imbalance']<=.002;return m
def curves(native):
    import gzip
    name='evidence/vco1_circuit_calibration_v1.json.gz';old=json.loads(gzip.decompress((ROOT/name).read_bytes()));assert old['passed'];matrix={};archived_cv={}
    for i,k in enumerate(['low','middle1','middle2','high']):
        x=old['verification'][k];s=x['receipt']['scenario'];c=config(3*i+1);assert s['r8_fraction']==c[0] and s['r11_active_ohm']==c[1] and s['keyboard_v']==-3.1+i and s['imposed_mixer_v']==0 and s['max_step_s']==125e-9 and s['method']=='gear';matrix[3*i+1]=x['measurements'];archived_cv[3*i+1]=s['keyboard_v']
    for x in native['spice'][:8]:matrix[x['scene']]=x['cycle']['measurements']
    assert set(matrix)==set(range(12))
    for bus in range(3):assert all(matrix[a]['frequency_hz']<matrix[a+3]['frequency_hz'] for a in range(bus,bus+9,3))
    out=[]
    for i,x in sorted(matrix.items()):
        b=matrix[(i//3)*3+1];out.append(dict(scene=i,keyboard_v=archived_cv.get(i,config(i)[7]),nominal_keyboard_v=config(i)[7],bus_v=config(i)[3],frequency_hz=x['frequency_hz'],load_frequency_difference_cents=1200*math.log2(x['frequency_hz']/b['frequency_hz']),load_saw_mean_difference_v=x['windows_v']['v(saw_output_9b)']['mean_v']-b['windows_v']['v(saw_output_9b)']['mean_v']))
    return dict(reference=name,reference_sha256=sha(ROOT/name),matrix=out,frequency_increasing_at_each_bus=True,archived_keyboard_construction='-3.1 + integer index',archived_keyboard_representation_error_v=max(abs(v-config(i)[7]) for i,v in archived_cv.items()),finite_load_effect_is_not_an_invariance_gate=True,small_frequency_load_shift_not_claimed_resolved_beyond_method_uncertainty=True)
def audit():
    before=read('evidence/vco_cv_load_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256'];assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else(ROOT/n).read_bytes()).hexdigest()==h,n
    for n,b in saved.items():assert(ROOT/n).read_bytes().startswith(b),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    for n,s in images().items():assert(ROOT/n).read_bytes()==s.encode()
    pre=read('evidence/vco_cv_load_preflight_failure01.json');assert not pre['passed'] and pre['no_compilation_or_integration'] and pre['unchanged_replay']['exit_code']!=0 and b'KeyError' in unpack(pre['unchanged_replay']['stderr']);cor=read('evidence/vco_cv_load_preflight_correction01.json');assert cor['passed'] and cor['numerical_gates_unchanged'] and cor['failure_sha256']==sha(ROOT/'evidence/vco_cv_load_preflight_failure01.json')
    names=sorted(p.relative_to(ROOT).as_posix() for p in(ROOT/'evidence').glob('vco_cv_load_native*.json'));assert len(names)==5;r=read(names[-1]);assert r['passed'] and r['temporary_area_empty'] and not r['new_audio'] and not r['physical_fidelity'] and not r['physical_cv_general'] and not r['real_time']
    pre_source=recover(pre)['tools/check_vco_cv_load.py'];first_source=recover(read(names[0]))['tools/check_vco_cv_load.py'];assert hashlib.sha256(pre_source).hexdigest()==cor['before_sha256'] and hashlib.sha256(first_source).hexdigest()==cor['after_sha256'];assert pre_source.replace(cor['replace_before'].encode(),cor['replace_after'].encode(),1)==first_source
    for n,b in recover(r).items():assert(ROOT/n).read_bytes()==b,n
    for n,h in r['private_used_sha256'].items():assert private[n]==h==sha(ROOT/n),n
    assert r['compiler_sha256']==old['compiler']['sha256']==sha(Path(old['compiler']['path']))
    differences={}
    for name in names[:-1]:
        x=read(name);assert not x['passed'] and x['temporary_area_empty'] and x['failed_phase']=='spice_dc' and 'unchanged_gate_replay' in x
        if 'spice_failed_original' in x:assert x['spice_failed_original']['exit_code']==0 and b'error:' in unpack(x['spice_failed_original']['stderr']).lower() and b'error:' in unpack(x['spice_unchanged_replay']['stderr']).lower()
        else:assert 'AssertionError:' in x['failure'] and 'AssertionError:' in x['unchanged_gate_replay']
        d={n:dict(archived_sha256=hashlib.sha256(b).hexdigest(),current_sha256=sha(ROOT/n)) for n,b in recover(x).items() if(ROOT/n).read_bytes()!=b};assert set(d)<={'tools/check_vco_cv_load.py','tools/vco_cv_load_probe.rs'};differences[name]=d
    for name in ['seed','dc_continuation','dc_refinement','dc_budget']:
        d=read(f'evidence/vco_cv_load_{name}_decision01.json');assert d['passed'] and d['numerical_gates_unchanged'] and d['failure_sha256']==sha(ROOT/d['failure'])
    diagnostic=read('evidence/vco_cv_load_dc_diagnostic01.json');assert diagnostic['passed'] and len(diagnostic['cases'])==2 and all(x['passed'] for x in diagnostic['cases']) and diagnostic['temporary_area_empty']
    budget=read('evidence/vco_cv_load_dc_budget_decision01.json');assert budget['diagnostic_sha256']==sha(ROOT/budget['diagnostic']) and budget['before_sha256']==diagnostic['source_sha256']['tools/check_vco_cv_load.py'] and budget['after_sha256']==sha(ROOT/'tools/check_vco_cv_load.py') and budget['continuation_retired'] and budget['native_budgets_unchanged'] and budget['transient_settings_unchanged']
    # Historical diagnostic checker differs from selected checker; its source image is retained.
    for n,b in recover(diagnostic).items():
        if n!='tools/check_vco_cv_load.py':assert(ROOT/n).read_bytes()==b,n
    assert len(r['dc'])==12 and len(r['spice'])==9 and len(r['profiles'])==2 and r['roots']['exit_code']==0
    for i,x in enumerate(r['dc']):
        assert x['scene']==i and x['exit_code']==0 and len(x['original_root'])==135 and x['rows']==1
        deck=unpack(x['deck']).decode();assert '.nodeset ' in deck and '.options itl1=1000 itl2=1000 ' in deck and '\nop\n' in deck and '\ndc ' not in deck
        assert x['scenario']['keyboard_v']==config(i)[7] and x['scenario']['imposed_mixer_v']==config(i)[3]
    decimal=decimal_audit(unpack(r['roots']['stdout']),[x['original_root'] for x in r['dc']]);assert canonical(decimal)==canonical(r['decimal'])
    dc,_=parse_roots(unpack(r['roots']['stdout']))
    ports=[]
    for i,row in dc.items():
        values=[a+b for a,b in zip(row[3:137],row[137:])];current=(values[12]-values[39])/33000.;balance=abs(current+values[108]);assert balance<=1e-13;ports.append(dict(scene=i,kind='dc',r45_bus_current_a=current,vmixer_current_a=values[108],port_kcl_a=balance))
    for x in [*r['spice'],*r['profiles']]:check_cycle(x['cycle'])
    assert all(x['elapsed_s']<=180 and x['export_bytes']<256*1024*1024 for x in [*r['dc'],*r['spice']])
    method=compare(r['spice'][3]['cycle']['measurements'],r['spice'][8]['cycle']['measurements']);assert canonical(method)==canonical(r['spice_method_comparison'])
    assert [x['maximum_half_ticks'] for x in r['profiles']]==[131072,65536]
    for x in r['profiles']:
        assert x['exit_code']==0 and x['stream_bytes']==x['rows']*136 and x['elapsed_s']<=2400 and x['stream_bytes']<256*1024*1024
        lines=unpack(x['stderr']).decode().splitlines();done=[z.split(',') for z in lines if z.startswith('COMPLETE,')];assert len(done)==1;z=done[0];assert len(z)==8 and int(z[1])==x['maximum_half_ticks'] and int(z[2])==x['rows'] and int(z[3])==15728640000 and 4<=int(z[4])<=x['maximum_half_ticks'] and all(0<=float(v)<=1 for v in z[5:])
        assert len([v for v in lines if v.startswith('INITIAL,')])==len([v for v in lines if v.startswith('FINAL,')])==1 and len([v for v in lines if v.startswith('INTERVAL,')])==2
        initial=list(map(float,next(v for v in lines if v.startswith('INITIAL,')).split(',')[1:]));assert struct.pack('<268d',*initial)==struct.pack('<268d',*dc[5][3:])
        final=list(map(float,next(v for v in lines if v.startswith('FINAL,')).split(',')[1:]));assert len(final)==268;v=[a+b for a,b in zip(final[:134],final[134:])];current=(v[12]-v[39])/33000.;balance=abs(current+v[108]);assert balance<=1e-13;ports.append(dict(profile=x['maximum_half_ticks'],kind='final',r45_bus_current_a=current,vmixer_current_a=v[108],port_kcl_a=balance))
        pairs=[compare(x['cycle']['measurements'],r['spice'][k]['cycle']['measurements']) for k in [3,8]];assert canonical(pairs)==canonical(x['spice_comparisons'])
    temporal=compare(*[x['cycle']['measurements'] for x in r['profiles']]);assert canonical(temporal)==canonical(r['temporal_refinement'])
    intervals=read('evidence/vco_cv_load_intervals01.json');assert intervals['passed'] and intervals['native']==names[-1] and intervals['native_sha256']==sha(ROOT/names[-1]) and len(intervals['intervals'])==4 and intervals['new_trajectories']==0
    for n,b in recover(intervals).items():assert(ROOT/n).read_bytes()==b,n
    unique_pairs=len({x['problem_sha256'] for x in intervals['intervals']});unique_actual_roots=2*unique_pairs;unique_root_sets=12+16+unique_actual_roots;original_rows=134*unique_root_sets;assert 1<=unique_pairs<=4
    assert sum(not x['independent_problem_reused'] for x in intervals['intervals'])==unique_pairs and all(x['native_duplicate_bitwise_identical'] for x in intervals['intervals'] if x['independent_problem_reused'])
    storage=read('evidence/vco_cv_load_storage01.json');assert storage['passed'] and storage['path']==names[-1] and storage['compact_json_sha256']==sha(ROOT/names[-1]) and storage['pack_sha256']==sha(ROOT/storage['pack']) and storage['windows']==11 and storage['all_float64_windows_bitwise_identical'] and storage['restored_original_json_bitwise_identical'] and not storage['unused_samples_removed']
    codec=read('evidence/vco_cv_load_codec_transform_decision01.json');previous=unpack(codec['previous_source_image']);assert hashlib.sha256(previous).hexdigest()==codec['previous_source_sha256']==read('evidence/vco_cv_load_codec_preflight01.json')['source_sha256'] and codec['selected_source_sha256']==sha(ROOT/'tools/vco_cv_load_storage.py') and codec['all_compared_roundtrips_bitwise_identical']
    restored=json.loads(json.dumps(r))
    for group in ['spice','profiles']:
        for x in restored[group]:x['cycle']['window']=packed(decode(x['cycle']))
    assert hashlib.sha256((json.dumps(restored,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()==storage['original_json_sha256']
    assert sha(ROOT/old['new_listening']['path'])==old['new_listening']['sha256']==r['previous_wav_sha256'];assert not list((ROOT/'tmp/lab-current').iterdir())
    size=sum(p.stat().st_size for p in(ROOT/'evidence').glob('vco_cv_load*') if p.is_file() and p!=ROOT/OUT);assert size<=32*1024*1024,size
    available=shutil.disk_usage(ROOT).free;assert available>1024**3
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged and storage['pack'] in staged and not any(n.endswith('.wav') for n in staged)
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links'] and(not k.startswith('new_') or k=='new_listening')}
    result['inherited_legacy_new_fields_reference']=dict(path=before['previous_qa'],sha256=before['previous_qa_sha256'],fields=sorted(k for k in old if k.startswith('new_') and k!='new_listening'))
    result['experimental_vco_cv_load_resource_observations']=dict(free_bytes_at_qa=available,reserve_bytes=1024**3,maximum_export_bytes=max(x.get('export_bytes',x.get('stream_bytes',0)) for x in [*r['dc'],*r['spice'],*r['profiles']]),continuous_disk_reserve_monitor_measured=False)
    result['experimental_vco_cv_load_port_kcl']=ports
    result.update(schema='rf-d/calibrated-vco-cv-bus-contrast/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),experimental_pitch_renderer_origin_commit=before['base_commit'],experimental_pitch_renderer_origin_commit_pending_self_commit=False,experimental_vco_cv_load_admitted=True,experimental_vco_cv_load_scope='12 documentary DC roots, 16 local Radau stage roots, 8 actual stage comparisons deduplicated by controls/history/h, one loaded CV point in two complete native histories; no general CV dynamics or hardware fidelity',experimental_vco_cv_load_reference={n:sha(ROOT/n) for n in names+['evidence/vco_cv_load_intervals01.json','evidence/vco_cv_load_storage01.json',storage['pack']]},experimental_vco_cv_load_dc_count=12,experimental_vco_cv_load_local_stage_roots=16,experimental_vco_cv_load_actual_stage_root_comparisons=8,experimental_vco_cv_load_unique_actual_stage_roots=unique_actual_roots,experimental_vco_cv_load_unique_root_sets=unique_root_sets,experimental_vco_cv_load_new_original_equation_rows=original_rows,experimental_vco_cv_load_temporal_refinement=temporal,experimental_vco_cv_load_spice_method_refinement=method,experimental_vco_cv_load_cv_bus_curves=curves(r),experimental_vco_cv_load_r8_fraction=config(0)[0],experimental_vco_cv_load_r11_ohm=config(0)[1],experimental_vco_cv_load_full_native_cv_v=-2.1,experimental_vco_cv_load_full_native_bus_v=.125,experimental_vco_cv_load_full_native_duration_s=.03,experimental_vco_cv_load_profiles_ticks=[131072,65536],experimental_vco_cv_load_solver_origins={n:dict(private_origin=p,private_origin_sha256=private[p],derived_source_sha256=sources[n]) for n,p in ORIGINS.items()},experimental_vco_cv_load_origin_commit=None,experimental_vco_cv_load_origin_commit_pending_self_commit=True,experimental_vco_cv_load_archived_source_differences=differences,experimental_vco_cv_load_receipt_bytes_before_qa=size,experimental_vco_cv_load_receipt_budget_bytes=32*1024*1024,inherited_test_count=old['covered_test_count'],covered_test_count=old['covered_test_count'],native_test_count=0,inherited_tests_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_global_trajectories_reexecuted=False,inherited_global_trajectory_suite_reexecuted=False,new_unit_test_definitions=0,new_unit_tests_executed=0,new_unit_test_invocations=0,new_original_equation_rows=original_rows,new_vco_cv_load_native_trajectories=2,new_vco_cv_load_spice_trajectories=9,new_audio=False,new_audio_export=False,new_audio_export_count=0,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,physical_cv_model=False,physical_cv_general=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_voice','active_voice_implementation','active_solver','active_initializer','active_readout','active_antialias','active_antialias_coefficients','active_output_pipeline','active_offline_producer','active_nominal_renderer','active_nominal_render_tool','experimental_pitch_producer','experimental_pitch_renderer','experimental_pitch_render_tool','new_listening','private_input_sha256']:assert result[k]==old[k],k
    return result
def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_vco_cv_load.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/vco_cv_load_qa_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/vco_cv_load_qa_failure{k:02d}.json',r);raise
    write(ROOT/OUT,r);print('VCO_CV_LOAD_QA',len(r['source_sha256']),len(r['private_input_sha256']),r['experimental_vco_cv_load_receipt_bytes_before_qa'],flush=True)
if __name__=='__main__':main()
