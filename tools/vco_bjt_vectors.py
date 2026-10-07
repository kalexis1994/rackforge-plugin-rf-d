"""Independent Decimal100 four-terminal nominal BJT oracle, NG-46 subset."""
import hashlib,json,math,subprocess
from decimal import Decimal,localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='b1ec45a1c0b15bfa3c82b4390b59e3daf2b99d29'
LIB='crates/rf-d-circuit/src/lib.rs';EXPORT=b'\npub mod vco_bjt;\n'
ATTRS=b'/crates/rf-d-circuit/src/vco_bjt.rs text eol=lf\n/crates/rf-d-circuit/tests/vco_bjt.rs text eol=lf\n/crates/rf-d-circuit/tests/vco_bjt_no_alloc.rs text eol=lf\n/evidence/voice_vco_bjt_vectors01.txt -text\n/evidence/voice_vco_bjt_spice01.txt -text\n/evidence/voice_vco_bjt_neighbors01.txt -text\n'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
VT=(1.38064852e-23/1.6021766208e-19)*298.15
PRIVATE=('references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/devices/bjt/bjtload.c','references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/devices/bjt/bjttemp.c','references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/devices/bjt/bjtsetup.c','references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/parser/inp2q.c','references-local/voice-circuit/newton-build11/ngspice-46/src/include/ngspice/const.h','references-local/voice-circuit/newton-build11/ngspice-46/src/main.c')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inherited():
 q=json.loads((ROOT/'evidence/voice_junction_charge_tests01.json').read_text(encoding='utf8'))
 if not q['passed'] or q['covered_test_count']!=197:raise ValueError('inherited admission')
 for n,h in q['source_sha256'].items():
  if n in (LIB,'.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
   if hashlib.sha256(old).hexdigest()!=h or (ROOT/n).read_bytes()!=old+(EXPORT if n==LIB else ATTRS):raise ValueError('exact additive exports/policies')
  elif sha(ROOT/n)!=h:raise ValueError('inherited input '+n)
 return q
D=Decimal.from_float

def reference(polarity,node,previous,dt):
 # Round only the terminal-to-junction mapping as the declared binary64 interface.
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
 return list(map(float,[*currents,*transient,*charges,*flat(jac),*flat(dynamic),*flat(cap),*deltas,*qnorm]))

def fixtures():
 rows=[];neighbors=[];knee=-3*VT
 biases=[-20.,math.nextafter(knee,-math.inf),knee,math.nextafter(knee,math.inf),0.,.3,.7,.85]
 with localcontext() as ctx:
  ctx.prec=100
  for polarity in (1,-1):
   for base in (-.25,.25):
    for be in biases:
     for bc in biases:
      node=[base-polarity*bc,base,base-polarity*be,.125]
      for previous in (node,[base+polarity*2,base,base-polarity*.6,.125],[base-polarity*.6,base,base+polarity*2,.125]):
       for dt in (125e-9,500e-9):rows.append([polarity,*node,*previous,dt,*reference(polarity,node,previous,dt)])
   for value in (-20.,-.2,.01,.65,.85):
    for branch in (0,1):
     old=[1.,0.,1.,0.];node=list(old);terminal=2 if branch==0 else 0
     old[terminal]=-polarity*value;node[terminal]=-polarity*math.nextafter(value,math.inf)
     # Keep the other junction reverse biased for either polarity.
     other=0 if branch==0 else 2;old[other]=polarity;node[other]=polarity
     expected=reference(polarity,node,old,125e-9)[60:62]
     neighbors.append([polarity,*node,*old,125e-9,*expected])
 text='\n'.join(' '.join(format(v,'.17e') for v in row) for row in rows)+'\n'
 return rows,text,neighbors

def main():
 out=ROOT/'evidence/voice_vco_bjt_vectors01.json';txt=out.with_suffix('.txt')
 nt=ROOT/'evidence/voice_vco_bjt_neighbors01.txt'
 if out.exists() or txt.exists() or nt.exists():raise ValueError('preserve oracle')
 q=inherited();names=set(q['source_sha256'])|{'evidence/voice_junction_charge_tests01.json','docs/VCO_BJT_NOMINAL_PROTOCOLO.md','crates/rf-d-circuit/src/vco_bjt.rs','tools/vco_bjt_vectors.py'}
 before={n:sha(ROOT/n) for n in sorted(names)};private={n:sha(ROOT/n) for n in PRIVATE}
 rows,text,neighbors=fixtures()
 if len(rows)!=1536 or any(len(r)!=74 for r in rows) or len(neighbors)!=20:raise ValueError('bank dimensions')
 after={n:sha(ROOT/n) for n in before}
 if before!=after or private!={n:sha(ROOT/n) for n in private}:raise ValueError('source changed')
 txt.write_text(text,encoding='utf8',newline='\n')
 nt.write_text('\n'.join(' '.join(format(v,'.17e') for v in row) for row in neighbors)+'\n',encoding='utf8',newline='\n')
 out.write_text(json.dumps(dict(schema='rf-d/vco-bjt-oracle/v1',passed=True,rows=1536,columns=74,decimal_precision=100,input_conversion='Decimal.from_float',native_seeds_used=False,thermal_voltage_v=VT,cases=rows,neighbors=neighbors,source_sha256=before,source_sha256_after=after,private_input_sha256=private,text_sha256=sha(txt),neighbor_text_sha256=sha(nt)),indent=2)+'\n',encoding='utf8',newline='\n')
 print('BJT Decimal100: 1536 x 74, 20 neighbor cases',flush=True)
if __name__=='__main__':main()
