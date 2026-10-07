"""Full LM741 Decimal100 incidence oracle and fresh forced-port ngspice roots."""
import argparse,hashlib,json,math,subprocess,time
from decimal import Decimal,localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NODES=[1,2,99,50,28,3,4,5,6,7,8,9,10,98,49,15,16,17,23,24,26,22,25,27,21,20]
V_NAMES=['EOS','V2','V3','EH','E1','V6','V7','V5','V4'];L_NAMES=['L2','L3'];NV=26;N=37
VT=(1.38064852e-23/1.6021766208e-19)*298.15
MODEL='references-local/datasheets/ti_lm741_lm741.lib'
EXE='references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
BIAS=[[0,.001,12,-12,0],[.25,.251,12,-12,.25],[0,.001-1e-6,12,-12,2],[0,.001+1e-6,12,-12,-2],[0,-.01,12,-12,8],[0,.01,12,-12,-8]]
D=Decimal.from_float
GATES={'decimal_kcl_absolute':1e-14,'decimal_constraint_absolute':1e-11,'decimal_relative':3e-12,'decimal_jac_kcl_absolute':1e-12,'decimal_jac_constraint_absolute':1e-10,'dc_kcl_absolute':1e-11,'dc_constraint_absolute':1e-11,'dc_port_absolute':2e-14,'dc_port_relative':1e-7,'fd_kcl_absolute':2e-9,'fd_constraint_absolute':1e-6,'fd_relative':2e-6}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(rows):return ''.join(' '.join(format(v,'.17e') for v in row)+'\n' for row in rows)
def card():
 lines=(ROOT/MODEL).read_text(encoding='utf8').splitlines();result=[]
 suffix={'K':1e3,'M':1e-3,'U':1e-6,'N':1e-9,'P':1e-12,'MA':1e-3,'V':1.,'MEG':1e6}
 import re
 for line in lines:
  w=line.upper().split()
  if not w or w[0][0] in '*.' :continue
  kind=w[0][0]
  if kind not in 'RICLQDEGFV':raise ValueError('unhandled primary device')
  if kind in 'RICLV':
   m=re.fullmatch(r'([0-9.+E-]+)([A-Z]*)',w[3]);value=float(m[1])*suffix.get(m[2],1.)
   result.append((w[0],kind,int(w[1]),int(w[2]),value))
  elif kind in 'QD':result.append((w[0],kind,*map(int,w[1:-1])))
  elif kind in 'EG':
   if w[3]=='POLY(1)':result.append((w[0],kind,int(w[1]),int(w[2]),int(w[4]),int(w[5]),float(w[6]),float(w[7])))
   else:result.append((w[0],kind,*map(int,w[1:5]),0.,float(w[5])))
  elif kind=='F':result.append((w[0],kind,int(w[1]),int(w[2]),w[4],450e-6,float(w[6])))
 nodes=set()
 for w in result:
  for v in (w[2:5] if w[1]=='Q' else w[2:6] if w[1] in 'EG' else w[2:4]):nodes.add(v)
 if nodes!=set(NODES) or len(result)!=41:raise ValueError(('primary inventory',len(result),nodes-set(NODES)))
 return result

