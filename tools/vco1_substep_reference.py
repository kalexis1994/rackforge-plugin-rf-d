"""Conditional short-step roots and full stamps, independent incidence/pivots."""
import argparse,json,time
from decimal import localcontext
import numpy as np
import vco1_newton_reference as ref
ROOT=ref.ROOT;sha=ref.sha
SOURCES=ref.SOURCES+['tools/vco1_substep_reference.py','crates/rf-d-circuit/src/vco1_substep.rs','docs/VCO1_SUBPASOS_PROTOCOLO.md']
PATH='references-local/vco1-native-cycles01/substep-probe01/trajectory.bin'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 if not 2<=a<=99:raise ValueError('preserve first failed attempt')
 out=ROOT/f'evidence/voice_vco1_substep_reference{a:02d}.json';work=ROOT/f'references-local/vco1-substep-reference{a:02d}'
 if out.exists() or work.exists():raise ValueError('preserve substep reference')
 before={n:sha(ROOT/n) for n in SOURCES};raw=np.memmap(ROOT/PATH,dtype='<f8',mode='r').reshape(-1,143);reset=int(np.argmin(raw[:,136]));ramp=int(np.searchsorted(raw[:,0],.020));indices=[ramp,reset];pattern=[tuple(map(int,l.split())) for l in (ROOT/'evidence/voice_vco1_stamp_pattern08.txt').read_text().splitlines()]
 r=dict(schema='rf-d/vco1-short-step-independent/v1',passed=False,stamp_bank_complete=False,all_roots_admitted=False,source_sha256=before,private_input_sha256={PATH:sha(ROOT/PATH)},gates=ref.GATES,conditional_history_from_diagnostic=True,native_current_roots_used_as_initial=False,decimal_precision=100,device_interface='binary64 primitive law, Decimal100 incidence/pivots',cases=[],unchanged_replays=[],new_spice_processes=0,new_audio=False)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save();work.mkdir();vectors=[];start=time.perf_counter()
 with localcontext() as ctx:
  ctx.prec=100
  for pf in (10,100):
   for scene,k in enumerate(indices):
    x=raw[k,1:135].tolist();old=raw[k-1,1:135].tolist();c=[.5,500.,pf*1e-12,0.,0.,*([-2.1]*6)]
    for power in range(1,13):
     dt=125e-9/(2**power);case=dict(c4_pf=pf,history_scene=scene,history_index=k,power=power,dt_s=dt,previous=old,stamp_state=x,controls=c);r['cases'].append(case);save()
     try:
      rr,j,g=ref.stamp.reference(x,old,dt,c)
      if any(j[a][b]!=0. for a in range(134) for b in range(134) if (a,b) not in pattern):raise ValueError('short-step sparse topology changed')
      root,f,it=ref.solve(old,old,dt,c,False);case.update(root=root,iterations=it,passed=True)
      vectors.append([*c,*x,*old,dt,*rr,g,*[j[a][b] for a,b in pattern],*root]);save()
     except Exception as e:
      case.update(passed=False,error=repr(e));save()
      try:ref.solve(old,old,dt,c,False)
      except Exception as e2:r['unchanged_replays'].append(dict(c4_pf=pf,scene=scene,power=power,error=repr(e2),source_sha256={n:sha(ROOT/n) for n in before}))
      else:r['unchanged_replays'].append(dict(c4_pf=pf,scene=scene,power=power,error='unexpected success'))
      vectors.append([*c,*x,*old,dt,*rr,g,*[j[a][b] for a,b in pattern],*([0.]*134)])
      save();continue
    print('short-step independent C4',pf,'scene',scene,'12 roots',flush=True)
 p=ROOT/f'evidence/voice_vco1_substep_vectors{a:02d}.txt'
 if p.exists():raise ValueError('preserve fixture')
 p.write_text(ref.stamp.op.table(vectors),encoding='utf8',newline='\n');r.update(passed=False,stamp_bank_complete=len(vectors)==48,all_roots_admitted=all(c['passed'] for c in r['cases']),rows=len(vectors),columns=len(vectors[0]),text_sha256=sha(p),pattern_sha256=sha(ROOT/'evidence/voice_vco1_stamp_pattern08.txt'),wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before});save();print('short-step reference passed',r['stamp_bank_complete'],'roots',sum(c['passed'] for c in r['cases']),flush=True)
if __name__=='__main__':main()
