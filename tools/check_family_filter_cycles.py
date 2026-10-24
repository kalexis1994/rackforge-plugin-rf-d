"""Whole first cycles, physical C27 balance and algebraic restrictions."""
import json,math,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from vco_family import decode_window,coefficients
def measure(raw):
    end=float(np.interp(1.,raw[-2:,1],raw[-2:,0]));knots=np.r_[0.,raw[(raw[:,0]>0)&(raw[:,0]<end),0],end];phase=knots/end;phase[0]=0.;phase[-1]=1.
    c=np.array([coefficients(phase,np.interp(knots,raw[:,0],raw[:,k]),8) for k in [2,3,4,5,6]])
    return 1/end,c
def audit():
    n=json.loads((ROOT/'evidence/family_filter_sdirk_native01.json').read_text(encoding='utf8'));assert n['passed'] and len(n['profiles'])==4;sources=Sources(['tools/check_family_filter_cycles.py','tools/family_filter_sdirk_kernel.rs','docs/FAMILIA_FILTRO_RESTRICCIONES.md']);gamma=1-1/math.sqrt(2);results=[];spectra=[];base_controls=[];dup_controls=[]
    for x in n['profiles']:
        a=decode_window(x['window'],ROOT/n['pack']);assert a.shape==(x['rows'],11) and np.isfinite(a).all();z=unpack(x['stderr']).decode().strip().split(',');assert len(z)==7 and z[0]=='COMPLETE' and int(z[1])==len(a)-1 and max(float(z[2]),float(z[3]))<=1 and z[4:]==['0','2','true']
        h=x['step_ns']*1e-9;current=(1-gamma)*a[1:,9]+gamma*a[1:,6];q=float(h*sum(current));dq=float(1e-5*((a[-1,2]-a[-1,3])-(a[0,2]-a[0,3])));through=float(h*sum(abs(current)));error=abs(q-dq);assert error<=1e-16+through*1e-8,(x['cv_v'],x['step_ns'],error,through)
        algebraic=float(np.max(abs(a[1:,10])));assert algebraic<=1e-13;f,c=measure(a);spectra.append((f,c));basechange=float(np.linalg.norm(c[1,1:]));assert basechange>1e-5;base_controls.append(basechange);dup=float(np.max(abs(a[1:,10]+a[1:,5])));assert dup>1e-13;dup_controls.append(dup)
        results.append(dict(cv_v=x['cv_v'],step_ns=x['step_ns'],frequency_hz=f,charge_error_c=error,charge_throughput_c=through,algebraic_kcl_max_a=algebraic,bus_min_v=float(a[:,2].min()),bus_max_v=float(a[:,2].max()),base_min_v=float(a[:,3].min()),base_max_v=float(a[:,3].max()),j7_peak_v=float(max(abs(a[:,4]))),heap_allocations=0,initial_point_is_source_jump=True))
    comparison=[]
    for idx in [0,2]:
        fa,a=spectra[idx];fb,b=spectra[idx+1];cents=abs(1200*math.log2(fa/fb));assert cents<=1;d=a-b;r=dict(cv_v=n['profiles'][idx]['cv_v'],frequency_error_cents=cents,signals={})
        for k,name in enumerate(['bus','base_q29','j7','panel_bus','c27']):
            dc=float(abs(d[k,0]));norm=float(np.linalg.norm(d[k,1:]));ref=float(np.linalg.norm(b[k,1:]))
            if k<2:assert max(dc,norm)<=1e-5,(name,dc,norm)
            elif k==2:assert dc<=.0005 and(norm<=1e-6 or norm/max(ref,1e-30)<=.02),(name,dc,norm,ref)
            else:assert max(dc,norm)<=2e-9,(name,dc,norm)
            r['signals'][name]=dict(dc_error=dc,harmonics_1_8_norm_error=norm,reference_harmonic_norm=ref)
        comparison.append(r)
    rejected=json.loads((ROOT/'evidence/family_filter_constraint_replay01.json').read_text(encoding='utf8'));assert rejected['passed'] and rejected['unchanged_output_identical'] and rejected['observed_max_residual_a']>1e-13
    sources.unchanged();return dict(passed=True,**sources.fields(),native_sha256=sha(ROOT/'evidence/family_filter_sdirk_native01.json'),profiles=results,refinement=comparison,negative_controls=dict(trapezoidal_algebraic_residual_a=rejected['observed_max_residual_a'],fixed_base_trace_min_missing_harmonic_v=min(base_controls),duplicate_r45_min_kcl_error_a=min(dup_controls),trace_controls_are_not_additional_circuit_trajectories=True),new_spice_processes=0,new_audio=False,initial_capacitor_charge_preserved=True,full_settled_cycle_claim=False)
if __name__=='__main__':
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/check_family_filter_cycles.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/family_filter_cycles_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/family_filter_cycles_failure{k:02d}.json',r);raise
    write(ROOT/'evidence/family_filter_cycles01.json',r);print('FILTER_CYCLES_PASS',max(x['signals']['bus']['harmonics_1_8_norm_error'] for x in r['refinement']))