def reference(x,dt,history):
 # Decimal gradients assembled from physical incidence, primary card order.
 z=[D(v) for v in x];zero=Decimal(0);one=Decimal(1);r=[zero]*N;j=[[zero]*N for _ in range(N)];ground=zero;vt=D(VT)
 def branch(a,b,i,gradient):
  for row,sign in ((a,1),(b,-1)):
   r[row]+=sign*i
   for col,g in gradient.items():j[row][col]+=sign*g
 def junction(v,is_a):
  if v>=-3*vt:e=(v/vt).exp();return is_a*(e-one),is_a*e/vt
  q=(3*vt/(one.exp()*v))**3;return -is_a*(one+q),is_a*3*q/v
 for w in card():
  name,kind=w[:2];a=NODES.index(w[2]);b=NODES.index(w[3])
  if kind=='R':g=one/D(w[4]);branch(a,b,(z[a]-z[b])*g,{a:g,b:-g})
  elif kind=='I':branch(a,b,D(w[4]),{})
  elif kind=='Q':
   e=NODES.index(w[4]);vbe=z[b]-z[e];vbc=z[b]-z[a];ibe,gbe=junction(vbe,D(1e-16));ibc,gbc=junction(vbc,D(1e-16));gm=D(1e-12)
   branch(a,e,ibe-ibc,{b:gbe-gbc,e:-gbe,a:gbc});branch(b,e,ibe/D(625.)+gm*vbe,{b:gbe/D(625.)+gm,e:-gbe/D(625.)-gm});branch(b,a,ibc+gm*vbc,{b:gbc+gm,a:-gbc-gm});r[a]+=gm*z[a];j[a][a]+=gm;ground-=gm*z[a]
  elif kind=='D':v=z[a]-z[b];i,g=junction(v,D(1e-15));gm=D(1e-12);branch(a,b,i+gm*v,{a:g+gm,b:-g-gm})
  elif kind=='G':c=NODES.index(w[4]);d=NODES.index(w[5]);g=D(w[7]);branch(a,b,g*(z[c]-z[d]),{c:g,d:-g})
  elif kind in 'EV':
   k=NV+V_NAMES.index(name);branch(a,b,z[k],{k:one});r[k]+=z[a]-z[b];j[k][a]+=one;j[k][b]-=one
   if kind=='V':r[k]-=D(w[4])
   else:
    c=NODES.index(w[4]);d=NODES.index(w[5]);r[k]-=D(w[6])+D(w[7])*(z[c]-z[d]);j[k][c]-=D(w[7]);j[k][d]+=D(w[7])
  elif kind=='F':k=NV+V_NAMES.index(w[4]);branch(a,b,D(w[5])+D(w[6])*z[k],{k:D(w[6])})
  elif kind=='C' and dt:
   k=['C4','C3','C5'].index(name);g=D(w[4])/D(dt);branch(a,b,g*(z[a]-z[b]-D(history[k])),{a:g,b:-g})
  elif kind=='L':
   k=35+L_NAMES.index(name);branch(a,b,z[k],{k:one});r[k]=z[a]-z[b];j[k][a]=one;j[k][b]=-one
   if dt:coef=D(w[4])/D(dt);r[k]-=coef*(z[k]-D(history[3+k-35]));j[k][k]=-coef
 candidate=[z[NODES.index(a)]-z[NODES.index(b)] for a,b in [(5,6),(98,9),(98,15)]]+z[35:37]
 return list(map(float,[*r,*[g for row in j for g in row],*candidate,ground]))

