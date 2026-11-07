"""Semilinear charge DAE, exact linear FOH plus implicit nonlinear-current FOH."""
import math
import numpy as np
from recovery_port_input_model import build as base_build,law,cases

def build(case,h=1/384000):
    m=base_build(case,h);a=m['a'];c=m['c'];pivots=[]
    for k in range(68):
        if np.linalg.matrix_rank(a[:,pivots+[k]])>len(pivots):pivots.append(k)
    alg=[k for k in range(68) if k not in pivots];t=np.linalg.inv(np.vstack([a,np.eye(68)[alg]]));gt=t.T@m['g']@t;bt=t.T@m['b'];dt=t.T@m['d'];r=np.linalg.solve(gt[18:,18:],gt[18:,:18]);s=np.linalg.solve(gt[18:,18:],bt[18:]);sn=np.linalg.solve(gt[18:,18:],dt[18:]);xq=t[:,:18]-t[:,18:]@r;xu=t[:,18:]@s;xn=t[:,18:]@sn
    k=gt[:18,:18]-gt[:18,18:]@r;b=bt[:18]-gt[:18,18:]@s;dn=dt[:18]-gt[:18,18:]@sn;aa=-k/c[:,None];forcing=np.column_stack([b/c,-dn/c[:,None]])
    eig,v=np.linalg.eig(aa);inv=np.linalg.inv(v);z=eig*h;phi1=np.empty_like(z);phi2=np.empty_like(z);small=abs(z)<1e-3
    phi1[~small]=np.expm1(z[~small])/z[~small];phi2[~small]=(np.expm1(z[~small])-z[~small])/z[~small]**2
    phi1[small]=sum(z[small]**j/float(math.factorial(j+1)) for j in range(9));phi2[small]=sum(z[small]**j/float(math.factorial(j+2)) for j in range(9))
    f=(v*np.exp(z))@inv;w0=h*(v*(phi1-phi2))@inv@forcing;w1=h*(v*phi2)@inv@forcing;imag=float(max(np.max(abs(q.imag)) for q in [f,w0,w1]));assert imag<=1e-10;f=f.real;w0=w0.real;w1=w1.real;half=((v*np.exp(z/2))@inv).real;sg=float(np.max(abs(half@half-f)));assert sg<=1e-10
    err=float(max(np.max(abs(a@xq-np.eye(18))),np.max(abs(a@xu)),np.max(abs(a@xn))));assert err<=1e-11
    identities=[]
    for left,right,scale in [(aa@(w0+w1),(f-np.eye(18))@forcing,abs(aa)@(abs(w0)+abs(w1))+(abs(f)+np.eye(18))@abs(forcing)),(aa@w1,(w0+w1)/h-forcing,abs(aa)@abs(w1)+(abs(w0)+abs(w1))/h+abs(forcing))]:
        scaled=float(np.max(np.max(abs(left-right),axis=0)/np.maximum(1e-30,np.max(scale,axis=0))));assert scaled<=1e-10,scaled;identities.append(scaled)
    eigen_error=float(np.linalg.norm(aa@v-v*eig)/max(np.linalg.norm(aa)*np.linalg.norm(v),1e-30));assert eigen_error<=1e-10
    nd=xn-xq@w1[:,1:];m.update(f=f,u0=w0[:,0],u1=w1[:,0],n0=w0[:,1:],n1=w1[:,1:],xq=xq,xu=xu,xn=xn,xd=nd,zh=m['e']@xq,zu=m['e']@xu,p=m['e']@nd,projection_error=err,imaginary_error=imag,semigroup_error=sg,identity_scaled=max(identities),eigen_residual=eigen_error,ode_a=aa,ode_forcing=forcing,alg=t[:,18:].T)
    return m

def independent_maps(m):
    h=m['h'];a=m['ode_a'];b=m['ode_forcing'];scale=1/np.maximum(1.,np.max(abs(h*b),axis=0));z=np.zeros((44,44));z[:18,:18]=h*a;z[:18,18:31]=h*b*scale;z[18:31,31:]=np.eye(13)
    n=max(0,math.ceil(math.log2(np.linalg.norm(z,np.inf)/.125)));z/=2**n;term=np.eye(44);p=term.copy()
    for k in range(1,25):term=(term@z)/k;p+=term
    for _ in range(n):p=p@p
    f=p[:18,:18];w1=p[:18,31:]/scale;w0=p[:18,18:31]/scale-w1;checks=[]
    for got,ref in [(m['f'],f),(np.column_stack([m['u0'],m['n0']]),w0),(np.column_stack([m['u1'],m['n1']]),w1)]:
        error=float(max(np.max(abs(got-ref),axis=0)/np.maximum(1.,np.max(abs(ref),axis=0))));assert error<=1e-10,error;checks.append(error)
    return dict(squarings=n,taylor_degree=24,relative_column_errors=checks)

def step(m,q,old,new,seed):
    base=m['f']@q+m['u0']*old+m['u1']*new+m['n0']@seed;zp=m['zh']@base+m['zu']*new;z=zp-m['p']@seed
    for i in range(12):
        n,s=law(m,z);r=z-zp+m['p']@n
        if max(abs(r))<=2e-13:break
        z-=np.linalg.solve(np.eye(12)+m['p']*s,r)
    else:raise ValueError('exponential root budget')
    nextq=base+m['n1']@n;x=m['xq']@base+m['xu']*new-m['xd']@n
    return nextq,n,x,base,z,float(max(abs(r)))

def simulate(m,t,u):
    q=np.zeros(18);seed=np.zeros(12);out=np.empty((len(t),68));out[0]=m['dc'];qs=np.zeros((len(t),18));ns=np.zeros((len(t),12))
    for j in range(1,len(t)):
        q,seed,x,_,_,_=step(m,q,u[j-1],u[j],seed);out[j]=m['dc']+x;qs[j]=q;ns[j]=seed
    return out,qs,ns
