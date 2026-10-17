"""Held-out spectral and electrical checks, independent Rust queries and derivatives."""
import gzip,json,math,os,subprocess,traceback
import numpy as np
from prepare_dual_chain import ROOT,write,sha
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER
from prepare_vco_family import ORACLE,DATA,image
from vco_family import *
from vco_cv_load_analysis import compare
from vco_cv_load_storage import decode as old_decode
from vco_family_receipts import read as receipt_read,logical_sha
AREA=ROOT/'tmp/lab-current'

def spectral_check(training,cv,bus,target,include_cv=True,include_panel=True):
    z=interpolate(training,cv,bus);c=z['c'];ref=complex_coeff(target);delta=c-ref
    cents=abs(1200*math.log2(z['frequency_hz']/target['frequency_hz']));assert cents<=1.,cents
    waves={}
    for k,name in enumerate(CHANNELS[:3]):
        dc=abs(delta[k,0]);ac=np.linalg.norm(delta[k,1:9])/np.linalg.norm(ref[k,1:9])
        assert dc<=.005 and ac<=.02,(name,float(dc),float(ac))
        waves[name]=dict(dc_error_v=float(dc),harmonics_1_8_relative=float(ac),harmonics_9_64_relative=float(np.linalg.norm(delta[k,9:])/np.linalg.norm(ref[k,9:])))
    p,cv_cur=spectral_ports(c,cv,bus);rp,rcv=spectral_ports(ref,cv,bus)
    panel_dc=float(np.max(np.abs(p[:,0]-rp[:,0])));panel_ac=float(np.max(np.linalg.norm(p[:,1:9]-rp[:,1:9],axis=1)))
    if include_panel:assert panel_dc<=2e-9 and panel_ac<=2e-9,(panel_dc,panel_ac)
    out=dict(frequency_error_cents=cents,waves=waves,panel_dc_error_a=panel_dc,panel_harmonics_1_8_error_a=panel_ac,panel_admitted=include_panel)
    if include_cv:
        sum_dc=float(abs(delta[3,0]));sum_ac=float(np.linalg.norm(delta[3,1:9]));assert sum_dc<=1e-5 and sum_ac<=1e-5,(sum_dc,sum_ac)
        cur_dc=float(np.max(np.abs(cv_cur[:,0]-rcv[:,0])));cur_ac=float(np.max(np.linalg.norm(cv_cur[:,1:9]-rcv[:,1:9],axis=1)))
        assert cur_dc<=2e-9 and cur_ac<=2e-9,(cur_dc,cur_ac)
        balance=float(abs(c[5,0]+c[6,0])/abs(c[5,0]));assert balance<=.002,balance
        out.update(ic1_sum_dc_error_v=sum_dc,ic1_sum_harmonics_1_8_error_v=sum_ac,cv_dc_error_a=cur_dc,cv_harmonics_1_8_error_a=cur_ac,qa_q10_dc_balance_relative=balance,qa_dc_error_a=float(abs(delta[5,0])),q10_dc_error_a=float(abs(delta[6,0])))
    return out

def archived_target(m):
    a=np.array(m['cycle_v']);phase=np.array(m['phase_grid']);c=np.zeros((7,H+1),complex)
    for k,col in enumerate([2,3,4]):c[k]=coefficients(phase,a[:,col],H)
    return dict(frequency_hz=m['frequency_hz'],coefficients_ri=np.stack([c.real,c.imag],axis=-1).tolist())

