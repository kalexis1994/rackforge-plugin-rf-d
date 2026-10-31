"""Numerical vs deadline verdicts are deliberately separate."""
import json,traceback,math
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources,recover
from check_hybrid_voice import unpack
from check_mono_voice import parse

def diff(a,b,pre_key=False):
    a=np.array(a);b=np.array(b);d=a-b;assert a.shape==b.shape and np.isfinite(d).all()
    rms=float(np.sqrt(np.mean(d*d)));ref=float(np.sqrt(np.mean(b*b)));peak=float(max(abs(d)));base=float(max(abs(b)));mean=float(abs(np.mean(d)))
    assert mean<=1e-6 and((rms<=1e-6 and peak<=1e-6) if pre_key else(ref>0 and base>0 and rms<=.001*ref and peak<=.003*base)),(rms,ref,peak,base,mean)
    return dict(samples=len(a),rms_error_v=rms,reference_rms_v=ref,rms_relative=rms/max(ref,1e-30),max_error_v=peak,reference_peak_v=base,peak_relative=peak/max(base,1e-30),mean_error_v=mean)

def volts(bits):
    a=np.array(bits,dtype='<u8').view('<f8');assert np.isfinite(a).all();return a[:118]+a[118:]

def audit():
    name='evidence/mono_voice_native01.json';r=json.loads((ROOT/name).read_text(encoding='utf8'));assert r['passed'] and len(r['profiles'])==4 and r['temporary_area_empty'] and r['wav_unchanged'];recover(r)
    profiles=[parse(unpack(p['stdout']),p['args'][0]=='reference') for p in r['profiles']]
    # JSON object keys restore as strings; canonicalize both serialized domains.
    for p,x in zip(r['profiles'],profiles):assert json.dumps(p['measurements'],sort_keys=True)==json.dumps(json.loads(json.dumps(x)),sort_keys=True)
    a,b,c,ref=profiles
    initial=[x['states']['INITIAL'] for x in profiles[:3]];assert initial[0]==initial[1]==initial[2]
    comparisons={}
    for tag,left,right in [('partition64_128',a,b),('time_refinement',a,c),('old_producer',a,ref)]:
        indices=sorted(set(left['audio'])&set(right['audio']));comparisons[tag]=dict(whole=diff([left['audio'][k] for k in indices],[right['audio'][k] for k in indices]),windows={})
        for label,lo,hi in [('pre_key',48,96),('attack_legato',96,240),('release',240,336),('second_attack',336,384),('second_release',384,480)]:
            ix=[k for k in indices if lo<=k<hi];comparisons[tag]['windows'][label]=diff([left['audio'][k] for k in ix],[right['audio'][k] for k in ix],label=='pre_key')
        nodal=abs(volts(left['states']['FINAL'])-volts(right['states']['FINAL']));error=float(max(nodal))
        comparisons[tag].update(final_all_nodes_max_error_v=error,final_worst_node=int(np.argmax(nodal)),strict_nodal_gate_v=1e-6,strict_nodal_gate_pass=error<=1e-6)
    try:diff([0.]*len(a['audio']),list(a['audio'].values()))
    except AssertionError:zero_control_rejected=True
    else:zero_control_rejected=False
    assert zero_control_rejected
    costs=[]
    for p,x in zip(r['profiles'][:3],profiles[:3]):
        block=int(p['args'][0]);blocks=[b for b in x['blocks'] if b['frames']==block];ratios=[b['budget_ratio'] for b in blocks];elapsed=[b['elapsed_s'] for b in blocks]
        costs.append(dict(block_frames=block,profile=p['args'][1],complete_voice=True,warmup_excluded=False,full_blocks=len(blocks),partial_blocks=len(x['blocks'])-len(blocks),duration_s=sum(b['frames'] for b in x['blocks'])/48000,processing_s=sum(b['elapsed_s'] for b in x['blocks']),rt_factor=sum(b['elapsed_s'] for b in x['blocks'])/(sum(b['frames'] for b in x['blocks'])/48000),median_block_s=float(np.median(elapsed)),p95_block_s=float(np.quantile(elapsed,.95)),max_block_s=max(elapsed),budget_s=block/48000,max_budget_ratio=max(ratios),deadline_misses=sum(v>1 for v in ratios),target_50_percent_pass=all(v<=.5 for v in ratios),heap_allocations=sum(b['heap'] for b in x['blocks']),setup=x['setup'],iterations=sum(b['iterations'] for b in x['blocks']),accepted_calls=sum(b['calls'] for b in x['blocks']),adaptive_attempts=sum(b['attempts'] for b in x['blocks'])))
    # A failing deadline is a measured rejection, not a failed correctness receipt.
    real_time=all(x['target_50_percent_pass'] for x in costs)
    return dict(passed=True,passed_means_harness_complete_not_all_admissions=True,native_sha256=sha(ROOT/name),numerical_comparisons=comparisons,audio_gates_pass=True,strict_all_node_admission=all(x['strict_nodal_gate_pass'] for x in comparisons.values()),strict_relative_gates_even_below_1uv=True,zero_audio_negative_control_rejected=zero_control_rejected,costs=costs,real_time_admitted=real_time,observed_all_full_blocks_miss_deadline=all(x['deadline_misses']==x['full_blocks'] for x in costs),one_vco_nominal_transposition=True,not_h128_family=True,hardware_fidelity=False,voice_scene_ms=10,phase_and_capacitor_resets=0,output_latency_samples=48,late_tail_admission_inherited_not_remeasured=True,benchmark_is_short_observation_not_wcet=True,reference_shared_nominal_source=True,independent_physical_vco_oracle=False,new_audio=False)

if __name__=='__main__':
    sources=Sources(['tools/analyse_mono_voice.py'])
    try:r=audit()
    except Exception:
        r=dict(passed=False,**sources.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/mono_voice_analysis_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/mono_voice_analysis_failure{k:02d}.json',r);raise
    sources.unchanged();r.update(sources.fields());write(ROOT/'evidence/mono_voice_analysis01.json',r);print('MONO_ANALYSIS',r['real_time_admitted'],[(x['block_frames'],x['rt_factor']) for x in r['costs']])
