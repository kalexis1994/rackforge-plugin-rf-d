"""SI electrical boundaries and phase-defined comparisons, no waveform fitting."""
import math
import numpy as np
from vco_family import interpolate,coefficients
from vco1_circuit_reference import crossings

CVS=[-2.6,-1.6,-.6]
C=10e-6
def other_g(load):
    assert load in [0,1]
    return 1/33000.+(2/39250.+1/17250. if load else 0.)
def initial_bus(training,cv,load):
    lo=interpolate(training,cv,-.125)['c'][0,0].real;hi=interpolate(training,cv,.125)['c'][0,0].real
    slope=(hi-lo)/.25;intercept=(hi+lo)/2
    return float(.5*intercept/(1+39250*other_g(load)-.5*slope))
def spectral(raw,a,b,columns):
    t=raw[:,0];knots=np.r_[a,t[(t>a)&(t<b)],b];phase=(knots-a)/(b-a);phase[0]=0.;phase[-1]=1.
    c=np.array([coefficients(phase,np.interp(knots,t,raw[:,i]),8) for i in columns])
    return np.stack([c.real,c.imag],axis=-1).tolist()
def complex_rows(values):
    a=np.array(values);return a[...,0]+1j*a[...,1]
def capture_spice(raw,load):
    e=crossings(raw[:,0],raw[:,1],-2.,True);e=e[e>=.015];assert len(e)>=3
    a,b=e[-3],e[-1];idx=max(0,int(np.searchsorted(raw[:,0],a))-2);last=raw[idx:].copy();bus=raw[:,6]
    assert np.min(last[:,6])>=-.125 and np.max(last[:,6])<=.125
    panel=(bus-raw[:,5])/33000.;other=other_g(load)*bus
    # t=0 is the constrained OP: C27 current is zero while .ic holds BUS.
    # The claimed KCL domain is the retained late transient window.
    kcl=float(np.max(np.abs((panel+other+raw[:,7])[idx:])));assert kcl<=1e-10,kcl
    knots=np.r_[a,raw[(raw[:,0]>a)&(raw[:,0]<b),0],b];v=np.interp(knots,raw[:,0],bus);i=np.interp(knots,raw[:,0],raw[:,7]);q=float(np.trapezoid(i,knots));dq=C*(v[-1]-v[0]);through=float(np.trapezoid(abs(i),knots));err=abs(q-dq)
    assert err<=1e-14 or err/max(through,1e-30)<=.002,(q,dq,through)
    controls=(CVS[0],CVS[1],CVS[2])
    # Columns output [saw,tri,pulse,BUS,panelBUS,other,C27,IC1_SUM,KEYBOARD].
    projected=np.column_stack([raw[:,0],raw[:,2:5],bus,panel,other,raw[:,7:10]])
    return last,dict(crossings_s=e.tolist(),start_s=float(a),start_bus_v=float(np.interp(a,raw[:,0],bus)),reference_end_s=float(b),frequency_hz=float(1/np.mean(np.diff(e[-3:]))),spectral_ri=spectral(projected,e[-2],e[-1],range(1,10)),kcl_max_a=kcl,charge_error_c=err,charge_throughput_c=through,bus_min_v=float(last[:,6].min()),bus_max_v=float(last[:,6].max()))
def capture_native(raw):
    # Native columns: time, unwrapped phase, BUS, saw/tri/pulse, wiper,
    # panelBUS, other, C27, IC1_SUM, KEYBOARD, Newton residual/correction.
    e=[]
    for k in [1.,2.]:
        j=int(np.searchsorted(raw[:,1],k));assert 0<j<len(raw)
        e.append(float(np.interp(k,raw[j-1:j+1,1],raw[j-1:j+1,0])))
    # Oracle exports i(VKEYBOARD), opposite to current entering the VCO.
    p=np.column_stack([raw[:,0],raw[:,3:6],raw[:,2],raw[:,7:11],-raw[:,11]])
    return dict(frequency_hz=1/(e[1]-e[0]),spectral_ri=spectral(p,*e,range(1,10)),crossings_s=e,bus_min_v=float(raw[:,2].min()),bus_max_v=float(raw[:,2].max()))
def compare(actual,reference):
    a=complex_rows(actual['spectral_ri']);b=complex_rows(reference['spectral_ri']);d=a-b
    cents=abs(1200*math.log2(actual['frequency_hz']/reference['frequency_hz']));assert cents<=1.,cents
    out=dict(frequency_error_cents=cents,signals={})
    for i,name in enumerate(['saw','triangle','pulse','bus','panel_bus','other','c27','ic1_sum','keyboard']):
        dc=float(abs(d[i,0]));norm=float(np.linalg.norm(d[i,1:]))
        if i<3:ac=norm/float(np.linalg.norm(b[i,1:]));assert dc<=.005 and ac<=.02,(name,dc,ac)
        elif i in [3,7]:assert max(dc,norm)<=1e-5,(name,dc,norm)
        else:assert max(dc,norm)<=2e-9,(name,dc,norm)
        out['signals'][name]=dict(dc_error=dc,harmonics_1_8_error=norm)
    return out
