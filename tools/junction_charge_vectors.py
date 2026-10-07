"""Independent Decimal100 depletion oracle. Preserve every production attempt."""
import hashlib,json,math,subprocess
from decimal import Decimal,localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='e2d263e19343d0e1d6c11d16a4f210e2ba734983'
LIB='crates/rf-d-circuit/src/lib.rs'
EXPORT=b'\npub mod junction_charge;\n'
ATTRS=b'/crates/rf-d-circuit/src/junction_charge.rs text eol=lf\n/crates/rf-d-circuit/tests/junction_charge.rs text eol=lf\n/crates/rf-d-circuit/tests/junction_charge_no_alloc.rs text eol=lf\n/evidence/voice_junction_charge_vectors01.txt -text\n'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inherited():
 q=json.loads((ROOT/'evidence/voice_mixer_direct_tests01.json').read_text(encoding='utf8'))
 if not q['passed'] or q['covered_test_count']!=193: raise ValueError('inherited admission')
 for n,h in q['source_sha256'].items():
  if n in (LIB,'.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
   if hashlib.sha256(old).hexdigest()!=h or (ROOT/n).read_bytes()!=old+(EXPORT if n==LIB else ATTRS): raise ValueError('exact additive export/policy '+n)
  elif sha(ROOT/n)!=h: raise ValueError('inherited bytes '+n)
 return q
CARDS=((7e-12,.75,.5,.4),(3e-12,.7,.33,.4),(3.3e-12,1.,.5,.5),(5.4990908339470075e-12,1.,.5,.5))
def fixtures():
 rows=[]
 with localcontext() as ctx:
  ctx.prec=100
  D=Decimal.from_float
  def charge(v,p):
   c,pb,m,fc=map(D,p);v=D(v);one=Decimal(1);vf=fc*pb;e=one-m
   def low(x): return c*pb/e*(one-((one-x/pb).ln()*e).exp())
   cf=c*((one-fc).ln()*(-m)).exp();slope=cf*m/(pb*(one-fc))
   if v<vf: return low(v),c*((one-v/pb).ln()*(-m)).exp()
   d=v-vf
   return low(vf)+cf*d+slope*d*d/2,cf+slope*d
  for card,p in enumerate(CARDS):
   vf=p[1]*p[3]
   voltages=[-40.,-20.,-1.,-1e-12,-1e-24,-0.,0.,1e-24,1e-12,vf-.01,math.nextafter(vf,-math.inf),vf,math.nextafter(vf,math.inf),vf+.01,.75,1.2,4.,10.,20.,40.]
   for v in voltages:
    previous=[-20.,0.,max(-40.,math.nextafter(v,-math.inf)),v,min(40.,math.nextafter(v,math.inf)),vf-.01,vf,vf+.01]
    for old in previous:
     for dt in (125e-9,500e-9):
      q0,_=charge(old,p);q,c=charge(v,p);delta=q-q0
      rows.append([card,*p,old,v,dt,float(q0),float(q),float(c),float(delta),float(delta/D(dt)),float(c/D(dt))])
 text='\n'.join(' '.join(format(x,'.17e') for x in row) for row in rows)+'\n'
 return rows,text

def main():
 out=ROOT/'evidence/voice_junction_charge_vectors01.json';txt=out.with_suffix('.txt')
 if out.exists() or txt.exists(): raise ValueError('preserve measured oracle')
 q=inherited()
 names=set(q['source_sha256'])|{'evidence/voice_mixer_direct_tests01.json','docs/VCO_CARGA_JUNTURA_PROTOCOLO.md','crates/rf-d-circuit/src/junction_charge.rs','tools/junction_charge_vectors.py'}
 before={n:sha(ROOT/n) for n in sorted(names)}
 rows,text=fixtures();after={n:sha(ROOT/n) for n in before}
 if before!=after or len(rows)!=1280: raise ValueError('oracle identity/count')
 txt.write_text(text,encoding='utf8',newline='\n')
 out.write_text(json.dumps(dict(schema='rf-d/junction-charge-oracle/v1',passed=True,rows=1280,columns=14,decimal_precision=100,input_conversion='Decimal.from_float',native_seeds_used=False,cases=rows,source_sha256=before,source_sha256_after=after,text_sha256=sha(txt)),indent=2)+'\n',encoding='utf8',newline='\n')
 print('Decimal100: 1280 rows x 14 columns')
if __name__=='__main__': main()
