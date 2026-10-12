"""205-node independent equations: Decimal VCO, Python follower/chain and FD Jacobian."""
import copy,inspect,json,sys,time,traceback
from decimal import Decimal,localcontext
from functools import lru_cache
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require,checkpoint
import check_joint_reference as previous
from chain_charge_reference import matrix
from circuit66_dc_vectors import dc_evaluator
from circuit66_vca_dc_vectors import boundary_values
from cutoff_j7_vectors import setup
from loudness_follower_vectors import evaluate as follower_evaluate
from loudness_contour_reference import Semiconductors
D=previous.D
def ci(k):return previous.ci(k) if k<68 else k+132
@lru_cache(None)
def problem(c2,reset,r61,mask,sources):
 values=boundary_values(setup(r61),0.,2.);controls=copy.deepcopy(values[4]);controls['panel']['cutoff_fraction_from_neg10']=1.;core=dc_evaluator(values,controls);y=matrix(mask)
 b=dict(c2_v=c2,reset_base_v=reset,supply_v=9.3,load_conductance_s=1/68000)
 def dc(x):
  r=np.zeros(73);r[:66]=core(x[:66].tolist())[0];r[:48]*=-1.;r[66]=(y@np.array([*sources,x[66]]))[5];i=(x[22]-x[67])/25500.;r[22]+=i;r[67]=-i
  r[32]-=x[71]/68000.;r[68:]=follower_evaluate(x[68:],dict(b,load_reference_v=x[32]),Semiconductors())[0];return r
 def gradient(x):
  j=np.empty((73,73))
  for k in range(73):
   a=x.copy();b=x.copy();a[k]+=1e-6;b[k]-=1e-6;j[:,k]=(dc(a)-dc(b))/2e-6
  return j
 return dc,gradient,y
def scoped(c2,reset):
 # Retain the admitted auditor's entire physical/mass body, extending only
 # the algebraic chain dimension and replacing its explicitly scoped problem.
 s=inspect.getsource(previous.evaluate).replace('range(68)','range(73)').replace('Decimal(0)]*68','Decimal(0)]*73').replace('zeros((68,68))','zeros((73,73))')
 g=dict(previous.__dict__,N=205,ci=ci,problem=lambda r,m,s:problem(c2,reset,r,m,tuple(s)))
 exec(compile(s,'<declared 205-node auditor>','exec'),g);return g['evaluate']
def state(line):
 v=list(map(float,line.split(',')[1:]));require(len(v)==410,'205 high/low codec');return [D(v[k])+D(v[205+k]) for k in range(205)],v
def audit():
 native=json.loads((ROOT/'evidence/voice_loudness_native02.json').read_text(encoding='utf8'));require(native['passed'],'native completed');inp=json.loads((ROOT/'evidence/voice_loudness_inputs02.json').read_text(encoding='utf8'));seed=checkpoint((ROOT/inp['seed_path']).read_bytes());seedbytes=np.array([*seed['high'],*seed['low']],dtype='<f8').tobytes()
 lines=(ROOT/'references-local/joint-loudness02/selected.txt').read_text(encoding='utf8').splitlines();profiles=[];roots=[];ports=[];i=0
 while i<len(lines):
  _,c2,reset,h,count=lines[i].split(',');c2,reset,h=float(c2),float(reset),float(h);count=int(count);initial,v=state(lines[i+1]);require(np.array([*v[:200],*v[205:405]],dtype='<f8').tobytes()==seedbytes,'incoming 400 coordinates by bits');i+=2;checks=[];obs=[]
  while lines[i]!='FINAL':
   if lines[i].startswith('JOINT_ROOT,'):
    _,mask,dt,res,corr=lines[i].split(',');states=[state(s)[0] for s in lines[i+1:i+6]];checks.append(scoped(c2,reset)((int(mask),float(dt),*states)))
    for x in states[-2:]:
     nvt=1.5*1.380649e-23*298.15/1.602176634e-19
     timing=(D(c2)-x[200])/D(10000);diode=-D(1e-8)*(((x[204]-D(reset))/D(nvt)).exp()-1);r59=(x[203]-x[165])/D(68000)
     high=np.array([float(x[ci(k)]) for k in range(73)]);_,current=follower_evaluate(high[68:],dict(c2_v=c2,reset_base_v=reset,supply_v=9.3,load_conductance_s=1/68000,load_reference_v=high[32]),Semiconductors())
     error=max(abs(float(timing)-current[0]),abs(float(diode)-current[1]),abs(float(r59)+current[2]));require(error<=1e-9,'exposed port signs/currents');ports.append(dict(c2_v=c2,reset_v=reset,h_s=h,timing_a=str(timing),reset_a=str(diode),r59_a=str(r59),reference_error_a=error))
    i+=6
   else:
    require(lines[i].startswith('OBS,'),'observation record');obs.append(list(map(float,lines[i].split(',')[1:])));i+=1
  final,raw=state(lines[i+1]);require(len(checks)==2 and len(obs)==count and [o[0] for o in obs]==list(range(count)),'full history coverage');i+=2
  require(max(abs(float(final[k]) - obs[-1][col]) for k,col in [(203,1),(194,2)])==0,'final observation agrees')
  profiles.append(dict(c2_v=c2,reset_v=reset,h_s=h,steps=count,initial_high_low=v,final_high_low=raw,final_loudness_v=float(final[203]),final_j7_v=float(final[194]),final_timing_a=obs[-1][3],final_reset_a=obs[-1][4],final_r59_a=obs[-1][5],maximum_native_residual_ratio=max(o[6] for o in obs)));roots.extend(checks)
 refinement=[]
 for a,b in zip(profiles[::2],profiles[1::2]):
  x,_=state('JOINT_STATE,'+','.join(map(str,a['final_high_low'])));y,_=state('JOINT_STATE,'+','.join(map(str,b['final_high_low'])));ratio=max(float(abs(u-v)/D(2e-9 if 98<=k<133 else 2e-6)) for k,(u,v) in enumerate(zip(x,y)));require(ratio<=1,'fixed-step refinement');refinement.append(dict(c2_v=a['c2_v'],reset_v=a['reset_v'],gate_ratio=ratio))
 require(len(profiles)==12 and len(roots)==24 and len(ports)==48,'coverage');return dict(profiles=profiles,root_checks=roots,port_checks=ports,same_clock_refinement=refinement,independent_candidates=48,independent_nonlinear_rows=9840,first_step_bit_replays=12,new_steps=288,incoming_bit_coordinates=400,loaded_follower_admitted=True,full_contour_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 names={'tools/check_joint_loudness.py','evidence/voice_loudness_native02.json','evidence/voice_loudness_inputs02.json','docs/VOZ_SEGUIDOR_PROTOCOLO.md'}
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
  if f:
   p=__import__('pathlib').Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 sources={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=sources);start=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(audit())
  require(time.perf_counter()-start<=300,'oracle budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_joint_loudness.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};r['wall_s']=time.perf_counter()-start;require(sources==r['source_sha256_after'],'stable oracle');write('evidence/voice_loudness_reference01.json',r);print('LOUDNESS_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
