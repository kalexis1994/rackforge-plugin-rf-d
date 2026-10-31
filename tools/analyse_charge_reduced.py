"""Production-clock checks on retained port traces and selected full states."""
import json,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from check_charge_reduced_domain import simulate
from vco_family import decode_window

def metric(left,right):
    d=left-right;ref=float(np.linalg.norm(right));rms=float(np.linalg.norm(d)/max(ref,1e-30));peak=float(max(abs(d))/max(max(abs(right)),1e-30));mean=float(abs(np.mean(d)));maximum=float(max(abs(d)))
    passed=(rms<=.001 and peak<=.003 and mean<=1e-6)or(maximum<=1e-9 and mean<=1e-6)
    return dict(rms_relative=rms,peak_relative=peak,mean_error_v=mean,max_error_v=maximum,passed=bool(passed))

def audit():
    d=json.loads((ROOT/'evidence/charge_reduced_domain01.json').read_text(encoding='utf8'));models=json.loads((ROOT/'evidence/charge_reduced_derivation01.json').read_text(encoding='utf8'))['models'];native=json.loads((ROOT/'evidence/charge_reduced_native01.json').read_text(encoding='utf8'));assert d['passed'] and native['passed'];pack=ROOT/d['compact_pack'];assert sha(pack)==d['compact_sha256'];runtime=[];refinement=[]
    for p in d['profiles']:
        if p['step_ns']!=250:continue
        m=models[p['case']];small=decode_window(p['full_state_window'],pack);signals=decode_window(p['signal_window'],pack);time=np.arange(1537)/384000;u=p['amplitude_v']*(np.sin(2*np.pi*137*time)+.3*np.sin(2*np.pi*1103*time));nodes=simulate(m,time,u);truth=small[:,2:70]+small[:,70:138]-np.array(m['dc']);sampled=np.column_stack([np.interp(small[:,0],time,nodes[:,k]) for k in range(68)]);node=float(max(abs(sampled-truth).flat));assert node<=1e-6,node
        j7=metric(np.interp(signals[:,0],time,nodes[:,61]),signals[:,2]);assert j7['passed'],j7
        bus_error=float(max(abs(np.interp(signals[:,0],time,nodes[:,66])-signals[:,3])));assert bus_error<=1e-6 and bus_error/39250<=2e-9
        runtime.append(dict(case=p['case'],amplitude_v=p['amplitude_v'],node_check_rows=len(small),full_node_checks_are_sparse=True,all_retained_nodes_error_v=node,full_port_bus_error_v=bus_error,panel_error_a=bus_error/39250,j7=j7))
        coarse=next(x for x in d['profiles'] if x['case']==p['case'] and x['amplitude_v']==p['amplitude_v'] and x['step_ns']==500);coarse=decode_window(coarse['signal_window'],pack);fine=signals[::2];assert coarse.shape==fine.shape;z=metric(coarse[:,2],fine[:,2]);assert z['passed'];refinement.append(dict(case=p['case'],amplitude_v=p['amplitude_v'],j7=z,max_bus_error_v=float(max(abs(coarse[:,3]-fine[:,3])))))
    vectors=np.frombuffer(unpack(native['vectors']['stdout']),dtype='<f8').reshape(2,512,91)
    for a in vectors:
        assert np.array_equal(a[:,1:4].view('<u8'),a[:,[23+66,23+6,23+61]].view('<u8'))
    return dict(passed=True,domain_sha256=sha(ROOT/'evidence/charge_reduced_domain01.json'),native_sha256=sha(ROOT/'evidence/charge_reduced_native01.json'),production_clock_hz=384000,production_clock_comparisons=runtime,nonlinear_reference_refinement=refinement,all_native_published_outputs_equal_reconstructed_ports_by_bits=True,all_eight_nonlinear_reserves_admitted=all(p['nonlinear_domain_admitted'] for p in d['profiles']),no_whole_voice_admission=True)

if __name__=='__main__':
    sources=Sources(['tools/analyse_charge_reduced.py'])
    try:r=audit()
    except Exception:
        r=dict(passed=False,**sources.fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/charge_reduced_validation_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/charge_reduced_validation_failure{k:02d}.json',r);raise
    sources.unchanged();r.update(sources.fields());write(ROOT/'evidence/charge_reduced_validation01.json',r);print('CHARGE_VALIDATION',[(x['case'],x['amplitude_v'],x['all_retained_nodes_error_v'],x['j7']['rms_relative']) for x in r['production_clock_comparisons']])
