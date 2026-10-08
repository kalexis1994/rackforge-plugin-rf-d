"""Full Decimal100 device laws; Decimal junctions, charges and dynamic incidences.
Derived from the prior independent nominal oracles; no native algorithm/states.
"""
from decimal import Decimal
from vco_bjt_vectors import VT
from vco_jfet_vectors import CARD
D=lambda v:v if isinstance(v,Decimal) else Decimal.from_float(v)
def bjt_reference(polarity,node,previous,dt):
 # Terminal-to-junction mapping is Decimal100 in this oracle.
 u=[D(polarity*(node[1]-node[2])),D(polarity*(node[1]-node[0]))]
 old=[D(polarity*(previous[1]-previous[2])),D(polarity*(previous[1]-previous[0]))]
 vt=D(VT);is_a=D(1e-14);gm=D(1e-12);one=Decimal(1);zero=Decimal(0)
 def diode(v):
  if v>=-3*vt:return is_a*((v/vt).exp()-one),is_a*(v/vt).exp()/vt
  # Mathematical e; independent of native rational evaluation order.
  a=(3*vt/(one.exp()*v))**3
  return -is_a*(one+a),is_a*3*a/v
 def charge(v,k):
  c,pb,m,fc=map(D,((7e-12,.75,.5,.4),(3e-12,.7,.33,.4))[k]);e=one-m;vf=fc*pb
  def low(x):return c*pb/e*(one-((one-x/pb).ln()*e).exp())
  cf=c*((one-fc).ln()*(-m)).exp();s=cf*m/(pb*(one-fc))
  if v<vf:q=low(v);cap=c*((one-v/pb).ln()*(-m)).exp()
  else:x=v-vf;q=low(vf)+cf*x+s*x*x/2;cap=cf+s*x
  i,g=diode(v);tau=D((1e-9,3e-9)[k])
  return q+tau*i,cap+tau*g
 currents=[zero]*4;jac=[[zero]*4 for _ in range(4)];cap=[[zero]*4 for _ in range(4)];charges=[zero]*4
 incbe=[0,1,-1,0];incbc=[-1,1,0,0];inctr=[1,0,-1,0]
 f,gf=diode(u[0]);r,gr=diode(u[1])
 branches=[(inctr,Decimal(polarity)*(f-r),[gf*incbe[j]-gr*incbc[j] for j in range(4)]),
  (incbe,Decimal(polarity)*(f/D(100.)+gm*u[0]),[(gf/D(100.)+gm)*x for x in incbe]),
  (incbc,Decimal(polarity)*(r/D(5.)+gm*u[1]),[(gr/D(5.)+gm)*x for x in incbc])]
 substrate=[0]*4;target=0 if polarity==1 else 1;substrate[target]=1;substrate[3]=-1
 branches.append((substrate,gm*(D(node[target])-D(node[3])),[gm*x for x in substrate]))
 for incidence,current,gradient in branches:
  for i in range(4):
   currents[i]+=incidence[i]*current
   for j in range(4):jac[i][j]+=incidence[i]*gradient[j]
 qnorm=[];deltas=[];transient=list(currents)
 for k,incidence in enumerate((incbe,incbc)):
  q,c=charge(u[k],k);qo,_=charge(old[k],k);delta=q-qo;qnorm.append(q);deltas.append(delta)
  for i in range(4):
   charges[i]+=polarity*incidence[i]*q;transient[i]+=polarity*incidence[i]*delta/D(dt)
   for j in range(4):cap[i][j]+=incidence[i]*incidence[j]*c
 dynamic=[[jac[i][j]+cap[i][j]/D(dt) for j in range(4)] for i in range(4)]
 flat=lambda m:[v for row in m for v in row]
 return list([*currents,*transient,*charges,*flat(jac),*flat(dynamic),*flat(cap),*deltas,*qnorm])

def jfet_reference(node,previous,dt):
 u=[D(node[1]-node[2]),D(node[1]-node[0])];old=[D(previous[1]-previous[2]),D(previous[1]-previous[0])]
 vt=D(VT);one=Decimal(1);zero=Decimal(0);is_a=D(CARD['IS']);gm=D(1e-12)
 def gate(v):
  if v>=-3*vt:i=is_a*((v/vt).exp()-one);g=is_a*(v/vt).exp()/vt
  else:a=(3*vt/(one.exp()*v))**3;i=-is_a*(one+a);g=is_a*3*a/v
  return i+gm*v,g+gm
 def charge(v,k):
  c=D(CARD['CGS'] if k==0 else CARD['CGD']);pb=D(CARD['PB']);m=D(.5);fc=D(CARD['FC']);vf=fc*pb
  def low(x):return c*pb/(one-m)*(one-((one-x/pb).ln()*(one-m)).exp())
  cf=c*((one-fc).ln()*(-m)).exp();slope=cf*m/(pb*(one-fc))
  if v<vf:return low(v),c*((one-v/pb).ln()*(-m)).exp()
  x=v-vf;return low(vf)+cf*x+slope*x*x/2,cf+slope*x
 ds=u[0]-u[1];h=abs(ds);forward=ds>=0;sign=1 if forward else -1
 control=0 if forward else 1;over=u[control]-D(CARD['VTO']);beta=D(CARD['BETA']);lam=D(CARD['LAMBDA']);eff=beta*(one+lam*h)
 ch=zero;derivative=[zero,zero]
 if over>0:
  # Independent polynomial difference and incidence expansion.
  if h<=over:shape=over*over-(over-h)*(over-h);du=2*eff*h;dh=2*eff*(over-h)+beta*lam*shape
  else:shape=over*over;du=2*eff*over;dh=beta*lam*shape
  ch=sign*eff*shape
  derivative[control]+=sign*du
  derivative[0]+=dh;derivative[1]-=dh
 incgs=[0,1,-1];incgd=[-1,1,0];incch=[1,0,-1]
 current=[zero]*3;jac=[[zero]*3 for _ in range(3)];cap=[[zero]*3 for _ in range(3)];terminal_q=[zero]*3
 igs,ggs=gate(u[0]);igd,ggd=gate(u[1])
 branches=[(incch,ch,[derivative[0]*incgs[j]+derivative[1]*incgd[j] for j in range(3)]),(incgs,igs,[ggs*x for x in incgs]),(incgd,igd,[ggd*x for x in incgd])]
 for inc,i,gradient in branches:
  for k in range(3):
   current[k]+=inc[k]*i
   for j in range(3):jac[k][j]+=inc[k]*gradient[j]
 transient=list(current);qnorm=[];delta=[]
 for k,inc in enumerate((incgs,incgd)):
  q,c=charge(u[k],k);qp,_=charge(old[k],k);change=q-qp;qnorm.append(q);delta.append(change)
  for i in range(3):
   terminal_q[i]+=inc[i]*q;transient[i]+=inc[i]*change/D(dt)
   for j in range(3):cap[i][j]+=inc[i]*inc[j]*c
 dynamic=[[jac[i][j]+cap[i][j]/D(dt) for j in range(3)] for i in range(3)]
 flat=lambda m:[v for row in m for v in row]
 return list([*current,*transient,*terminal_q,*flat(jac),*flat(dynamic),*flat(cap),*delta,*qnorm,ch])
