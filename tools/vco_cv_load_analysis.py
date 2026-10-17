"""Frozen electrical gates and bounded reanalysis of exact retained cycle windows."""
import math,re
from decimal import Decimal,localcontext
import numpy as np
from check_hybrid_voice import packed,unpack
from vco1_circuit_reference import measure,crossings
from vco1_circuit_probes import observations,comparison,GATES
from render_vco1_circuit import coefficients
import vco1_radau_reference as oracle

R8=.2613404652606161;R11=521.3126579373712
TICK=125e-9/65536
def config(i):return [R8,R11,1e-11,[-.125,0.,.125][i%3],0.,-2.1,-2.1,[-3.1,-2.1,-1.1,-.1][i//3],-2.1,-2.1,-2.1]
def tail(raw):
    e=crossings(raw[:,0],raw[:,1],-2.,True);e=e[e>=.015];assert len(e)>=3
    first=max(0,int(np.searchsorted(raw[:,0],e[-3]))-2);return raw[first:].copy(),e
def capture(raw):
    a,e=tail(raw);m=observations(a,None);all_period=np.diff(e);m['frequency_hz']=float(1/np.mean(all_period));m['period_spread_relative']=float(np.ptp(all_period)/np.mean(all_period));m['reset_crossings_s']=e.tolist()
    assert m['period_spread_relative']<=GATES['period_spread_relative'] and m['cycle_charge_check']['relative_imbalance']<=GATES['cycle_charge_relative'],m
    return dict(shape=list(a.shape),window=packed(a.astype('<f8').tobytes()),settled_crossings_s=e.tolist(),measurements=m)
def restore(item):return np.frombuffer(unpack(item['window']),dtype='<f8').reshape(item['shape'])
def check_capture(item):
    a=restore(item);m=observations(a,None);e=np.array(item['settled_crossings_s']);m['frequency_hz']=float(1/np.mean(np.diff(e)));m['period_spread_relative']=float(np.ptp(np.diff(e))/np.mean(np.diff(e)));m['reset_crossings_s']=e.tolist();return m
def shape(a,b):
    out={};phase=np.linspace(0.,1.,1025)
    for col,name in [(2,'saw'),(3,'triangle'),(4,'pulse')]:
        x=coefficients(phase,np.array(a['cycle_v'])[:,col],8);y=coefficients(phase,np.array(b['cycle_v'])[:,col],8)
        dc=float(abs(x[0]-y[0]));ac=float(np.linalg.norm(x[1:]-y[1:])/np.linalg.norm(y[1:]));assert dc<=.005 and ac<=.02,(name,dc,ac);out[name]=dict(dc_error_v=dc,ac_harmonics_1_8_relative=ac)
    return out
def compare(a,b):
    r=comparison(a,b);assert r['frequency_error_cents']<=1 and max(r['output_extrema_error_v'].values())<=.005,r;r['shape']=shape(a,b);return r
def parse_roots(raw):
    dc={};local={}
    for line in raw.decode().splitlines():
        z=line.split(',')
        if z[0]=='DC':dc[int(z[1])]=list(map(float,z[2:]));assert len(dc[int(z[1])])==271
        elif z[0]=='LOCAL':local[tuple(map(int,z[1:4]))]=list(map(float,z[4:]));assert len(local[tuple(map(int,z[1:4]))])==270
    assert set(dc)==set(range(12)) and len(local)==16
    return dc,local
def decimal_audit(raw,spice_dc):
    dc,local=parse_roots(raw);out=dict(dc=[],local=[])
    with localcontext() as ctx:
        ctx.prec=100
        for i,row in dc.items():
            forcing,residual,correction,*states=row;assert residual<=1 and correction<=1;nodes=states[:134];assert states[134:]==[0.]*134
            target=spice_dc[i];nv=float(max(abs(a-b) for a,b in zip(nodes[:98],target[:98])));na=float(max(abs(a-b) for a,b in zip(nodes[98:],target[98:134])));forcing_err=abs(forcing-target[134]);assert nv<=2e-7 and na<=2e-10 and forcing_err<=2e-10,(i,nv,na,forcing_err)
            rr,j,g=oracle.circuit.reference_decimal(nodes,nodes,0.,config(i));rr[43]+=Decimal.from_float(forcing);g-=Decimal.from_float(forcing);kcl=float(max(map(abs,rr[:98])));constraint=float(max(map(abs,rr[98:])));balance=float(abs(sum(rr[:98])+g));assert kcl<=2e-14 and constraint<=2e-12 and balance<=1e-11,(i,kcl,constraint,balance)
            out['dc'].append(dict(scene=i,node_error_v=nv,branch_error_a=na,forcing_error_a=forcing_err,kcl_a=kcl,constraint_v=constraint,ground_balance_a=balance))
        for i in [0,2,9,11]:
            old=[Decimal.from_float(a)+Decimal.from_float(b) for a,b in zip(dc[i][3:137],dc[i][137:])]
            for ticks in [4,32]:
                p=oracle.solve(old,ticks*TICK,config(i));rr,j,g=oracle.system([p['stage'],p['endpoint']],old,ticks*TICK,config(i))
                for stage,key in enumerate(['stage','endpoint']):
                    n=local[(i,ticks,stage)];assert n[0]<=1 and n[1]<=1;values=[Decimal.from_float(a)+Decimal.from_float(b) for a,b in zip(n[2:136],n[136:])];err=[abs(a-b) for a,b in zip(values,p[key])];nv=float(max(err[:98]));na=float(max(err[98:]));kcl=float(max(map(abs,rr[stage*134:stage*134+98])));constraint=float(max(map(abs,rr[stage*134+98:(stage+1)*134])));balance=float(abs(sum(rr[stage*134:stage*134+98])+g[stage]));assert nv<=2e-7 and na<=2e-10 and kcl<=2e-14 and constraint<=2e-12 and balance<=1e-11,(i,ticks,stage,nv,na,kcl,constraint,balance)
                    out['local'].append(dict(scene=i,ticks=ticks,stage=stage,node_error_v=nv,branch_error_a=na,kcl_a=kcl,constraint_v=constraint,ground_balance_a=balance,independent_decimal=[str(v) for v in p[key]]))
    return out
