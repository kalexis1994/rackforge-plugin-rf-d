"""Preserve all Decimal100 incremental roots, complete matrices and retries."""
import argparse,json,math,time
from decimal import Decimal,localcontext
import vco1_increment_circuit as oracle
from vco1_newton_reference import ROOT,sha,GATES
from lm741_reference import table
from vco1_stamp_reference import SOURCES as OLD
SOURCES=OLD+['tools/lm741_port_reference.py','tools/vco1_increment_devices.py','tools/vco1_increment_circuit.py','tools/vco1_increment_reference.py','crates/rf-d-circuit/src/vco1_increment.rs','docs/VCO1_INCREMENTOS_PROTOCOLO.md','evidence/voice_vco1_substep_reference02.json','evidence/voice_vco1_adaptive_failure_history01.txt']
def pairs(values):
 hi=list(map(float,values));lo=[float(v-Decimal.from_float(h)) for v,h in zip(values,hi)];return hi,lo

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 if not 1<=a<=99:raise ValueError('attempt')
 out=ROOT/f'evidence/voice_vco1_increment_reference{a:02d}.json';work=ROOT/f'references-local/vco1-increment-reference{a:02d}'
 if out.exists() or work.exists():raise ValueError('preserve incremental oracle')
 before={n:sha(ROOT/n) for n in SOURCES};private={oracle.op.MODEL:sha(ROOT/oracle.op.MODEL)};work.mkdir()
 r=dict(schema='rf-d/vco1-increment-decimal100/v1',passed=False,gates=GATES,source_sha256=before,private_input_sha256=private,precision=100,interfaces='Decimal100 terminal/junction/history/incidence/pivots; constants Decimal.from_float',native_current_roots_used=False,conditional_history=True,cases=[],unchanged_replays=[],new_spice_processes=0,new_audio=False)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save();start=time.perf_counter();previous=json.loads((ROOT/'evidence/voice_vco1_substep_reference02.json').read_text(encoding='utf8'));pattern=[tuple(map(int,l.split())) for l in (ROOT/'evidence/voice_vco1_stamp_pattern08.txt').read_text().splitlines()];vectors=[];sums=[]
 with localcontext() as ctx:
  ctx.prec=100
  scenes=[]
  for old in previous['cases']:
   hi=old['previous'];lo=[math.ulp(v)*.25*((k%3)-1) if old['power']%2 else 0. for k,v in enumerate(hi)];delta=[u-v for u,v in zip(old['stamp_state'],hi)]
   scenes.append(dict(controls=old['controls'],previous_high=hi,previous_low=lo,delta=delta,dt_s=old['dt_s'],kind='conditional-'+str(old['history_scene']),power=old['power']))
  hi=list(map(float,(ROOT/'evidence/voice_vco1_adaptive_failure_history01.txt').read_text().split()))
  for dt in (2*125e-9/4096,125e-9/4096):scenes.append(dict(controls=[.5,500.,1e-11,0.,0.,*([-2.1]*6)],previous_high=hi,previous_low=[0.]*134,delta=[0.]*134,dt_s=dt,kind='preserved-floor-reject'))
  for index,case in enumerate(scenes):
   r['cases'].append(case);save();c=case['controls'];old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(case['previous_high'],case['previous_low'])];x=[v+Decimal.from_float(d) for v,d in zip(old,case['delta'])];dt=case['dt_s']
   try:
    rr,j,g=oracle.reference_decimal(x,old,dt,c)
    if any(j[u][v]!=0 for u in range(134) for v in range(134) if (u,v) not in pattern):raise ValueError('sparse topology')
    root,it,res,ground=oracle.solve(old,dt,c);rh,rl=pairs(root);case.update(passed=True,root_high=rh,root_low=rl,iterations=it,max_kcl_a=float(max(map(abs,res[:98]))),max_constraint_v=float(max(map(abs,res[98:]))),ground_balance_a=float(abs(sum(res[:98])+ground)))
    if case['max_kcl_a']>2e-14 or case['max_constraint_v']>2e-12 or case['ground_balance_a']>1e-11:raise ValueError('independent root gates')
    vectors.append([*c,*case['previous_high'],*case['previous_low'],*case['delta'],dt,*map(float,rr),float(g),*[float(j[u][v]) for u,v in pattern],*rh,*rl]);save()
    if index%12==11 or index>=48:print('Decimal100 increment roots',index+1,'/50',flush=True)
   except Exception as exc:
    case.update(passed=False,error=repr(exc));r['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in SOURCES if n.endswith(('.rs','.py','.md'))};save()
    try:oracle.solve(old,dt,c)
    except Exception as retry:r['unchanged_replays'].append(dict(case=index,error=repr(retry),source_sha256={n:sha(ROOT/n) for n in before}))
    else:r['unchanged_replays'].append(dict(case=index,error='unexpected solve success; original stamp/gate failure retained'))
    r.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private});save();return
  for value in (-40.,-10.,-4.,-3.8724851763271135,-1.,-.1,0.,.1,1.,10.,40.):
   for power in (-60,-55,-53,-52,-25):
    for sign in (-1,1):
     b=sign*2.**power;h,l=pairs([Decimal.from_float(value)+Decimal.from_float(b)]);sums.append([value,b,h[0],l[0]])
  vp=ROOT/f'evidence/voice_vco1_increment_vectors{a:02d}.txt';sp=ROOT/f'evidence/voice_vco1_increment_sum{a:02d}.txt'
  if vp.exists() or sp.exists():raise ValueError('preserve fixtures')
  vp.write_text(table(vectors),encoding='utf8',newline='\n');sp.write_text(table(sums),encoding='utf8',newline='\n')
 r.update(passed=True,rows=len(vectors),columns=len(vectors[0]),sum_rows=len(sums),text_sha256=sha(vp),sum_sha256=sha(sp),pattern_sha256=sha(ROOT/'evidence/voice_vco1_stamp_pattern08.txt'),wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private});save();print('Increment oracle',r['passed'],flush=True)
if __name__=='__main__':main()
