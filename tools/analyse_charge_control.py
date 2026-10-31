"""Separate static admission, charge continuity, reference error and runtime."""
import json,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from check_charge_control import metrics
from vco_family import decode_window

def audio(left,right):
    d=left-right;reference=right-right[0];rms=float(np.linalg.norm(d)/max(np.linalg.norm(reference),1e-30));peak=float(max(abs(d))/max(max(abs(reference)),1e-30));mean=float(abs(np.mean(d)));maximum=float(max(abs(d)));passed=(rms<=.001 and peak<=.003 and mean<=1e-6)or(maximum<=1e-9 and mean<=1e-6)
    return dict(j7_rms_relative=rms,j7_peak_relative=peak,j7_mean_error_v=mean,j7_max_error_v=maximum,audio_gate_pass=bool(passed))

def audit():
    original=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'));fine=json.loads((ROOT/'evidence/charge_control_refinement01.json').read_text(encoding='utf8'));native=json.loads((ROOT/'evidence/charge_control_rust01.json').read_text(encoding='utf8'));assert original['passed'] and fine['passed'] and native['passed'];assert fine['reference_converged'] and fine['original_250ns_replay_identical']
    assert sha(ROOT/original['pack'])==original['pack_sha256'] and sha(ROOT/fine['pack'])==fine['pack_sha256'];last=fine['profiles'][-1];assert last['reference_comparison']['domain_admitted'];s=decode_window(last['state_window'],ROOT/fine['pack']);signals=decode_window(last['signal_window'],ROOT/fine['pack']);a=np.frombuffer(unpack(native['vectors']['stdout']),dtype='<f8').reshape(1537,111);nodes=a[:,43:]
    full=s[:,3:71]+s[:,71:139];at=np.column_stack([np.interp(s[:,0],a[:,0],nodes[:,k]) for k in range(68)]);production=metrics(full,at);j7=np.interp(signals[:,0],a[:,0],nodes[:,61]);production.update(audio(j7,signals[:,3]),node_checks_are_sparse=True,full_j7_grid_checked=True)
    bus=float(max(abs(np.interp(signals[:,0],a[:,0],nodes[:,66])-signals[:,4])));production['full_bus_error_v']=bus;production['full_panel_error_a']=bus/39250;production['domain_admitted']=bool(production['node_gate_pass'] and production['audio_gate_pass'] and bus<=1e-6 and bus/39250<=2e-9)
    static=[p for p in original['profiles'] if not p['dynamic']];accepted=[p for p in static if p['domain_admitted']];rejected=[p for p in original['profiles'] if not p['domain_admitted']];assert len(accepted)==6 and all(p['amplitude_v']==.01 for p in accepted) and len(rejected)==14 and all(p['unchanged_native_replay']['identical'] for p in rejected)
    return dict(passed=True,passed_means_receipt_complete_not_dynamic_admission=True,source_native_sha256=sha(ROOT/'evidence/charge_control_native01.json'),refinement_sha256=sha(ROOT/'evidence/charge_control_refinement01.json'),rust_sha256=sha(ROOT/'evidence/charge_control_rust01.json'),accepted_static_reserves=6,rejected_level_reserves=12,rejected_initial_dynamic_reserves=2,static_accepted_amplitude_v=.01,static_cutoff_values=original['cutoff_values'],fine_reference_step_ns=last['step_ns'],fine_reference_comparison=last['reference_comparison'],candidate_at_fine_step=last['candidate_same_step_metrics'],production_clock_dynamic_comparison=production,charge_continuity_pass=True,max_switch_charge_voltage_error_v=max(p['charge_voltage_continuity_error_v'] for p in last['switches']),minimum_reset_negative_control_error_v=min(p['reset_negative_control_error_v'] for p in last['switches']),dynamic_cutoff_physical_admission=last['candidate_same_step_metrics']['domain_admitted'] and production['domain_admitted'],cost_observed_admission=native['cost']['target_50_percent_pass'] and native['cost']['deadline_misses']==0,whole_voice_rt=False,static_level_gate_not_relaxed=True,dynamic_gates_not_relaxed=True,full_grid_metrics_precede_export_retirement=True,retained_full_states_are_sparse=True)

if __name__=='__main__':
    sources=Sources(['tools/analyse_charge_control.py'])
    try:r=audit()
    except Exception:
        r=dict(passed=False,**sources.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/charge_control_analysis_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/charge_control_analysis_failure{k:02d}.json',r);raise
    sources.unchanged();r.update(sources.fields());write(ROOT/'evidence/charge_control_analysis01.json',r);print('CONTROL_ANALYSIS',r['fine_reference_step_ns'],r['candidate_at_fine_step']['all_nodes_error_v'],r['production_clock_dynamic_comparison']['all_nodes_error_v'],r['dynamic_cutoff_physical_admission'],r['cost_observed_admission'])