def audit():
    oracle=receipt_read(ORACLE);assert oracle['passed'] and len(oracle['training'])==8 and len(oracle['reserved'])==3 and len(oracle['method'])==2
    assert (ROOT/DATA).read_bytes()==image(oracle).encode()
    sources=Sources(['tools/validate_vco_family_model.py','tools/vco_family.py','tools/prepare_vco_family.py',DATA,'tools/vco_family_kernel.rs','tools/vco_family_probe.rs','tools/vco_family_receipts.py','docs/VCO_FAMILIA_RESERVA_DENSA.md'])
    result=dict(passed=False,**sources.fields(),oracle=ORACLE,oracle_sha256=logical_sha(ORACLE),training_ids=list(range(8)),reserved_data_used_for_fit=False,training_comparisons=[],held_out_new=[],held_out_archived=[],held_out_bus_zero=[],method_comparisons=[],native_boundary_comparisons=[])
    training=oracle['training'];old=json.loads((ROOT/'evidence/vco_cv_load_native05.json').read_text(encoding='utf8'))
    for x,y in zip(training,old['spice'][:8]):result['training_comparisons'].append(compare(x['measurements'],y['cycle']['measurements']))
    for x in oracle['reserved']:
        s=x['scenario'];result['held_out_new'].append(dict(cv=s['keyboard_v'],bus=s['imposed_mixer_v'],**spectral_check(training,s['keyboard_v'],s['imposed_mixer_v'],x['reduction'])))
    controls=[]
    for name in ['frequency','saw_dc','cv_sum_dc']:
        x=json.loads(json.dumps(oracle['reserved'][1]['reduction']))
        if name=='frequency':x['frequency_hz']*=2**(2/1200)
        elif name=='saw_dc':x['coefficients_ri'][0][0][0]+=.01
        else:x['coefficients_ri'][3][0][0]+=.0001
        try:spectral_check(training,-1.6,.0625,x)
        except AssertionError:controls.append(name)
        else:raise AssertionError('negative control failed: '+name)
    result['negative_controls_rejected']=controls
    archived=json.loads(gzip.decompress((ROOT/'evidence/vco1_circuit_calibration_v1.json.gz').read_bytes()))
    for name in ['low','middle1','middle2','high']:
        x=archived['verification'][name];cv=x['receipt']['scenario']['keyboard_v'];actual_cv=float(np.clip(cv,CV[0],CV[-1]))
        # Archived high is -3.1+3; it remains within the declared domain unchanged.
        assert cv==actual_cv
        result['held_out_archived'].append(dict(name=name,cv=cv,bus=0.,cv_current_claimed=False,**spectral_check(training,cv,0.,archived_target(x['measurements']),False,False)))
    dense=receipt_read('evidence/vco_family_dense01.json');assert dense['passed'] and len(dense['cases'])==4 and dense['family_data_sha256']==sha(ROOT/DATA)
    assert sha(ROOT/dense['pack'])==dense['pack_sha256']
    result['dense_reference_sha256']=sha(ROOT/'evidence/vco_family_dense01.json')
    for x in dense['cases']:
        cv=x['scenario']['keyboard_v'];result['held_out_bus_zero'].append(dict(cv=cv,bus=0.,cv_current_claimed=False,**spectral_check(training,cv,0.,x['reduction'],False)))
        raw=decode_window(x['window'],ROOT/x['window_pack']);a,b=x['settled_crossings_s'][-2:];t=raw[:,0];knots=np.r_[a,t[(t>a)&(t<b)],b];phase=(knots-a)/(b-a);phase[0]=0.;phase[-1]=1.;c=np.zeros((7,H+1),complex)
        for k,col in enumerate([3,4,5]):c[k]=coefficients(phase,np.interp(knots,t,raw[:,col]),H)
        assert np.array_equal(c,complex_coeff(x['reduction'])) and np.max(np.abs(-raw[:,6]/33000.+raw[:,7]))<=2e-12
    for x in oracle['method']:
        result['method_comparisons'].append(compare(x['measurements'],oracle['reserved'][1]['measurements']))
        result['held_out_new'].append(dict(cv=-1.6,bus=.0625,method=x['scenario']['method'],max_step_s=x['scenario']['max_step_s'],**spectral_check(training,-1.6,.0625,x['reduction'])))
    # Native boundary oracles have no IC1_SUM; only channels available in them.
    for x in old['profiles']:
        a=np.frombuffer(old_decode(x['cycle']),dtype='<f8').reshape(x['cycle']['shape']);edges=x['cycle']['settled_crossings_s'];t=a[:,0];aa,bb=edges[-2:];knots=np.r_[aa,t[(t>aa)&(t<bb)],bb];phase=(knots-aa)/(bb-aa);phase[0]=0.;phase[-1]=1.
        c=np.zeros((7,H+1),complex)
        for k,col in enumerate([3,4,5]):c[k]=coefficients(phase,np.interp(knots,t,a[:,col]),H)
        target=dict(frequency_hz=x['cycle']['measurements']['frequency_hz'],coefficients_ri=np.stack([c.real,c.imag],axis=-1).tolist())
        result['native_boundary_comparisons'].append(spectral_check(training,-2.1,.125,target,False))
    # Spectral data regenerate from the retained exact windows without SPICE rerun.
    pack=ROOT/oracle['pack'];assert sha(pack)==oracle['pack_sha256']
    reconstruction=[]
    for x in [*training,*oracle['reserved'],*oracle['method']]:
        raw=decode_window(x['window'],ROOT/x.get('window_pack',oracle['pack']));s=x['scenario'];a,b=x['measurements']['reset_crossings_s'][-2:];t=raw[:,0];knots=np.r_[a,t[(t>a)&(t<b)],b];phase=(knots-a)/(b-a);phase[0]=0.;phase[-1]=1.
        c=np.array([coefficients(phase,np.interp(knots,t,raw[:,col]),H) for col in COLS]);expected=complex_coeff(x['reduction']);assert np.array_equal(c,expected)
        # Independently exported source currents, not reconstructed from family.
        controls=np.array([-2.1,-2.1,s['keyboard_v'],-2.1,-2.1,-2.1]);cv_cur=(controls-raw[:,17,None])/RESISTANCE
        assert np.max(np.abs(cv_cur+raw[:,19:25]))<=2e-12 and np.max(np.abs((s['imposed_mixer_v']-raw[:,13])/33000.+raw[:,18]))<=2e-12
        reconstruction.append(dict(raw_sha256=x['window']['raw_sha256'],coefficients_bitwise_reconstructed=True,rows=len(raw)))
        print('FAMILY_WINDOW_RECONSTRUCTED',len(reconstruction),flush=True)
    result['retained_window_reconstruction']=reconstruction
    # Analytic log-frequency derivative is a quadratic at each BUS endpoint.
    logs=np.array([math.log2(x['reduction']['frequency_hz']) for x in training]).reshape(4,2);minimum=[]
    for j in range(2):
        poly=np.polynomial.polynomial.polyfit(CV,logs[:,j],3);d=np.polynomial.polynomial.polyder(poly);critical=-d[1]/(2*d[2]);nodes=[CV[0],CV[-1]]+([critical] if CV[0]<=critical<=CV[-1] else []);v=min(float(np.polynomial.polynomial.polyval(n,d)) for n in nodes);assert v>0;minimum.append(v)
    result['minimum_log_frequency_dcv_at_bus_endpoints']=minimum
    qold=json.loads((ROOT/'evidence/vco_cv_load_tests01.json').read_text(encoding='utf8'));assert sha(__import__('pathlib').Path(COMPILER))==qold['compiler']['sha256']
    assert not list(AREA.iterdir());env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols',str(ROOT/'tools/vco_family_probe.rs'),'-o',str(AREA/'family.exe')]
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);result['compile']=dict(command=command,exit_code=p.returncode,stdout=packed(p.stdout),stderr=packed(p.stderr));assert p.returncode==0,p.stderr
        p=subprocess.run([str(AREA/'family.exe')],cwd=ROOT,env=env,capture_output=True,timeout=60);result['native']=dict(exit_code=p.returncode,stdout=packed(p.stdout),stderr=packed(p.stderr));assert p.returncode==0 and p.stderr.strip()==b'COMPLETE,245,9,0',p.stderr
        checks=[];fd=[];port=[]
        for line in p.stdout.decode().splitlines():
            z=line.split(',');assert z[0]=='Q' and len(z)==61
            cv,bus,phase=map(float,z[1:4]);actual=np.array(list(map(float,z[4:]))).reshape(3,19);v,d=sample(training,cv,bus,phase);expected=np.vstack([v,d]);scaled=np.abs(actual-expected)/(1e-11+np.abs(expected)*2e-12);assert np.max(scaled)<=1,(cv,bus,phase,np.max(scaled));checks.append(float(np.max(scaled)))
            assert abs(sum(v[9:12]))<=1e-18 and abs(v[1]*v[9]+bus*v[11]-v[18])<=1e-18
            # MNA solve with imposed saw/BUS voltage constraints, independent of condensation.
            g=1/12500.;h=1/33000.;m=np.array([[g,0.,-g,1.,0.],[0.,h,-h,0.,1.],[-g,-h,2*g+h,0.,0.],[1.,0.,0.,0.,0.],[0.,1.,0.,0.,0.]])
            solved=np.linalg.solve(m,np.array([0.,0.,0.,v[1],bus]));original=np.array([-solved[3],-solved[2]*g,-solved[4]]);pe=float(np.max(np.abs(original-v[9:12])));assert pe<=1e-18;port.append(pe)
            if CV[0]<cv<CV[-1] and -.125<bus<.125:
                for axis in range(2):
                    eps=1e-3;offset=np.zeros(2);offset[axis]=eps
                    plus=sample(training,cv+offset[0],bus+offset[1],phase)[0];minus=sample(training,cv-offset[0],bus-offset[1],phase)[0];approx=(plus-minus)/(2*eps);err=np.abs(approx-d[axis])/(1e-10+1e-5*np.abs(d[axis]));assert np.max(err)<=1,(cv,bus,phase,axis,float(np.max(err)));fd.append(float(np.max(err)))
        assert len(checks)==245
        result.update(rust_queries=245,invalid_domains_checked=9,heap_allocations_in_measured_queries=0,rust_python_max_scaled_error=max(checks),derivative_comparisons=len(fd),derivative_max_scaled_error=max(fd),panel_mna_max_error_a=max(port),panel_kcl_gate_a=1e-18,panel_dissipation_gate_w=1e-18)
    finally:
        exe=AREA/'family.exe'
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    sources.unchanged();result.update(passed=True,temporary_area_empty=not list(AREA.iterdir()),new_audio=False,real_time=False,physical_fidelity=False,dynamic_cv_admitted=False)
    return result

def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,**Sources(['tools/validate_vco_family_model.py','tools/vco_family_kernel.rs','tools/vco_family_probe.rs',DATA]).fields(),failure=traceback.format_exc())
        try:audit();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        k=1
        while(ROOT/f'evidence/vco_family_model_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/vco_family_model_failure{k:02d}.json',r);raise
    write(ROOT/'evidence/vco_family_model01.json',r);print('FAMILY_MODEL_PASS',max(x['frequency_error_cents'] for x in [*r['held_out_new'],*r['held_out_bus_zero']]),r['rust_queries'],flush=True)
if __name__=='__main__':main()