def fixtures(roots):
 rows=[]
 with localcontext() as ctx:
  ctx.prec=100
  for root in roots:
   v=root[:N];mem=[v[NODES.index(a)]-v[NODES.index(b)] for a,b in [(5,6),(98,9),(98,15)]]+v[35:37]
   modes=[(0.,mem)]+[(dt,h) for dt in (125e-9,500e-9) for h in (mem,[m+(.01 if k<3 else 1e-8) for k,m in enumerate(mem)])]
   for variant in range(2):
    x=[q+(0. if variant==0 else ((k%3)-1)*(2e-5 if k<NV else 1e-9)) for k,q in enumerate(v)]
    for dt,h in modes:rows.append([*x,dt,*h,*reference(x,dt,h)])
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);number=ap.parse_args().attempt
 out=ROOT/f'evidence/voice_lm741_reference{number:02d}.json';work=ROOT/f'references-local/lm741-reference{number:02d}'
 if out.exists() or work.exists():raise ValueError('preserve attempts')
 q=json.loads((ROOT/'evidence/voice_vco_jfet_tests01.json').read_text(encoding='utf8'))
 if not q['passed'] or q['covered_test_count']!=205:raise ValueError('inherited QA')
 private={n:sha(ROOT/n) for n in [MODEL,EXE]+['references-local/voice-circuit/newton-build11/ngspice-46/src/'+n for n in ['spicelib/devices/bjt/bjtload.c','spicelib/devices/bjt/bjtsetup.c','spicelib/devices/bjt/bjttemp.c','spicelib/devices/dio/dioload.c','spicelib/devices/dio/diosetup.c','include/ngspice/const.h']]}
 if private[MODEL]!='f58370983c8bd22bf6a59ddd05a1dd492f1a0ea60f673ffd460a356da5e693dc' or private[EXE]!=q['official_executable_sha256']:raise ValueError('pinned originals')
 names=['tools/lm741_reference.py','crates/rf-d-circuit/src/lm741.rs','docs/VCO_741_NATIVO_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names}
 import shutil
 free=shutil.disk_usage(ROOT).free
 report=dict(passed=False,gates=GATES,source_sha256=before,private_input_sha256=private,commands=[],unchanged_replays=[],outputs=[],new_audio=False,resource_passed=free>=2*1024**3+8*1024**2,available_free_bytes=free,estimated_export_bytes=8*1024**2,margin_bytes=2*1024**3,estimates_are_not_bounds=True)
 def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 write()
 if not report['resource_passed']:return
 work.mkdir();roots=[];start=time.perf_counter()
 try:
  graph=card();report['primary_device_count']=len(graph);report['nodes']=NODES;report['unknown_count']=N
  for index,bias in enumerate(BIAS):
   folder=work/f'case{index:02d}';folder.mkdir();deck=folder/'probe.cir';data=folder/'root.txt'
   expressions=['v(p'+str(k)+')' for k in range(5)]+['v(xop.'+str(n)+')' for n in NODES[5:]]
   expressions+=[('real(-@q.xop.q2[ib])' if n=='EOS' else 'real(i('+('e' if n in ['EH','E1'] else 'v')+'.xop.'+n.lower()+'))') for n in V_NAMES]+['real(i(l.xop.'+n.lower()+'))' for n in L_NAMES]+['real(-i(vp'+str(k)+'))' for k in range(5)]
   text='LM741 forced five ports\n.include "'+(ROOT/MODEL).as_posix()+'"\n.options temp=25 tnom=25 gmin=1e-12 reltol=1e-10 abstol=1e-15 vntol=1e-12\n'
   text+=''.join('vp'+str(k)+' p'+str(k)+' 0 '+format(v,'.17g')+'\n' for k,v in enumerate(bias))+'xop p0 p1 p2 p3 p4 LM741\n.control\nop\nset wr_singlescale\nset wr_vecnames\nset numdgt=17\nwrdata '+data.as_posix()+' '+' '.join(expressions)+'\nquit\n.endc\n.end\n'
   deck.write_text(text,encoding='utf8',newline='\n');command=[str(ROOT/EXE),'-b',str(deck)]
   p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=60);(folder/'probe.log').write_text(p.stdout+p.stderr,encoding='utf8',newline='\n')
   entry=dict(command=command,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,deck_sha256=sha(deck));report['commands'].append(entry);write()
   try:
    if p.returncode or any(v in (p.stdout+p.stderr).lower() for v in ('error:','simulation(s) aborted','fatal')):raise ValueError('independent root rejected')
    values=list(map(float,data.read_text().splitlines()[1].split()))
    if len(values)!=N+6 or not all(math.isfinite(v) for v in values):raise ValueError(('root shape',len(values)))
    root=values[1:];roots.append(root)
    with localcontext() as ctx:
     ctx.prec=100;r=reference(root[:N],0.,[0.]*5)
    if max(abs(v) for v in r[5:NV])>1e-11 or max(abs(v) for v in r[NV:N])>1e-11:raise ValueError('independent residual gate')
    if any(abs(r[k]-root[N+k])>2e-14+1e-7*abs(root[N+k]) for k in range(5)):raise ValueError('independent port gate')
   except Exception:
    replay=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=60);report['unchanged_replays'].append(dict(command=command,exit_code=replay.returncode,stdout=replay.stdout,stderr=replay.stderr));raise
  rows=fixtures(roots);rp=ROOT/f'evidence/voice_lm741_roots{number:02d}.txt';vp=ROOT/f'evidence/voice_lm741_vectors{number:02d}.txt'
  for p,values in [(rp,roots),(vp,rows)]:
   if p.exists():raise ValueError('preserve fixture')
   p.write_text(table(values),encoding='utf8',newline='\n')
  report.update(passed=True,roots=roots,row_count=len(rows),column_count=len(rows[0]),decimal_precision=100,native_seeds_used=False,text_sha256=sha(vp),roots_text_sha256=sha(rp),new_spice_processes=len(roots))
 except Exception as exc:report['error']=repr(exc);report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names}
 report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in names},private_input_sha256_after={n:sha(ROOT/n) for n in private})
 report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in work.rglob('*') if p.is_file()];report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after'];write();print('741 independent:',report['passed'],report.get('error',''),flush=True)
if __name__=='__main__':main()
