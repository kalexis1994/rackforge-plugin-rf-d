"""Own eight-junction recovery law with all eighteen physical charge states.

CA-72 inspired partition only: no copied equations, tables or calibration.
G/M and Ebers-Moll parameters are those of the frozen RF-D oracle.
"""
import json
import numpy as np
from prepare_dual_chain import ROOT
from check_hybrid_voice import unpack
from prepare_charge_reduced import Y,GAMMA
VT=1.380649e-23*298.15/1.602176634e-19

def cases():
    r=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'));out=[{} for _ in range(3)]
    for line in unpack(r['export']['stdout']).decode().splitlines():
        z=line.split(',');v=np.array(list(map(float,z[2:])));out[int(z[1])][z[0]]=v if z[0]=='DC' else v.reshape(68,68)
    for c,m in zip(out,r['models']):c['a']=np.array(m['incidence']);c['c']=np.array(m['c'])
    return out

def build(case,h=1/384000):
    dc=case['DC'][:68]+case['DC'][68:];g=case['G'].copy();g[66,66]+=Y
    b=np.zeros(68);b[66]=.5*Y;a=case['a'];c=case['c'];e=np.zeros((8,68));d=np.zeros((68,8));iexp=[]
    def terminal(n):return dc[n] if n<68 else 10.
    for k,(base,col,emit) in enumerate([(16,21,18),(17,68,19),(18,21,20),(19,68,20)]):
        for j,other in [(2*k,emit),(2*k+1,col)]:
            e[j,base]=1/VT
            if other<68:e[j,other]=-1/VT
            iexp.append(1e-14*np.exp((terminal(base)-terminal(other))/VT))
        for node,f,r in [(base,.01,.2),(col,1.,-1.2),(emit,-1.01,1.)]:
            if node<68:d[node,2*k]=f;d[node,2*k+1]=r
    dt=GAMMA*h;matrix=g+case['M']/dt;xh=np.linalg.solve(matrix,a.T*c/dt);xu=np.linalg.solve(matrix,b);xd=np.linalg.solve(matrix,d)
    return dict(dc=dc,g=g,m=case['M'],b=b,a=a,c=c,e=e,d=d,iexp=np.array(iexp),h=h,dt=dt,xh=xh,xu=xu,xd=xd,qh=a@xh,qu=a@xu,qd=a@xd,zh=e@xh,zu=e@xu,p=e@xd)

def law(m,z):
    # Eight-term series avoids expm1(z)-z cancellation at the origin.
    z=np.asarray(z);small=abs(z)<1e-3
    v=np.expm1(z)-z
    v[small]=sum(z[small]**k/float(__import__('math').factorial(k)) for k in range(2,10))
    return m['iexp']*v,m['iexp']*np.expm1(z)

def stage(m,q,u):
    zp=m['zh']@q+m['zu']*u;z=zp.copy()
    for iteration in range(12):
        n,slope=law(m,z);r=z-zp+m['p']@n
        if max(abs(r))<=2e-13:break
        delta=np.linalg.solve(np.eye(8)+m['p']*slope,r);z-=delta
    else:raise ValueError(('root budget',float(max(abs(r)))))
    n,_=law(m,z);x=m['xh']@q+m['xu']*u-m['xd']@n
    return m['qh']@q+m['qu']*u-m['qd']@n,x,iteration,float(max(abs(z-m['e']@x)))

def step(m,q,old,new):
    q1,_,i1,_=stage(m,q,(1-GAMMA)*old+GAMMA*new)
    history=q+(1-GAMMA)/GAMMA*(q1-q)
    q2,x,i2,err=stage(m,history,new)
    return q2,x,max(i1,i2),err

def simulate(m,t,u):
    q=np.zeros(18);out=np.empty((len(t),68));out[0]=m['dc'];maximum=0
    for k in range(1,len(t)):
        q,x,it,err=step(m,q,u[k-1],u[k]);out[k]=m['dc']+x;maximum=max(maximum,it)
    return out,maximum

def dense_stage(m,q,u):
    mat=m['g']+m['m']/m['dt'];rhs=m['a'].T@(m['c']*q)/m['dt']+m['b']*u;x=np.linalg.solve(mat,rhs)
    for i in range(12):
        n,s=law(m,m['e']@x);r=mat@x-rhs+m['d']@n
        if max(abs(r))<=2e-16:break
        x-=np.linalg.solve(mat+(m['d']*s)@m['e'],r)
    else:raise ValueError('dense root budget')
    return x,float(max(abs(r)))
