"""No parameter fitting: held-out full nonlinear trajectories vs charge ODE."""
import json,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from vco_family import decode_window,encode_window
from prepare_charge_reduced import Y,GAMMA,exports

def matrices(m,h):
    c=np.array(m['c']);a=-np.array(m['k'])/c[:,None];b=np.array(m['forcing'])/c;l=np.linalg.solve(np.eye(18)-GAMMA*h*a,np.eye(18));su=GAMMA*h*l@b;v=l@(h*(1-GAMMA)*(a@su+b));w=l@(GAMMA*h*b)
    return l@(np.eye(18)+h*(1-GAMMA)*a@l),(1-GAMMA)*v,GAMMA*v+w,l,su

def simulate(m,t,u):
    h=t[1]-t[0];f,u0,u1,l,su=matrices(m,h);xq=np.array(m['xq']);xu=np.array(m['xu']);state=np.zeros(18);q=np.empty((len(t),18));q[0]=state
    for i in range(1,len(t)):state=f@state+u0*u[i-1]+u1*u[i];q[i]=state
    return q@xq.T+u[:,None]*xu

def main():
    sources=Sources(['tools/check_charge_reduced_domain.py']);native=json.loads((ROOT/'evidence/charge_reduced_oracle02.json').read_text(encoding='utf8'));derived=json.loads((ROOT/'evidence/charge_reduced_derivation01.json').read_text(encoding='utf8'));assert native['passed'] and derived['passed'];r=dict(passed=False,**sources.fields(),oracle_sha256=sha(ROOT/'evidence/charge_reduced_oracle02.json'),derivation_sha256=sha(ROOT/'evidence/charge_reduced_derivation01.json'),profiles=[])
    compact=ROOT/'evidence/charge_reduced_compact01.xz';assert not compact.exists();oldpack=ROOT/native['pack'];assert sha(oldpack)==native['pack_sha256']
    try:
        with compact.open('xb') as sink:
            for p in native['profiles']:
                a=decode_window(p['window'],oldpack);m=derived['models'][p['case']];base=np.array(m['dc']);full=a[:,2:70]+a[:,70:138]-base
                reduced=simulate(m,a[:,0],a[:,1]);error=abs(full-reduced);node=float(np.max(error));idx=np.unravel_index(np.argmax(error),error.shape);d=full[:,61]-reduced[:,61];rms=float(np.linalg.norm(d)/max(np.linalg.norm(full[:,61]),1e-30));peak=float(max(abs(d))/max(max(abs(full[:,61])),1e-30));mean=float(abs(np.mean(d)));panel=Y*float(max(abs(full[:,66]-reduced[:,66])));audio=(rms<=.001 and peak<=.003 and mean<=1e-6)or(max(abs(d))<=1e-9 and mean<=1e-6)
                item=dict(case=p['case'],amplitude_v=p['amplitude_v'],step_ns=p['step_ns'],all_nodes_error_v=node,all_nodes_gate_pass=node<=1e-6,worst_row=int(idx[0]),worst_node=int(idx[1]),panel_error_a=panel,panel_gate_pass=panel<=2e-9,j7_rms_relative=rms,j7_peak_relative=peak,j7_mean_error_v=mean,j7_max_error_v=float(max(abs(d))),audio_gate_pass=bool(audio));item['nonlinear_domain_admitted']=bool(item['all_nodes_gate_pass'] and item['panel_gate_pass'] and audio)
                # Retain all output/port samples and sparse complete HIGH/LOW states.
                selected=np.unique(np.r_[np.arange(0,len(a),16),len(a)-1,idx[0]]);item['full_state_rows']=selected.tolist();item['full_state_window']=encode_window(a[selected],sink);signals=np.column_stack([a[:,0],a[:,1],full[:,61],full[:,66],full[:,6]]);item['signal_window']=encode_window(signals,sink);item['original_full_stream_sha256']=p['stream_sha256'];item['original_full_stream_bytes']=p['stream_bytes'];item['full_state_stride']=16;item['full_original_rows_not_all_retained']=True
                sink.flush();assert decode_window(item['full_state_window'],compact).tobytes()==a[selected].tobytes();assert decode_window(item['signal_window'],compact).tobytes()==signals.tobytes();r['profiles'].append(item)
        r.update(passed=True,compact_pack=compact.relative_to(ROOT).as_posix(),compact_sha256=sha(compact),compact_bytes=compact.stat().st_size,original_pack_retirement_pending=True,full_grid_metrics_measured_before_retirement=True,reduced_parameters_fitted_to_reserved_cases=False)
    except Exception:r['failure']=traceback.format_exc();raise
    finally:
        sources.unchanged();write(ROOT/'evidence/charge_reduced_domain01.json',r)
    print('CHARGE_DOMAIN',[(p['case'],p['amplitude_v'],p['step_ns'],p['all_nodes_error_v'],p['nonlinear_domain_admitted']) for p in r['profiles']],r['compact_bytes'])
if __name__=='__main__':main()
