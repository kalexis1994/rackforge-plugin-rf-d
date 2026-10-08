"""Independent short coupled VCO1 roots; Decimal100 pivots, binary64 device interfaces."""
import argparse,json,math,time
from decimal import Decimal,localcontext
from pathlib import Path
import vco1_stamp_reference as stamp
from lm741_port_reference import dense
ROOT=stamp.ROOT;sha=stamp.sha;N=134;NV=98;RAMP=43
SOURCES=stamp.SOURCES+['tools/vco1_newton_reference.py','crates/rf-d-circuit/src/vco1_newton.rs','docs/VCO1_NEWTON_PROTOCOLO.md']
GATES=dict(node_v=2e-7,branch_a=2e-10,startup_a=2e-10,residual_a=1e-13,constraint_v=1e-11,correction_v=2e-9,correction_a=2e-12,independent_residual_a=2e-14,independent_constraint_v=2e-12,independent_correction_v=2e-10,independent_correction_a=2e-13)

def valid(x):
 if any(not math.isfinite(v) or abs(v)>(40. if k<NV else 1.) for k,v in enumerate(x)):return False
 inv=stamp.inventory();at=lambda n:0. if n=='0' else x[inv['nodes'].index(n)]
 for w in inv['lines']:
  if w[0][0]=='Q':
   sign=1 if w[4]=='LAB_NPN' else -1
   if any(not -40.<=sign*(at(w[2])-at(n))<=.9 for n in (w[1],w[3])):return False
  if w[0][0]=='J' and any(not -40.<=at(w[2])-at(n)<=.9 for n in (w[1],w[3])):return False
 return True

def system(x,old,dt,c,startup):
 if not valid(x):raise ValueError('independent device domain')
 r,j,g=stamp.reference(x,old,dt,c);forcing=-r[RAMP] if startup else 0.
 if startup:r[RAMP]=x[RAMP];j[RAMP]=[0.]*N;j[RAMP][RAMP]=1.
 return r,j,forcing

def solve(initial,old,dt,c,startup):
 x=list(initial)
 for iteration in range(64):
  r,j,f=system(x,old,dt,c,startup);norm=max(abs(v)/(2e-14 if k<NV and not(startup and k==RAMP) else 2e-12) for k,v in enumerate(r))
  d=list(map(float,dense([list(map(Decimal.from_float,row)) for row in j],[-Decimal.from_float(v) for v in r])))
  corr=max(abs(v)/(2e-10 if k<NV else 2e-13) for k,v in enumerate(d))
  if norm<=1. and corr<=1.:return x,f,iteration+1
  for power in range(24):
   alpha=2.**(-power);trial=[v+alpha*q for v,q in zip(x,d)]
   try:rr,jj,ff=system(trial,old,dt,c,startup)
   except ValueError:continue
   new=max(abs(v)/(2e-14 if k<NV and not(startup and k==RAMP) else 2e-12) for k,v in enumerate(rr))
   if new<norm or new<=1.:x=trial;break
  else:raise ValueError('independent line search')
 raise ValueError('independent iteration limit')

def fixtures(seedrows,progress=lambda x:None):
 dc=[];trajectory=[];iteration_max=0
 with localcontext() as ctx:
  ctx.prec=100
  for row in seedrows:
   c=row[:11];base=row[11:11+N];initial=[v+((k%3)-1)*(1e-5 if k<NV else 1e-9) for k,v in enumerate(base)]
   x,forcing,it=solve(initial,base,0.,c,True);dc.append([*c,*initial,*x,forcing]);iteration_max=max(iteration_max,it)
   if any(abs(a-b)>(2e-7 if k<NV else 2e-10) for k,(a,b) in enumerate(zip(x,base))) or abs(forcing-row[-1])>2e-10:raise ValueError('startup SPICE comparison')
   for dt in (125e-9,250e-9,500e-9):
    previous=list(x);steps=round(8e-6/dt)
    for index in range(1,steps+1):
     current,_,it=solve(previous,previous,dt,c,False);iteration_max=max(iteration_max,it);trajectory.append([*c,dt,float(index),*current]);previous=current
    progress('VCO1 coupled reference: C4='+str(c[2])+',dt='+str(dt)+',steps='+str(steps))
 return dc,trajectory,iteration_max

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 if not 1<=a<=99:raise ValueError('attempt')
 out=ROOT/f'evidence/voice_vco1_newton_reference{a:02d}.json';work=ROOT/f'references-local/vco1-newton-reference{a:02d}'
 if out.exists() or work.exists():raise ValueError('preserve independent attempt')
 seedp=ROOT/'evidence/voice_vco1_stamp_startup08.txt';before={n:sha(ROOT/n) for n in SOURCES+[seedp.relative_to(ROOT).as_posix()]}
 private={n:sha(ROOT/n) for n in [stamp.op.MODEL]+[f'references-local/vco1-stamp-reference08/case{k:02d}/dc.txt' for k in (0,1)]}
 report=dict(schema='rf-d/vco1-coupled-short-oracle/v1',passed=False,gates=GATES,source_sha256=before,private_input_sha256=private,outputs=[],new_spice_processes=0,new_audio=False,unchanged_replays=[],startup_seeds_imported_from_original_spice=True,native_own_startup_seed_admitted=False,native_full_period_admitted=False)
 def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 write();work.mkdir();seedrows=[list(map(float,l.split())) for l in seedp.read_text().splitlines()];start=time.perf_counter()
 try:
  dc,tr,it=fixtures(seedrows,lambda s:print(s,flush=True));dcp=ROOT/f'evidence/voice_vco1_newton_startup{a:02d}.txt';trp=ROOT/f'evidence/voice_vco1_newton_trajectory{a:02d}.txt'
  if dcp.exists() or trp.exists():raise ValueError('preserve fixtures')
  dcp.write_text(stamp.op.table(dc),encoding='utf8',newline='\n');trp.write_text(stamp.op.table(tr),encoding='utf8',newline='\n')
  report.update(passed=True,startup_rows=2,trajectory_rows=len(tr),profiles=6,duration_s=8e-6,max_independent_iterations=it,decimal_precision=100,device_interface='binary64 branches / Decimal100 incidence',startup_text_sha256=sha(dcp),trajectory_text_sha256=sha(trp),native_solutions_used=False)
 except Exception as exc:
  report.update(error=repr(exc),failed_source_text={n:(ROOT/n).read_text(encoding='utf8') for n in SOURCES if n.endswith(('.py','.rs','.md'))});write()
  try:fixtures(seedrows)
  except Exception as retry:report['unchanged_replays'].append(dict(stage='fixtures(seedrows)',error=repr(retry),source_sha256={n:sha(ROOT/n) for n in before}))
  else:report['unchanged_replays'].append(dict(stage='fixtures(seedrows)',error='unexpected success',source_sha256={n:sha(ROOT/n) for n in before}))
 report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private});report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after'];write();print('VCO1 coupled independent:',report['passed'],report.get('error',''),flush=True)
if __name__=='__main__':main()
