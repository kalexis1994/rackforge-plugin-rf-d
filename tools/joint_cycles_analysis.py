"""Lossless lab records, reset brackets and same-clock electrical comparisons."""
import hashlib,math,struct
from decimal import Decimal,localcontext
import numpy as np
TICK=125e-9/65536;ANCHOR=131072000;GOAL=2752512000
FIELDS=['residual','correction','lte','ramp','schmitt','saw','tri','pulse','bus','cursor','j7','panel_a','c27_a','bus_kcl','qa_a','q10_a','q7_a','c1_kcl']
DTYPE=np.dtype([('ticks','<u8'),('half_ticks','<u4'),('attempts','<u4')]+[(n,'<f8') for n in FIELDS])
CHECK=struct.Struct('<QIIII400d')
def require(ok,msg):
    if not ok:raise ValueError(msg)
def trace(path,complete=True,start_ticks=0):
    size=path.stat().st_size
    with path.open('rb') as f:require(f.read(8)==b'RFJTRC01','trace header')
    require(DTYPE.itemsize==160,'explicit record size')
    if complete:require((size-8)%160==0,'complete trace records')
    rows=np.fromfile(path,dtype=DTYPE,offset=8,count=(size-8)//160)
    require(len(rows)>0 and len(rows)%2==0 if complete else len(rows)>0,'complete half-step pairs')
    for n in FIELDS:require(np.isfinite(rows[n]).all(),'finite '+n)
    require((rows['ticks'][1:]>rows['ticks'][:-1]).all(),'monotonic clock')
    difference=np.diff(np.concatenate([np.array([start_ticks],dtype=np.uint64),rows['ticks']]))
    require((difference==rows['half_ticks']).all(),'exact half clocks')
    half=rows['half_ticks'];require(((half>=4)&((half&(half-1))==0)).all(),'half domain')
    require(((rows['attempts']>=1)&(rows['attempts']<=20)).all(),'attempt domain')
    for n in ['residual','correction','lte']:require(((rows[n]>=0)&(rows[n]<=1)).all(),'native gate '+n)
    if complete:
        for n in ['half_ticks','attempts','lte']:require(np.array_equal(rows[n][::2],rows[n][1::2]),'pair metadata '+n)
        raw=path.read_bytes();require(hashlib.sha256(raw).digest()==hashlib.sha256(b'RFJTRC01'+rows.tobytes()).digest(),'trace byte roundtrip')
    require(np.max(np.abs(rows['bus_kcl']))<=1e-12 and np.max(np.abs(rows['c1_kcl']))<=1e-12,'interface KCL')
    return rows
def checkpoint(raw):
    require(len(raw)==CHECK.size,'checkpoint size');values=CHECK.unpack(raw)
    ticks,proposal,maximum,attempts,reserved=values[:5];high=values[5:205];low=values[205:]
    require(reserved==0 and ticks%8==0 and attempts==20 and maximum in [65536,32768],'checkpoint metadata')
    require(8<=proposal<=2*maximum and proposal&(proposal-1)==0,'checkpoint proposal')
    for k,(h,l) in enumerate(zip(high,low)):
        limit=1 if 98<=k<133 else 40
        require(math.isfinite(h) and math.isfinite(l) and abs(h)<=limit and (abs(h)!=limit or h*l<=0),'checkpoint domain')
        s=h+l;v=s-h;e=(h-(s-v))+(l-v);require((s,e)==(h,l),'normalized memory')
    require(CHECK.pack(*values)==raw,'checkpoint byte roundtrip')
    return dict(ticks=ticks,proposal=proposal,maximum=maximum,high=high,low=low,raw_sha256=hashlib.sha256(raw).hexdigest())
def checkpoints(path):
    raw=path.read_bytes();require(raw[:8]==b'RFJCKP01' and (len(raw)-8)%CHECK.size==0,'checkpoint stream')
    return [checkpoint(raw[i:i+CHECK.size]) for i in range(8,len(raw),CHECK.size)]
def reset_measurements(rows):
    ids=np.flatnonzero((rows['ramp'][:-1]<-2)&(rows['ramp'][1:]>=-2))+1
    require(len(ids)>=2,'two reset crossings')
    crossings=[]
    for i in ids:
        a,b=rows[i-1],rows[i];alpha=(-2-float(a['ramp']))/(float(b['ramp'])-float(a['ramp']))
        clock=float(a['ticks'])+alpha*float(int(b['ticks'])-int(a['ticks']))
        crossings.append(dict(time_s=clock*TICK,bracket_ticks=[int(a['ticks']),int(b['ticks'])],half_ticks=int(b['half_ticks'])))
    begin,end=crossings[0]['time_s'],crossings[1]['time_s'];t=rows['ticks'].astype(float)*TICK
    window=(t>=begin)&(t<=end);extrema={}
    for n in ['saw','tri','pulse','bus','j7']:
        x=rows[n][window];x=np.concatenate([x,[np.interp(begin,t,rows[n]),np.interp(end,t,rows[n])]])
        extrema[n]=dict(min_v=float(np.min(x)),max_v=float(np.max(x)))
    return dict(crossings=crossings,cycle_begin_s=begin,cycle_end_s=end,period_s=end-begin,frequency_hz=1/(end-begin),extrema=extrema,steady_periodicity_admitted=False)
def compare(a,b):
    require([c['ticks'] for c in a]==[c['ticks'] for c in b],'shared checkpoint clocks')
    points=[]
    with localcontext() as ctx:
        ctx.prec=100
        for x,y in zip(a[1:],b[1:]):
            differences=[Decimal.from_float(h)+Decimal.from_float(l)-Decimal.from_float(j)-Decimal.from_float(m) for h,l,j,m in zip(x['high'],x['low'],y['high'],y['low'])]
            ratios=[abs(v)/Decimal.from_float(2e-9 if 98<=k<133 else 2e-6) for k,v in enumerate(differences)]
            maximum=max(ratios);require(maximum<=1,'same-clock state refinement '+str(maximum))
            points.append(dict(ticks=x['ticks'],max_error_ratio=str(maximum),worst_coordinate=ratios.index(maximum)))
    return points
