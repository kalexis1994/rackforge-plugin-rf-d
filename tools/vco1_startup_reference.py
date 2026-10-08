"""Independent Decimal100 solution from the production analytic seeds, not SPICE."""
import json,re,time
from decimal import localcontext
import vco1_newton_reference as ref
ROOT=ref.ROOT;sha=ref.sha
SOURCES=ref.SOURCES+['tools/vco1_startup_reference.py','crates/rf-d-circuit/src/vco1_startup.rs','docs/VCO1_ARRANQUE_PROTOCOLO.md','evidence/voice_vco1_startup_native01.json']
def main():
 out=ROOT/'evidence/voice_vco1_startup_reference01.json';work=ROOT/'references-local/vco1-startup-reference01'
 if out.exists() or work.exists():raise ValueError('preserve independent startup')
 before={n:sha(ROOT/n) for n in SOURCES};a=json.loads((ROOT/SOURCES[-1]).read_text(encoding='utf8'));stdout='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 roots={};seeds={}
 for m in re.finditer(r'STARTUP_(ROOT|SEED),([01]),([0-4]),([^\r\n]+)',stdout):
  values=list(map(float,m[4].split(',')));(roots if m[1]=='ROOT' else seeds)[(int(m[2]),int(m[3]))]=values
 if len(roots)!=10 or len(seeds)!=10:raise ValueError('ten captured scenes')
 r=dict(schema='rf-d/vco1-own-startup-independent/v1',passed=False,source_sha256=before,cases=[],unchanged_replays=[],gates=ref.GATES,new_spice_processes=0,new_audio=False,decimal_precision=100,device_interface='binary64 branch law, Decimal100 incidence/pivots',production_seeds_used=True,production_roots_used_as_initial=False)
 def save():out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
 save();work.mkdir();start=time.perf_counter()
 with localcontext() as ctx:
  ctx.prec=100
  for key in sorted(roots):
   pf,scene=key;c=[.5,500.,[1e-11,100e-12][pf],0.,0.,*([-2.1]*6)]
   if scene:c[0]=.26134047;c[1]=521.31266;c[7]=[-3.1,-2.1,-1.1,-.1][scene-1]
   initial=seeds[key];target=roots[key];case=dict(profile=pf,scene=scene,controls=c,initial=initial,native_root=target[1:],native_forcing_a=target[0]);r['cases'].append(case);save()
   try:
    root,f,it=ref.solve(initial,initial,0.,c,True);rr,j,ground=ref.stamp.reference(root,root,0.,c);rr[43]+=f;ground-=f
    node=max(abs(u-v) for u,v in zip(root[:98],target[1:99]));branch=max(abs(u-v) for u,v in zip(root[98:],target[99:]));forcing=abs(f-target[0]);balance=abs(sum(rr[:98])+ground)
    case.update(root=root,forcing_a=f,iterations=it,max_node_error_v=node,max_branch_error_a=branch,forcing_error_a=forcing,max_kcl_a=max(map(abs,rr[:98])),max_constraint_v=max(map(abs,rr[98:])),ground_balance_a=balance)
    if node>2e-7 or branch>2e-10 or forcing>2e-10 or case['max_kcl_a']>2e-14 or case['max_constraint_v']>2e-12 or balance>1e-11:raise ValueError('independent startup comparison gates')
    case['passed']=True;save();print('independent own startup',key,'iterations',it,'node',node,flush=True)
   except Exception as e:
    case.update(passed=False,error=repr(e));save()
    try:ref.solve(initial,initial,0.,c,True)
    except Exception as e2:r['unchanged_replays'].append(dict(profile=pf,scene=scene,error=repr(e2),source_sha256={n:sha(ROOT/n) for n in before}))
    else:r['unchanged_replays'].append(dict(profile=pf,scene=scene,error='unexpected solve success; recheck numerical gates'))
    break
 r.update(passed=len(r['cases'])==10 and all(c['passed'] for c in r['cases']),wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before});r['passed']=r['passed'] and before==r['source_sha256_after'];save();print('independent own startup passed:',r['passed'],flush=True)
if __name__=='__main__':main()
