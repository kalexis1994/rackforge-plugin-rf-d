"""Independent original Amount star and original chain KCL; no native Jacobian."""
import json, math, struct
from pathlib import Path
import numpy as np
from c5_trigger_reference import network, NAMES, charge_increment
from chain_charge_reference import matrix
from circuit66_dc_vectors import dc_evaluator
from circuit66_vca_dc_vectors import boundary_values
from circuit66_vca_release_probes import CAPS
from cutoff_j7_vectors import setup
ROOT=Path(__file__).resolve().parents[1]
N=118
def ci(k):
    if k==5:return 55
    if k==32:return 54
    if 62<=k<66:return k-28
    return 56+k-(k>5)-(k>32)-4*(k>65)
def source(t):return [.2*math.sin(2*math.pi*100*(t-.001)) if t>=.001 else 0.,0.,0.,0.,0.]
def expanded(x):return [*x,(x[32]/25000+x[34]/47000)/(2/25000+1/47000)]
class Original:
    def __init__(self):
        self.n=network(False)
        for k in ['VCA_CONTROL_LOAD','TAIL']:del self.n.rails[k]
        self.n.nodes=NAMES+['VCA_CONTROL_LOAD','TAIL','AMOUNT_CURSOR']
        self.n.index={v:k for k,v in enumerate(self.n.nodes)}
        self.n.alias={v:v for v in set(self.n.nodes)|set(self.n.rails)}
        self.values=boundary_values(setup(200.),0.,2.)
        self.audio=dc_evaluator(self.values,self.values[4])
        self.y=matrix(1)
    def dc(self,x,key=0.,short=False,t=0.):
        assert len(x)==119
        self.n.controls=__import__('dataclasses').replace(self.n.controls,external_s_short=short)
        # S remains OFF in this bank; static network resistor list is fixed.
        assert not short
        dual,_=self.n.evaluate([*x[:56],x[118]],key,jacobian=False)
        r=np.array([*dual[:56],*([0.]*62),dual[56]])
        a=[x[ci(k)] for k in range(68)]
        ar,_=self.audio(a[:66]);ar=[-v if k<48 else v for k,v in enumerate(ar)]
        ar[5]-=(a[5]-a[65])/680.
        ar[32]-=a[32]/68000.
        ar[62:66]=[0.]*4
        bus=(self.y@np.array([*source(t),a[66]]))[5]
        i=(a[22]-a[67])/25500.;ar[22]+=i
        for k,v in enumerate([*ar,bus,-i]):r[ci(k)]+=v
        return r
    def fd(self,x,key=0.,short=False,t=0.):
        x=np.array(x);j=np.empty((119,119))
        for k in range(119):
            a=x.copy();b=x.copy();a[k]+=1e-6;b[k]-=1e-6
            j[:,k]=(self.dc(a,key,short,t)-self.dc(b,key,short,t))/2e-6
        return j
    def reduced(self,x,key=0.,short=False,t=0.):return self.dc(expanded(x),key,short,t)[:118]
    def reduced_fd(self,x,key=0.,short=False,t=0.):
        j=np.empty((N,N));x=np.array(x)
        for k in range(N):
            a=x.copy();b=x.copy();a[k]+=1e-6;b[k]-=1e-6
            j[:,k]=(self.reduced(a,key,short,t)-self.reduced(b,key,short,t))/2e-6
        return j
    def seed(self):
        dual=json.loads((ROOT/'references-local/c5-trigger02/original_inputs.json').read_text(encoding='utf8'))['dc'][0]['original_root'][:54]
        a=[*self.values[5]['node_v'],0.,self.values[5]['node_v'][22]]
        x=dual+[a[32],a[5]]+[0.]*62
        for k in range(68):
            if 62<=k<66:continue
            x[ci(k)]=a[k]
        return expanded(x)
    def root(self,seed):
        x=np.array(seed)
        for iteration in range(100):
            r=self.dc(x);d=np.linalg.solve(self.fd(x),-r);err=max(abs(r));corr=max(abs(d))
            if err<=1e-12 and corr<=2e-9:return x.tolist(),dict(iterations=iteration+1,kcl_a=err,correction_v=corr)
            for power in range(28):
                trial=x+2.**-power*d
                try:
                    rr=self.dc(trial)
                    # Under the KCL gate, continue improving weak-node voltages.
                    # A global residual floor in another row must not halt Newton.
                    next_error=max(abs(rr))
                    if next_error<err or (err<=1e-12 and next_error<=1e-12 and max(abs(np.linalg.solve(self.fd(trial),-rr)))<corr):x=trial;break
                except (ValueError,OverflowError):pass
            else:raise ValueError(f'original joint DC line search {err=} {corr=}')
        raise ValueError('original joint DC budget')
def mass(h):
    m=np.zeros((N,N))
    from c5_trigger_reference import CAPS as DUAL
    for a,b,c in [(a,b if b<54 else None,c) for a,b,c in DUAL]+[(ci(a),ci(b) if isinstance(b,int) else ci(66) if b=='BUS' else None,c) for a,b,c in CAPS if a!=62]+[(ci(67),ci(7),1e-5)]:
        for row,sign in [(a,1),(b,-1)]:
            if row is not None:
                m[row,a]+=sign*c/h
                if b is not None:m[row,b]-=sign*c/h
    return m
def charge(old,now,h):
    # Float tuples identify high/low; independent Decimal65 junction increments.
    dual=charge_increment([*old[:54],*old[N:N+54]],[*now[:54],*now[N:N+54]],False)
    q=np.array([float(v)/h for v in dual]+[0.]*64)
    from decimal import Decimal as D,localcontext
    with localcontext() as ctx:
        ctx.prec=65
        delta=[D.from_float(now[k])+D.from_float(now[N+k])-D.from_float(old[k])-D.from_float(old[N+k]) for k in range(N)]
        for a,b,c in CAPS+[(67,7,1e-5)]:
            if a==62:continue
            a=ci(a);b=ci(b) if isinstance(b,int) else ci(66) if b=='BUS' else None
            v=float(D.from_float(c)/D.from_float(h)*(delta[a]-(delta[b] if b is not None else 0)))
            q[a]+=v
            if b is not None:q[b]-=v
    return q
