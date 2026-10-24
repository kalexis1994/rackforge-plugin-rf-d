"""Independent bisection and scalar tangent checks on accepted coupled steps."""
import re,json,traceback,math
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from vco_family import decode_window,lagrange
from family_mixer_analysis import C,other_g
def audit():
    n=json.loads((ROOT/'evidence/family_mixer_native128_01.json').read_text(encoding='utf8'));assert n['passed'];src=Sources(['tools/audit_family_mixer_steps.py','tools/family_mixer_data128.rs','tools/family_mixer_kernel128.rs','tools/family_mixer_analysis.py']);text=(ROOT/'tools/family_mixer_data128.rs').read_text(encoding='utf8');prefix,body=text.split('pub const COEFFICIENTS:',1);pattern=r'[-+]?\d+\.\d+e[-+]\d+'
    logs=np.array(list(map(float,re.findall(pattern,prefix)))).reshape(4,2);v=np.array(list(map(float,re.findall(pattern,body)))).reshape(4,2,7,129,2);v=v[...,0]+1j*v[...,1];results=[]
    for profile in n['profiles']:
        raw=decode_window(profile['window'],ROOT/n['pack']);scene=profile['scene'];cv=[-2.6,-1.6,-.6][scene//2];load=scene%2;w,_=lagrange(cv);cc=np.einsum('i,ijck->jck',w,v);ll=w@logs;cb=(cc[1]-cc[0])/.25;c0=(cc[1]+cc[0])/2;lb=(ll[1]-ll[0])/.25;l0=(ll[1]+ll[0])/2;g=other_g(load)
        def sample(bus,phase):
            c=c0[0]+cb[0]*bus;e=np.exp(2j*np.pi*np.arange(129)*phase);e[1:]*=2;freq=2**(l0+lb*bus);saw=float(np.real(c@e));dsb=float(np.real(cb[0]@e));dsp=float(np.real((c*2j*np.pi*np.arange(129))@e));return freq,(bus-.5*saw)/39250.+g*bus,dsb,dsp
        for k in [1,len(raw)//2]:
            old=raw[k-1];now=raw[k];h=now[0]-old[0];f,i,_,_=sample(old[2],old[1]%1)
            def system(delta):
                bus=old[2]+delta;fnew=2**(l0+lb*bus);phase=old[1]+h*.5*(f+fnew);_,current,db,dp=sample(bus,phase%1);r=delta+h*.5/C*(i+current);j=1+h*.5/C*((1-.5*db)/39250.+g-.5/39250.*dp*h*.5*fnew*math.log(2)*lb);return r,j,phase
            lo,hi=-1e-4,1e-4;assert system(lo)[0]<0<system(hi)[0]
            for _ in range(64):
                m=(lo+hi)/2
                if system(m)[0]<0:lo=m
                else:hi=m
            root=(lo+hi)/2;r,j,phase=system(root);bus_error=abs(old[2]+root-now[2]);phase_error=abs(phase-now[1]);assert bus_error<=1e-12 and phase_error<=1e-10,(scene,k,bus_error,phase_error)
            delta=now[2]-old[2];r,j,_=system(delta);eps=1e-5;fd=(system(delta+eps)[0]-system(delta-eps)[0])/(2*eps);scaled=abs(fd-j)/(1e-10+1e-5*abs(j));assert scaled<=1 and abs(r*C/h)<=1e-13,(scene,k,scaled,r*C/h)
            results.append(dict(scene=scene,step_ns=profile['step_ns'],row=k,bisection_bus_error_v=bus_error,bisection_phase_error_cycles=phase_error,original_capacitor_residual_a=abs(r*C/h),jacobian_scaled_error=scaled))
    coordinate=[]
    for voltage in [-.125,-.016,0.,.125]:
        for slope in [-1.,0.,1.]:
            K=.01;cs=1e-9;z=voltage/K;zd=slope/K;error=max(abs(C*voltage-cs*z/K),abs(C*slope-cs*zd/K),abs(.5*C*voltage**2-.5*cs*z*z));assert error<=1e-18;coordinate.append(error)
    src.unchanged();return dict(passed=True,**src.fields(),native_sha256=sha(ROOT/'evidence/family_mixer_native128_01.json'),step_roots=results,selected_roots=len(results),independent_search='bisection from +/-100 uV bracket, no native root seed',coordinate_identity_max_error=max(coordinate),new_trajectories=0)
if __name__=='__main__':
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/audit_family_mixer_steps.py']).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        write(ROOT/'evidence/family_mixer_steps_failure01.json',r);raise
    write(ROOT/'evidence/family_mixer_steps01.json',r);print('COUPLED_BISECTION',r['selected_roots'])
