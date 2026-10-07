"""Independent Decimal100 trajectories and complete Gear1 exports for LM741 port."""
import argparse,hashlib,json,math,subprocess,time,shutil
from decimal import Decimal,localcontext
from pathlib import Path
from lm741_reference import ROOT,NODES,V_NAMES,L_NAMES,VT,MODEL,EXE,sha,table,card as primary_card
D=lambda x:x if isinstance(x,Decimal) else Decimal.from_float(x)
NV=26;N=37
GRAPH=primary_card()
def card():return GRAPH
BASE='1564b7491af16c3ae1178491c5c978493234b77e'
GATES={'node_absolute_v':2e-7,'branch_absolute_a':2e-10,'port_absolute_a':2e-10,'gradient_absolute':2e-4,'gradient_relative':2e-4,'admittance_absolute_s':2e-7,'admittance_relative':2e-4,'residual_a':1e-13,'constraint_v':1e-11,'correction_v':2e-9,'correction_a':2e-12}
DTS=[125e-9,250e-9,500e-9];DURATION=16e-6
TIMES=[0.,4e-6,8e-6,12e-6,16e-6];LEVELS=[0.,1.,-1.,1.,0.]
def ports(scene,t):
 amp=[1e-5,.005,1.][scene]
 if t>=DURATION:level=0.
 else:
  i=next(k for k in range(4) if TIMES[k]<=t<TIMES[k+1]);level=LEVELS[i]+(LEVELS[i+1]-LEVELS[i])*(t-TIMES[i])/(TIMES[i+1]-TIMES[i])
 wave=amp*level
 return [wave,.001+wave,12.,-12.,0.] if scene==2 else [0.,.001+wave,12.,-12.,0.]
def memory(x):return [x[NODES.index(a)]-x[NODES.index(b)] for a,b in [(5,6),(98,9),(98,15)]]+x[35:37]
def dense(a,b):
 # Independent absolute pivots, internal constraints included; Decimal100.
 n=len(b)
 for k in range(n):
  pivot=max(range(k,n),key=lambda q:abs(a[q][k]));a[k],a[pivot]=a[pivot],a[k];b[k],b[pivot]=b[pivot],b[k]
  if not a[k][k]:raise ValueError('Decimal singular')
  for i in range(k+1,n):
   if not a[i][k]:continue
   f=a[i][k]/a[k][k];a[i][k]=Decimal(0)
   for q in range(k+1,n):a[i][q]-=f*a[k][q]
   b[i]-=f*b[k]
 x=[Decimal(0)]*n
 for i in range(n-1,-1,-1):x[i]=(b[i]-sum(a[i][k]*x[k] for k in range(i+1,n)))/a[i][i]
 return x

def decimal_solve(p,dt,h,initial):
 x=list(map(D,initial));inputs=list(map(D,p))
 # Initialize the linear common-mode state; all original rows remain in Newton.
 mid=(inputs[2]+inputs[3])/2;v3=(inputs[0]+inputs[1])/2
 il=-D(3.1623e-8)*(v3-mid);v17=mid-(D(.5305)/D(dt)*(il-D(h[3])) if dt else Decimal(0))
 v16=v17-D(1000.)*il;v7=inputs[0]+D(.001)+v16-mid
 x[6]+=((inputs[1]-x[1])+(v7-x[9]))/2
 x[5]=v3;x[9]=v7;x[13]=mid;x[14]=mid;x[16]=v16;x[17]=v17;x[35]=il;x[:5]=inputs
 for iteration in range(40):
  r,j,_,_=reference_decimal(x,dt,h)
  norm=max(abs(r[i])/(Decimal('1e-25') if i<NV else Decimal('1e-23')) for i in range(5,N))
  if norm<=1:return x,[r[i] for i in range(5)]
  d=dense([row[5:] for row in j[5:]],[-v for v in r[5:]])
  for power in range(30):
   scale=Decimal(2)**(-power);trial=x[:5]+[x[i]+scale*d[i-5] for i in range(5,N)]
   rr,_,_,_=reference_decimal(trial,dt,h);new=max(abs(rr[i])/(Decimal('1e-25') if i<NV else Decimal('1e-23')) for i in range(5,N))
   if new<norm:x=trial;break
  else:raise ValueError('Decimal line search exhausted')
 raise ValueError('Decimal iterations exhausted')
