"""Audit exact FOH dense queries from Rust states; no physical reference seeding."""
import json,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from check_charge_control import metrics
from analyse_charge_control import audio
from prepare_charge_control_exp import transition
from vco_family import decode_window

def audit():
    base=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'));ref=json.loads((ROOT/'evidence/charge_control_refinement01.json').read_text(encoding='utf8'));r=json.loads((ROOT/'evidence/charge_control_exp_rust01.json').read_text(encoding='utf8'));prepared=json.loads((ROOT/'evidence/charge_control_exponential01.json').read_text(encoding='utf8'));assert base['passed'] and ref['reference_converged'] and r['passed'] and prepared['passed'];a=np.frombuffer(unpack(r['vectors']['stdout']),dtype='<f8').reshape(1537,111);models=base['models'];last=ref['profiles'][-1];small=decode_window(last['state_window'],ROOT/ref['pack']);signals=decode_window(last['signal_window'],ROOT/ref['pack']);caps=[np.array(m['incidence'])@np.array(m['dc']) for m in models];dc=[np.array(m['dc']) for m in models];xq=[np.array(m['xq']) for m in models];xu=[np.array(m['xu']) for m in models];cache={};nodes=np.empty((len(signals),68))
    for n in range(len(signals)):
        k,rem=divmod(n*12,125)
        if rem==0:nodes[n]=a[k,43:];continue
        mid=(k+.5)/384000;idx=1 if mid<.001 or mid>=.003 else 2 if mid<.002 else 0;key=(idx,rem)
        if key not in cache:
            m=transition(models[idx],rem/(125*384000));cache[key]=[np.array(m[z]) for z in ['f','u0','u1']]
        f,u0,u1=cache[key];q=(a[k,7:25]+a[k,25:43])-caps[idx];u=a[k,1]+rem/125*(a[k+1,1]-a[k,1]);q=f@q+u0*a[k,1]+u1*u;nodes[n]=dc[idx]+xq[idx]@q+xu[idx]*u
    truth=small[:,3:71]+small[:,71:139];sparse=nodes[last['state_rows']];result=metrics(truth,sparse);result.update(audio(nodes[:,61],signals[:,3]));bus=float(max(abs(nodes[:,66]-signals[:,4])));result.update(full_bus_error_v=bus,full_panel_error_a=bus/39250,node_checks_are_sparse=True,ports_are_full_grid=True);result['domain_admitted']=bool(result['node_gate_pass'] and result['audio_gate_pass'] and bus<=1e-6 and bus/39250<=2e-9)
    linear=np.column_stack([np.interp(small[:,0],a[:,0],a[:,43+k]) for k in range(68)]);linear_error=float(max(abs(linear-truth).flat))
    return dict(passed=True,rust_sha256=sha(ROOT/'evidence/charge_control_exp_rust01.json'),preparation_sha256=sha(ROOT/'evidence/charge_control_exponential01.json'),fine_reference_sha256=sha(ROOT/'evidence/charge_control_refinement01.json'),fine_reference_step_ns=last['step_ns'],dense_partial_transition_count=len(cache),dense_partial_transition_from_rust_state_not_reference=True,dense_comparison=result,linear_node_interpolation_comparison_error_v=linear_error,cost=r['cost'],dynamic_cutoff_physical_admission=result['domain_admitted'],whole_voice_rt=False,no_fir_rate_or_audio_fidelity_admission=True,old_sdirk_rejections_retained=True)
if __name__=='__main__':
    sources=Sources(['tools/analyse_charge_control_exp.py','docs/CHARGE_CONTROL_DENSE.md'])
    try:r=audit()
    except Exception:
        r=dict(passed=False,**sources.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/charge_control_exp_analysis_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/charge_control_exp_analysis_failure{k:02d}.json',r);raise
    sources.unchanged();r.update(sources.fields());write(ROOT/'evidence/charge_control_exp_analysis01.json',r);print('CONTROL_EXP_ANALYSIS',r['dense_comparison'],r['linear_node_interpolation_comparison_error_v'])
