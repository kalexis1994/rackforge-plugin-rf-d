"""VCO1 complete Decimal100 circuit, with unrounded junction/history interfaces."""
from decimal import Decimal,localcontext
import math
import lm741_port_reference as op
from vco1_native_inventory import inventory
from vco1_stamp_reference import scenario
from vco1_increment_devices import bjt_reference,jfet_reference,D
N=134;NV=98
def reference_decimal(x,previous,dt,c):
 inv=inventory(scenario(c));names=inv['names'];ix=lambda n:N if n=='0' else inv['nodes'].index(n)
 z=list(map(D,x));previous=list(map(D,previous));zero=Decimal(0);one=Decimal(1);r=[zero]*N;j=[[zero]*N for _ in range(N)];ground=zero
 def add(row,i):
  nonlocal ground
  if row==N:ground+=i
  else:r[row]+=i
 def derivative(row,col,g):
  if row!=N and col!=N:j[row][col]+=g
 def branch(a,b,i,grad):
  for row,sign in ((a,1),(b,-1)):
   add(row,sign*i)
   for col,g in grad:derivative(row,col,sign*g)
 def val(n):return zero if n==N else z[n]
 trims=['RR8_HIGH','RR8_LOW','RR11_ACTIVE'];vs=0
 for w in inv['lines']:
  k=w[0][0]
  if w[0] in ('VR8_HIGH','VR8_LOW','VR11_ACTIVE'):w=['R'+w[0][1:],*w[1:]];k='R'
  if k in 'RCVI':
   a,b=ix(w[1]),ix(w[2]);v=float(w[3])
   if k=='V' and w[0] in ('VBEND','VTUNE','VKEYBOARD','VMOD','VEXT','VOSC1_RANGE'):v=c[5+['VBEND','VTUNE','VKEYBOARD','VMOD','VEXT','VOSC1_RANGE'].index(w[0])]
   if k=='R' and w[0] not in trims:
    g=one/D(v);branch(a,b,(val(a)-val(b))*g,[(a,g),(b,-g)])
   elif k=='C' and dt:
    # Decimal terminal voltages and their differences remain unrounded.
    now=val(a)-val(b);old=(zero if a==N else previous[a])-(zero if b==N else previous[b]);g=D(v)/D(dt)
    branch(a,b,g*(D(now)-D(old)),[(a,g),(b,-g)])
   elif k=='V' or (k=='R' and w[0] in trims):
    row=NV+vs if k=='V' else 131+trims.index(w[0]);vs+=int(k=='V');branch(a,b,z[row],[(row,one)])
    resistance=zero if k=='V' else D(v);r[row]=val(a)-val(b)-(D(v) if k=='V' else zero)-resistance*z[row]
    derivative(row,a,one);derivative(row,b,-one);derivative(row,row,-resistance)
   elif k=='I':branch(a,b,D(v),[])
  elif k in 'QJ':
   m=[ix(n) for n in w[1:4]]+([N] if k=='Q' else [])
   node=[zero if n==N else z[n] for n in m];old=[zero if n==N else previous[n] for n in m]
   out=bjt_reference(1 if w[4]=='LAB_NPN' else -1,node,old,dt or 125e-9) if k=='Q' else jfet_reference(node,old,dt or 125e-9)
   size=len(m);cur=out[size:2*size] if dt else out[:size];start=3*size+(size*size if dt else 0);jac=out[start:start+size*size]
   for ri,row in enumerate(m):
    add(row,D(cur[ri]))
    for ci,col in enumerate(m):derivative(row,col,D(jac[ri*size+ci]))
 for m in inv['opamp_maps']:
  q=[zero if n==N else z[n] for n in m];old=[zero if n==N else previous[n] for n in m]
  h=[old[op.NODES.index(a)]-old[op.NODES.index(b)] for a,b in [(5,6),(98,9),(98,15)]]+old[35:37]
  rr,jj,_,gg=op.reference_decimal(q,dt,h)
  for ri,row in enumerate(m):
   add(row,rr[ri])
   for ci,col in enumerate(m):derivative(row,col,jj[ri][ci])
  ground+=gg
 return r,j,ground

def valid(x,c):
 if any(not v.is_finite() or abs(v)>D(40. if k<NV else 1.) for k,v in enumerate(x)):return False
 inv=inventory(scenario(c));at=lambda n:Decimal(0) if n=='0' else x[inv['nodes'].index(n)]
 for w in inv['lines']:
  if w[0][0] in 'QJ':
   sign=(-1 if w[4]=='LAB_PNP' else 1) if w[0][0]=='Q' else 1
   if any(not D(-40.)<=sign*(at(w[2])-at(n))<=D(.9) for n in (w[1],w[3])):return False
 for m in inv['opamp_maps']:
  q=[Decimal(0) if n==N else x[n] for n in m]
  for w in op.card():
   if w[1]=='Q':pairs=[(w[3],w[2]),(w[3],w[4])]
   elif w[1]=='D':pairs=[(w[2],w[3])]
   else:continue
   if any(not D(-40.)<=q[op.NODES.index(a)]-q[op.NODES.index(b)]<=D(.9) for a,b in pairs):return False
 return True

def solve(old,dt,c):
 x=list(map(D,old));old=list(map(D,old));dt=D(dt)
 for iteration in range(64):
  if not valid(x,c):raise ValueError('Decimal circuit domain')
  r,j,g=reference_decimal(x,old,dt,c);norm=max(abs(v)/D(2e-14 if k<NV else 2e-12) for k,v in enumerate(r))
  d=op.dense([row[:] for row in j],[-v for v in r]);corr=max(abs(v)/D(2e-10 if k<NV else 2e-13) for k,v in enumerate(d))
  if norm<=1 and corr<=1:return x,iteration+1,r,g
  for power in range(24):
   alpha=Decimal(2)**(-power);trial=[v+alpha*q for v,q in zip(x,d)]
   if not valid(trial,c):continue
   rr,jj,gg=reference_decimal(trial,old,dt,c);new=max(abs(v)/D(2e-14 if k<NV else 2e-12) for k,v in enumerate(rr))
   if new<norm or new<=1:x=trial;break
  else:raise ValueError('Decimal increment line search')
 raise ValueError('Decimal increment iterations')
