"""Independent Decimal100 NJF nominal oracle by physical branch incidence."""
import hashlib,json,math,subprocess
from decimal import Decimal,localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='3af70f6d5132023642776b104a284be15992c787'
LIB='crates/rf-d-circuit/src/lib.rs';EXPORT=b'\npub mod vco_jfet;\n'
ATTRS=b'/crates/rf-d-circuit/src/vco_jfet.rs text eol=lf\n/crates/rf-d-circuit/tests/vco_jfet.rs text eol=lf\n/crates/rf-d-circuit/tests/vco_jfet_no_alloc.rs text eol=lf\n/evidence/voice_vco_jfet_vectors01.txt -text\n/evidence/voice_vco_jfet_neighbors01.txt -text\n/evidence/voice_vco_jfet_spice*.txt -text\n'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
VT=(1.38064852e-23/1.6021766208e-19)*298.15
JDIR='references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/devices/jfet/'
PRIVATE=tuple(JDIR+n for n in ('jfetload.c','jfettemp.c','jfetacld.c','jfetask.c','jfetset.c'))+('references-local/voice-circuit/newton-build11/ngspice-46/src/include/ngspice/const.h',)
D=Decimal.from_float
CARD={'LEVEL':1,'VTO':-2.5,'BETA':.0003018867924528302,'LAMBDA':.003,'CGS':3.3e-12,'CGD':5.4990908339470075e-12,'PB':1,'IS':1e-14,'B':1,'FC':.5,'RD':0,'RS':0,'TNOM':25}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inherited():
 q=json.loads((ROOT/'evidence/voice_vco_bjt_tests02.json').read_text(encoding='utf8'))
 if not q['passed'] or q['covered_test_count']!=201:raise ValueError('inherited admission')
 for n,h in q['source_sha256'].items():
  if n in (LIB,'.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
   if hashlib.sha256(old).hexdigest()!=h or (ROOT/n).read_bytes()!=old+(EXPORT if n==LIB else ATTRS):raise ValueError('exact additive exports/policies')
  elif sha(ROOT/n)!=h:raise ValueError('inherited input '+n)
 return q

def reference(node,previous,dt):
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
 return list(map(float,[*current,*transient,*terminal_q,*flat(jac),*flat(dynamic),*flat(cap),*delta,*qnorm,ch]))
def table(rows):return '\n'.join(' '.join(format(v,'.17e') for v in row) for row in rows)+'\n'
def fixtures():
 rows=[];neighbors=[];knee=-3*VT
 biases=[-20.,math.nextafter(-2.5,-math.inf),-2.5,math.nextafter(-2.5,math.inf),-.2,math.nextafter(knee,-math.inf),knee,math.nextafter(knee,math.inf),0.,math.nextafter(.5,-math.inf),.5,math.nextafter(.5,math.inf),.85]
 with localcontext() as ctx:
  ctx.prec=100
  for gate in (-.25,.25):
   for gs in biases:
    for gd in biases:
     node=[gate-gd,gate,gate-gs]
     for previous in (node,[gate+3,gate,gate+1],[gate+1,gate,gate+3]):
      for dt in (125e-9,500e-9):rows.append([*node,*previous,dt,*reference(node,previous,dt)])
  for v in (-20.,-3.,-2.5,-.2,knee,0.,1e-24,.49,.5,.85):
   for k in (0,1):
    previous=[1.,0.,1.];node=list(previous);terminal=2 if k==0 else 0
    previous[terminal]=-v;node[terminal]=-math.nextafter(v,math.inf)
    expected=reference(node,previous,125e-9)[36:38]
    neighbors.append([*node,*previous,125e-9,*expected])
 return rows,table(rows),neighbors

def main():
 out=ROOT/'evidence/voice_vco_jfet_vectors01.json';txt=out.with_suffix('.txt');nt=ROOT/'evidence/voice_vco_jfet_neighbors01.txt'
 if out.exists() or txt.exists() or nt.exists():raise ValueError('preserve oracle')
 q=inherited();card=json.loads((ROOT/'evidence/vco1_laboratory_devices.json').read_text(encoding='utf8'))
 if card['jfet']!=CARD or card['temperature_c']!=25:raise ValueError('exact nominal source card')
 names=set(q['source_sha256'])|{'evidence/voice_vco_bjt_tests02.json','docs/VCO_JFET_NOMINAL_PROTOCOLO.md','crates/rf-d-circuit/src/vco_jfet.rs','tools/vco_jfet_vectors.py'}
 before={n:sha(ROOT/n) for n in sorted(names)};private={n:sha(ROOT/n) for n in PRIVATE}
 rows,text,neighbors=fixtures();after={n:sha(ROOT/n) for n in before}
 if len(rows)!=2028 or any(len(r)!=48 for r in rows) or len(neighbors)!=20:raise ValueError('bank dimensions')
 if before!=after or private!={n:sha(ROOT/n) for n in private}:raise ValueError('oracle source changed')
 txt.write_text(text,encoding='utf8',newline='\n');nt.write_text(table(neighbors),encoding='utf8',newline='\n')
 # Keep each vector on one JSON line for review; no change of numeric representation.
 report=dict(schema='rf-d/vco-jfet-oracle/v1',passed=True,rows=2028,columns=48,decimal_precision=100,input_conversion='Decimal.from_float',native_seeds_used=False,thermal_voltage_v=VT,card=CARD,source_sha256=before,source_sha256_after=after,private_input_sha256=private,private_input_sha256_after={n:sha(ROOT/n) for n in private},text_sha256=sha(txt),neighbor_text_sha256=sha(nt))
 content=json.dumps(report,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(row) for row in rows)+'\n  ],\n  "neighbors": '+json.dumps(neighbors)+'\n}\n'
 out.write_text(content,encoding='utf8',newline='\n');json.loads(out.read_text(encoding='utf8'))
 print('JFET Decimal100: 2028 x 48, 20 neighbors',flush=True)
if __name__=='__main__':main()