def reference_decimal(x,dt,history):
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
 return r,j,candidate,ground

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);number=ap.parse_args().attempt
 out=ROOT/f'evidence/voice_lm741_port_reference{number:02d}.json';work=ROOT/f'references-local/lm741-port-reference{number:02d}'
 if out.exists() or work.exists():raise ValueError('preserve attempted bank')
 q=json.loads((ROOT/'evidence/voice_lm741_tests01.json').read_text(encoding='utf8'))
 if not q['passed'] or q['covered_test_count']!=209:raise ValueError('inherited QA')
 names=['tools/lm741_port_reference.py','tools/lm741_reference.py','crates/rf-d-circuit/src/lm741.rs','crates/rf-d-circuit/src/lm741_port.rs','docs/VCO_741_PUERTO_PROTOCOLO.md']
 before={n:sha(ROOT/n) for n in names};private=dict(json.loads((ROOT/'evidence/voice_lm741_reference09.json').read_text(encoding='utf8'))['private_input_sha256'])
 control='references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/analysis/cktdojob.c';private[control]=sha(ROOT/control)
 if any(sha(ROOT/n)!=h for n,h in private.items()):raise ValueError('primary sources changed')
 free=shutil.disk_usage(ROOT).free
 report=dict(passed=False,source_sha256=before,private_input_sha256=private,commands=[],unchanged_replays=[],outputs=[],gates=GATES,resource_passed=free>=2*1024**3+64*1024**2,available_free_bytes=free,estimated_export_bytes=64*1024**2,margin_bytes=2*1024**3,estimates_are_not_bounds=True,new_audio=False,xtrtol=1000000000)
 def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 write()
 if not report['resource_passed']:return
 work.mkdir();start=time.perf_counter();local_rows=[];profiles=[]
 try:
  for scene in range(3):
   for dt in DTS:
    index=len(profiles);folder=work/f'case{index:02d}';folder.mkdir();deck=folder/'probe.cir';data=folder/'trajectory.txt';base=ports(scene,0.)
    lines=['LM741 independent Gear order1 full trajectory','.include "'+(ROOT/MODEL).as_posix()+'"','.options temp=25 tnom=25 gmin=1e-12 method=gear maxord=1 reltol=1e-10 abstol=1e-15 vntol=1e-12']
    for k in range(5):
     samples=' '.join(format(t,'.17g')+' '+format(ports(scene,t)[k],'.17g') for t in TIMES)
     lines.append(f'vp{k} p{k} 0 DC {base[k]:.17g} PWL({samples})')
    expressions=['v(p'+str(k)+')' for k in range(5)]+['v(xop.'+str(n)+')' for n in NODES[5:]]
    expressions+=[('real(-@q.xop.q2[ib])' if n=='EOS' else 'real(i('+('e' if n in ['EH','E1'] else 'v')+'.xop.'+n.lower()+'))') for n in V_NAMES]+['real(i(l.xop.'+n.lower()+'))' for n in L_NAMES]+['real(-i(vp'+str(k)+'))' for k in range(5)]
    lines+=['xop p0 p1 p2 p3 p4 LM741','.save all @q.xop.q2[ib]','.control','set xtrtol=1000000000','set wr_singlescale','set wr_vecnames','set numdgt=17',f'tran {dt:.17g} {DURATION:.17g} 0 {dt:.17g}','wrdata '+data.as_posix()+' '+' '.join(expressions),'quit','.endc','.end']
    deck.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n');command=[str(ROOT/EXE),'-b',str(deck)]
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=60);log=folder/'probe.log';log.write_text(p.stdout+p.stderr,encoding='utf8',newline='\n');entry=dict(command=command,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,deck_sha256=sha(deck));report['commands'].append(entry);write()
    try:
     if p.returncode or any(s in (p.stdout+p.stderr).lower() for s in ('error:','fatal','simulation(s) aborted','invalid argument')):raise ValueError('SPICE process/export rejected')
     rows=[list(map(float,l.split())) for l in data.read_text().splitlines()[1:]]
     if len(rows)<33 or any(len(r)!=43 or not all(math.isfinite(v) for v in r) for r in rows) or abs(rows[-1][0]-DURATION)>1e-15 or rows[0][0]!=0. or any(a[0]>=b[0] for a,b in zip(rows,rows[1:])):raise ValueError('complete trajectory coverage')
     eligible=0;excluded=0
     for previous,current in zip(rows,rows[1:]):
      interval=current[0]-previous[0]
      if 125e-9<=interval<=1e-3:local_rows.append([interval,*previous[1:38],*current[1:]]);eligible+=1
      else:excluded+=1
     if eligible<20:raise ValueError('insufficient in-domain independent intervals')
     profiles.append(dict(scene=scene,maxstep_s=dt,rows=len(rows),eligible_intervals=eligible,excluded_intervals=excluded,begin_s=rows[0][0],end_s=rows[-1][0]))
    except Exception:
     if data.exists():
      original=folder/'trajectory-failed-original.txt';shutil.copyfile(data,original)
      entry['failed_export_before_replay']=dict(path=original.relative_to(ROOT).as_posix(),sha256=sha(original),bytes=original.stat().st_size);write()
     replay=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=60);report['unchanged_replays'].append(dict(command=command,exit_code=replay.returncode,stdout=replay.stdout,stderr=replay.stderr));raise
    print('SPICE complete profile',index,'intervals',eligible,'excluded',excluded,flush=True)
  roots=[list(map(float,l.split())) for l in (ROOT/'evidence/voice_lm741_roots09.txt').read_text().splitlines()];trajectory=[]
  with localcontext() as ctx:
   ctx.prec=100
   x0,i0=decimal_solve(ports(0,0.),0.,[0.]*5,roots[0][:37])
   for scene in range(3):
    for dt in DTS:
     x=list(x0)
     for k in range(1,round(DURATION/dt)+1):
      t=k*dt;p=ports(scene,t);h=memory(x);x,i=decimal_solve(p,dt,h,x)
      trajectory.append([scene,dt,t,*p,*map(float,x),*map(float,i)])
     print('Decimal100 profile',scene,dt,'complete',flush=True)
  sp=ROOT/f'evidence/voice_lm741_port_spice{number:02d}.txt';tp=ROOT/f'evidence/voice_lm741_port_trajectory{number:02d}.txt'
  for p,rows in [(sp,local_rows),(tp,trajectory)]:
   if p.exists():raise ValueError('preserve vector bank')
   p.write_text(table(rows),encoding='utf8',newline='\n')
  report.update(passed=True,profiles=profiles,trajectory_rows=len(trajectory),trajectory_columns=50,local_spice_rows=len(local_rows),local_spice_columns=80,decimal_precision=100,native_seeds_used=False,text_sha256=sha(tp),spice_text_sha256=sha(sp),new_spice_processes=9)
 except Exception as exc:report['error']=repr(exc);report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names}
 report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in names},private_input_sha256_after={n:sha(ROOT/n) for n in private})
 report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.rglob('*') if p.is_file()];report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after'];write();print('741 port reference:',report['passed'],report.get('error',''),flush=True)
if __name__=='__main__':main()
