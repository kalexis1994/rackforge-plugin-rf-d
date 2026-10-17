"""Stationary calibrated circuit family. SI units; no time-varying CV model."""
import hashlib,lzma,math
import numpy as np
from vco1_circuit_reference import crossings
from render_vco1_circuit import coefficients
CV=np.array([-3.1,-2.1,-1.1,-.1]);BUS=np.array([-.125,.125]);H=64
CHANNELS=['saw','triangle','pulse','ic1_sum','neg4_ref','qa','q10']
COLS=[3,4,5,17,6,15,16]
RESISTANCE=np.array([150000.,560000.,51100.,51100.,51100.,15000.])
OUTPUTS=['frequency_hz',*CHANNELS,'wiper_v','panel_saw_a','panel_ground_a','panel_bus_a',
         'bend_a','tune_a','keyboard_a','mod_a','ext_a','range_a','panel_dissipated_w']

def cycle(raw):
    edges=crossings(raw[:,0],raw[:,1],-2.,True);edges=edges[edges>=.015]
    assert len(edges)>=3
    a,b=edges[-2:];t=raw[:,0];knots=np.r_[a,t[(t>a)&(t<b)],b]
    phase=(knots-a)/(b-a);phase[0]=0.;phase[-1]=1.
    data=np.array([np.interp(knots,t,raw[:,col]) for col in COLS])
    c=np.array([coefficients(phase,v,H) for v in data])
    return dict(frequency_hz=float(1/np.mean(np.diff(edges))),coefficients_ri=np.stack([c.real,c.imag],axis=-1).tolist()),edges

def complex_coeff(item):
    a=np.array(item['coefficients_ri']);assert a.shape==(7,H+1,2)
    return a[...,0]+1j*a[...,1]

def lagrange(x):
    w=[];d=[]
    for i in range(4):
        other=[j for j in range(4) if j!=i];den=math.prod(CV[i]-CV[j] for j in other)
        w.append(math.prod(x-CV[j] for j in other)/den)
        d.append(sum(math.prod(x-CV[j] for j in other if j!=k) for k in other)/den)
    return np.array(w),np.array(d)

def interpolate(training,cv,bus):
    if not math.isfinite(cv) or not math.isfinite(bus) or not CV[0]<=cv<=CV[-1] or not BUS[0]<=bus<=BUS[-1]:
        raise ValueError('outside stationary calibrated CV/BUS domain')
    w,d=lagrange(cv);u=(bus-BUS[0])/(BUS[1]-BUS[0]);v=np.array([1-u,u]);dv=np.array([-4.,4.])
    table=np.array([complex_coeff(x['reduction']) for x in training]).reshape(4,2,7,H+1)
    logs=np.array([math.log2(x['reduction']['frequency_hz']) for x in training]).reshape(4,2)
    c=np.einsum('i,j,ijck->ck',w,v,table);dc=np.einsum('i,j,ijck->ck',d,v,table);db=np.einsum('i,j,ijck->ck',w,dv,table)
    log=float(w@logs@v);f=2**log
    return dict(frequency_hz=f,frequency_dcv=f*math.log(2)*float(d@logs@v),frequency_dbus=f*math.log(2)*float(w@logs@dv),c=c,dcv=dc,dbus=db)

def ports(saw,csum,cv,bus):
    w=(saw/12500.+bus/33000.)/(2/12500.+1/33000.)
    p=np.array([(saw-w)/12500.,-w/12500.,(bus-w)/33000.])
    controls=np.full(6,-2.1);controls[2]=cv
    currents=(controls-csum)/RESISTANCE
    power=(saw-w)**2/12500.+w*w/12500.+(bus-w)**2/33000.
    return w,p,currents,power

def sample(training,cv,bus,phase):
    if not math.isfinite(phase) or not 0<=phase<=1:raise ValueError('unit phase required')
    z=interpolate(training,cv,bus);e=np.exp(2j*np.pi*np.arange(H+1)*phase);e[1:]*=2
    v=np.real(z['c']@e);ds=[np.real(z[k]@e) for k in ['dcv','dbus']]
    w,p,cur,power=ports(v[0],v[3],cv,bus)
    values=np.r_[z['frequency_hz'],v,w,p,cur,power];derivatives=[]
    for axis,der in enumerate(ds):
        cvd=float(axis==0);bd=float(axis==1);wd=(der[0]/12500.+bd/33000.)/(2/12500.+1/33000.)
        pd=np.array([(der[0]-wd)/12500.,-wd/12500.,(bd-wd)/33000.]);cd=np.full(6,-der[3]);cd[2]+=cvd;cd/=RESISTANCE
        powerd=2*((v[0]-w)*(der[0]-wd)/12500.+w*wd/12500.+(bus-w)*(bd-wd)/33000.)
        derivatives.append(np.r_[z['frequency_dcv' if axis==0 else 'frequency_dbus'],der,wd,pd,cd,powerd])
    return values,np.array(derivatives)

def spectral_ports(c,cv,bus):
    boundary=np.zeros(H+1,complex);boundary[0]=bus
    w=(c[0]/12500.+boundary/33000.)/(2/12500.+1/33000.)
    panel=np.array([(c[0]-w)/12500.,-w/12500.,(boundary-w)/33000.])
    controls=np.zeros((6,H+1),complex);controls[:,0]=-2.1;controls[2,0]=cv
    return panel,(controls-c[3])/RESISTANCE[:,None]

def encode_window(raw,sink):
    a=np.ascontiguousarray(raw,dtype='<f8').view('<u8');d=a.copy()
    for _ in range(2):d[1:]=d[1:]-d[:-1]
    payload=lzma.compress(d.view(np.uint8).reshape(*a.shape,8).transpose(1,2,0).tobytes(),preset=9)
    offset=sink.tell();sink.write(payload);sink.flush()
    return dict(codec='f64-u64-delta2-byte-shuffle-xz-v1',shape=list(a.shape),offset_bytes=offset,compressed_bytes=len(payload),compressed_sha256=hashlib.sha256(payload).hexdigest(),raw_sha256=hashlib.sha256(a.tobytes()).hexdigest())

def decode_window(item,pack):
    with pack.open('rb') as f:f.seek(item['offset_bytes']);payload=f.read(item['compressed_bytes'])
    assert hashlib.sha256(payload).hexdigest()==item['compressed_sha256'];n,cols=item['shape']
    b=lzma.decompress(payload);assert len(b)==n*cols*8
    a=np.frombuffer(b,dtype=np.uint8).reshape(cols,8,n).transpose(2,0,1).copy().reshape(n,cols*8).view('<u8').reshape(n,cols)
    for _ in range(2):np.add.accumulate(a,axis=0,out=a)
    assert hashlib.sha256(a.tobytes()).hexdigest()==item['raw_sha256']
    return a.view('<f8')
