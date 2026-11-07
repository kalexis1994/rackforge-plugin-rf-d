"""Audit original native bytes; query the candidate at the oracle clock."""
import json,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from check_recovery_port_native import summarize_bench
from recovery_port_input_model import cases,build,simulate,step
from check_charge_control import metrics
from vco_family import decode_window

def audit():
    native=json.loads((ROOT/'evidence/recovery_port_native01.json').read_text(encoding='utf8'));assert not native['passed'] and native['bench']['exit_code']==0 and native['vectors']['exit_code']==0 and native['temporary_area_empty']
    assert 'int(z[4])==128' in native['failure'];cost=summarize_bench(unpack(native['bench']['stdout']));replay_cost=summarize_bench(unpack(native['unchanged_replay']['stdout']));assert native['unchanged_replay']['exit_code']==0
    a=np.frombuffer(unpack(native['vectors']['stdout']),dtype='<f8').reshape(3,1537,93);corpus=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'));cs=cases();comparisons=[];implementation=[]
    for idx in range(3):
        v=a[idx];m=build(cs[idx]);expected,it=simulate(m,v[:,1],v[:,2]);error=float(np.max(abs(expected-v[:,25:])));assert error<=1e-10
        qe=float(np.max(abs((v[:,25:]-m['dc'])@m['a'].T-v[:,7:25])));panel=float(max(abs((expected[:,66]-.5*v[:,2])/39250-v[:,6])));assert qe<=1e-11 and panel<=1e-14
        implementation.append(dict(index=idx,node_error_v=error,charge_error_v=qe,panel_error_a=panel))
        profile=next(p for p in corpus['profiles'] if p['index']==idx and p['amplitude_v']==.1 and p['step_ns']==250 and not p['dynamic']);signals=decode_window(profile['signal_window'],ROOT/corpus['pack']);states=decode_window(profile['state_window'],ROOT/corpus['pack']);x=np.empty((len(signals),68));cache={}
        for j in range(len(signals)):
            k,rem=divmod(j*12,125)
            if rem==0:x[j]=v[k,25:];continue
            if rem not in cache:cache[rem]=build(cs[idx],rem/(125*384000))
            u=v[k,2]+rem/125*(v[k+1,2]-v[k,2]);q,delta,_,_=step(cache[rem],v[k,7:25],v[k,2],u);x[j]=m['dc']+delta
        full=states[:,3:71]+states[:,71:139];result=metrics(full,x[profile['state_rows']]);ports=np.zeros_like(x);candidate=np.zeros_like(x)
        for col,node in [(3,61),(4,66),(5,6)]:ports[:,node]=signals[:,col];candidate[:,node]=x[:,node]
        port=metrics(ports,candidate);admitted=bool(result['node_gate_pass'] and port['audio_gate_pass'] and port['panel_gate_pass']);comparisons.append(dict(index=idx,amplitude_v=.1,sparse_nodes=result,dense_ports=port,domain_admitted=admitted,partial_maps=len(cache),candidate_restarted_from_own_rust_charge_only=True))
        print('RECOVERY_PRODUCTION',idx,result['all_nodes_error_v'],port['j7_rms_relative'],admitted,flush=True)
    return dict(passed=True,native_sha256=sha(ROOT/'evidence/recovery_port_native01.json'),corpus_sha256=sha(ROOT/'evidence/charge_control_native01.json'),implementation_comparisons=implementation,cost=cost,unchanged_replay_cost=replay_cost,original_cost_used_not_best_repetition=True,parser_correction_only=True,first_output_frames=80,subsequent_output_frames=128,production_comparisons=comparisons,whole_voice_rt=False,hardware_fidelity=False,dynamic_cutoff_admitted=False,cost_admitted=cost['target_50_percent_pass'] and cost['deadline_misses']==0,production_sparse_node_coverage=True,no_reference_state_seeding=True,antialias_fidelity_not_measured=True)

if __name__=='__main__':
    sources=Sources(['tools/analyse_recovery_port.py','tools/check_recovery_port_native.py','tools/recovery_port_input_model.py']);r=dict(passed=False,**sources.fields());k=1
    while(ROOT/f'evidence/recovery_port_analysis{k:02d}.json').exists():k+=1
    try:r.update(audit())
    except Exception:
        r['failure']=traceback.format_exc()
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    sources.unchanged();write(ROOT/f'evidence/recovery_port_analysis{k:02d}.json',r);print('RECOVERY_ANALYSIS',r['passed'],r.get('cost'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
