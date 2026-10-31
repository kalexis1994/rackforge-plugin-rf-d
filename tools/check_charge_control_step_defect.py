"""Isolate method error at actual endpoints; never infer it from linear interpolation."""
import json
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from analyse_charge_control import audio
from vco_family import decode_window

def main():
    sources=Sources(['tools/check_charge_control_step_defect.py']);base=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'));exp=json.loads((ROOT/'evidence/charge_control_exponential01.json').read_text(encoding='utf8'));fine=json.loads((ROOT/'evidence/charge_control_refinement01.json').read_text(encoding='utf8'));m=base['models'];last=fine['profiles'][-1];signals=decode_window(last['signal_window'],ROOT/fine['pack']);results=[]
    for filename in ['charge_control_rust01.json','charge_control_exp_rust01.json']:
        native=json.loads((ROOT/'evidence'/filename).read_text(encoding='utf8'));a=np.frombuffer(unpack(native['vectors']['stdout']),dtype='<f8').reshape(1537,111);worst=0.;qworst=0.
        for k in range(1,len(a)):
            idx=int(a[k,2]);model=m[idx];t=exp['transitions'][idx];dc=np.array(model['dc']);cap=np.array(model['incidence'])@dc;q=(a[k-1,7:25]+a[k-1,25:43])-cap;expected=np.array(t['f'])@q+np.array(t['u0'])*a[k-1,1]+np.array(t['u1'])*a[k,1];nodes=dc+np.array(model['xq'])@expected+np.array(model['xu'])*a[k,1];worst=max(worst,float(max(abs(nodes-a[k,43:]))));qworst=max(qworst,float(max(abs(expected-((a[k,7:25]+a[k,25:43])-cap)))))
        sample_audio=audio(a[:,5],np.interp(a[:,0],signals[:,0],signals[:,3]));results.append(dict(native=filename,native_sha256=sha(ROOT/'evidence'/filename),local_linear_endpoint_defect_v=worst,local_charge_voltage_endpoint_defect_v=qworst,physical_j7_at_published_clock=sample_audio,physical_reference_port_interpolation_used=True))
    assert results[1]['local_linear_endpoint_defect_v']<=1e-11
    sources.unchanged();r=dict(passed=True,**sources.fields(),results=results,defect_is_against_same_constitutive_ode_not_hardware=True,linear_node_interpolation_is_not_a_valid_method_error_estimator=True,no_physical_or_rt_admission=True);write(ROOT/'evidence/charge_control_step_defect01.json',r);print('CONTROL_STEP_DEFECT',results)
if __name__=='__main__':main()
