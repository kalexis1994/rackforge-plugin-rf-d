"""Separate observed cycle DC/AC drift and record memories after gate release."""
import json
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_sustained_voice import START,BOUNDARIES
from joint_cycles_analysis import require,TICK

def main():
    name='evidence/voice_sustained_reference01.json';ref=json.loads((ROOT/name).read_text(encoding='utf8'));require(ref['passed'],'admitted trajectory')
    names=[name,'tools/diagnose_sustained_voice.py','tools/prepare_sustained_voice.py'];sources={n:sha(ROOT/n) for n in names};private={};observations=[]
    for p,d in zip(ref['profiles'],ref['cycle_diagnostics']):
        path=f"references-local/sustained-voice01/{p['maximum_half_ticks']}/selected.txt";private[path]=sha(ROOT/path);require(private[path]==p['input_sha256'][path],'admitted trace')
        rows=np.array([list(map(float,line.split(',')[1:])) for line in (ROOT/path).read_text(encoding='utf8').splitlines() if line.startswith('OBS,')]);t=rows[:,0]*TICK;phase=np.linspace(0.,1.,2049);edges=d['held_cycle_edges_s'];waves=[np.interp(a+phase*(b-a),t,rows[:,4]) for a,b in zip(edges[:-1],edges[1:])]
        means=[float(np.trapezoid(v,phase)) for v in waves];centered=[v-mean for v,mean in zip(waves,means)]
        state=lambda tick:next(g['values'] for g in p['grids'] if g['ticks']==tick)
        def values(tick):
            s=state(tick);v=lambda k:s[k]+s[k+229]
            return dict(ticks=tick,c2_v=v(205),c7_v=v(221),loudness_v=v(203),reset_driver_v=v(217),q25_base_v=v(225),q25_collector_v=v(226),q15_base_v=v(227),q15_collector_v=v(228),c4_v=v(223)-v(225),board4_q18_base_v=v(165))
        boundaries=[values(START+delta) for delta in BOUNDARIES]
        observations.append(dict(maximum_half_ticks=p['maximum_half_ticks'],cycle_mean_j7_v=means,cycle_mean_change_v=means[-1]-means[0],centered_cycle_difference_max_v=float(np.max(abs(centered[-1]-centered[0]))),raw_cycle_difference_max_v=d['cycle_difference_max_v'],
            boundary_memories=boundaries,c2_change_during_hold_v=boundaries[2]['c2_v']-boundaries[1]['c2_v'],c2_change_during_release_v=boundaries[3]['c2_v']-boundaries[2]['c2_v'],c7_change_during_release_v=boundaries[3]['c7_v']-boundaries[2]['c7_v'],
            source_release_observed=True,circuit_cause_identified=False,physical_model_d_behavior_identified=False))
    require(sources=={n:sha(ROOT/n) for n in names} and private=={n:sha(ROOT/n) for n in private},'unchanged diagnostics inputs')
    write('evidence/voice_sustained_diagnostic01.json',dict(passed=True,source_sha256=sources,source_sha256_after=sources,private_used_sha256=private,private_used_sha256_after=private,observations=observations,
        repetition_candidate_unchanged=ref['repetition_candidate'],numerical_gates_changed=False,dc_subtraction_only_in_diagnostic=True,dc_subtraction_applied_to_native_wav=False,physical_fidelity=False))
    print('SUSTAINED_DIAGNOSTIC',[(q['maximum_half_ticks'],q['cycle_mean_change_v'],q['centered_cycle_difference_max_v'],q['c2_change_during_release_v']) for q in observations])
if __name__=='__main__':main()
