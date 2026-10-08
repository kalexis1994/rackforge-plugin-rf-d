"""Lossless bounded-block Radau trace adapter; native float bytes preserved."""
import gzip,hashlib,struct
import numpy as np
COLS=546
BLOCK=512

def encode_block(data):
    if len(data)%(COLS*8):raise ValueError('partial native row')
    a=np.frombuffer(data,dtype='<u8').reshape(-1,COLS)
    d=a.copy();d[1:]=a[1:]^a[:-1]
    return struct.pack('<I',len(a))+d.view(np.uint8).reshape(len(a),COLS,8).transpose(1,2,0).tobytes()

def blocks(path):
    with gzip.open(path,'rb') as f:
        while header:=f.read(4):
            if len(header)!=4:raise ValueError('partial header')
            n=struct.unpack('<I',header)[0]
            if not 1<=n<=BLOCK:raise ValueError('block size')
            b=f.read(n*COLS*8)
            if len(b)!=n*COLS*8:raise ValueError('partial block')
            a=np.frombuffer(b,dtype=np.uint8).reshape(COLS,8,n).transpose(2,0,1).copy().reshape(n,COLS*8).view('<u8').reshape(n,COLS)
            np.bitwise_xor.accumulate(a,axis=0,out=a)
            yield a.view('<f8')

def summary(path,maximum):
    from vco1_circuit_probes import observations
    tick=125e-9/65536;names=[43,48,46,54,44,15,35,7,10,21,4,3,39,20]
    digest=hashlib.sha256();size=0;rows=0;last=None;first=None;top=[];selected={};compact=[];maxima=np.zeros(3);minimum=maximum;actual_max=0
    for a in blocks(path):
        b=a.tobytes();digest.update(b);size+=len(b)
        if not np.isfinite(a).all():raise ValueError('nonfinite trace')
        if not np.array_equal(a[:,:2],np.floor(a[:,:2])):raise ValueError('integer clock')
        for col in (6,274):
            hi=a[:,col:col+134];lo=a[:,col+134:col+268]
            if not np.array_equal(hi+lo,hi) or np.any(np.abs(lo)>np.abs(np.spacing(hi))/2) or np.max(np.abs(hi[:,:98]))>40 or np.max(np.abs(hi[:,98:]))>1:raise ValueError('whole trace memory/domain')
        for k,r in enumerate(a):
            if rows==0:
                if np.any(r[:6]) or np.any(r[140:274]) or not np.array_equal(r[6:274],r[274:542]):raise ValueError('initial layout')
                first=r.copy()
            else:
                if r[0]-last[0]!=r[1] or not 4<=r[1]<=maximum or np.any(r[2:5]>1) or np.any(r[2:5]<0) or not 1<=r[5]<=20:raise ValueError('clock/gates')
                change=float(np.max(np.abs(r[6:104]-last[6:104])))
                top.append((change,rows,last.copy(),r.copy()));top.sort(key=lambda x:(x[0],x[1]),reverse=True);top=top[:2]
                if rows==1:selected[rows]=(last.copy(),r.copy())
                minimum=min(minimum,int(r[1]));actual_max=max(actual_max,int(r[1]));maxima=np.maximum(maxima,r[2:5])
            last=r.copy();rows+=1
        compact.append(np.column_stack([a[:,0]*tick,*[a[:,6+n]+a[:,140+n] for n in names],a[:,542:546]]))
    if rows<2:raise ValueError('empty trace')
    selected[rows-1]=(top[0][2],top[0][3]) if top[0][1]==rows-1 else (None,last)
    # Recover penultimate row without retaining every full-state row.
    tail=None
    for a in blocks(path):
        if tail is not None and len(a)==1:penultimate=tail
        else:penultimate=a[-2].copy() if len(a)>1 else None
        tail=a[-1].copy()
    selected[rows-1]=(penultimate,last)
    for _,index,old,now in top:selected[index]=(old,now)
    coverage=dict(rows=rows,columns=COLS,elapsed_s=float(last[0]*tick),uncompressed_bytes=size,uncompressed_sha256=digest.hexdigest(),minimum_actual_dt_s=minimum*tick,maximum_actual_dt_s=actual_max*tick,max_residual_ratio=float(maxima[0]),max_correction_ratio=float(maxima[1]),max_error_ratio=float(maxima[2]))
    return coverage,first,selected,observations(np.concatenate(compact),None)
