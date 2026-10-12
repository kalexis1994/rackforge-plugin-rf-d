"""Scoped reference functions, charge ledger, nominal prefix and same-clock states."""
import copy,json,struct,sys,time,traceback,types
from decimal import Decimal,localcontext
from functools import lru_cache,partial
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,trace,checkpoint,checkpoints,compare,TICK
from prepare_cutoff_temporal import MARKS
from analyze_joint_cycles import summary
from check_joint_reference import evaluate,D
from check_joint_cycles import check as selected_check
from check_joint_corrected_cycles import ledger
from chain_charge_reference import matrix
from circuit66_dc_vectors import dc_evaluator
from cutoff_j7_vectors import setup

@lru_cache(None)
def configured_problem(knob,r61,mask,sources):
 values=setup(r61);controls=copy.deepcopy(values[4]);controls['panel']['cutoff_fraction_from_neg10']=knob;core=dc_evaluator(values,controls);y=matrix(mask)
 def dc(x):
  r=np.zeros(68);r[:66]=core(x[:66].tolist())[0];r[:48]*=-1.;r[66]=(y@np.array([*sources,x[66]]))[5];i=(x[22]-x[67])/25500.;r[22]+=i;r[67]=-i;return r
 def gradient(x):
  j=np.empty((68,68))
  for k in range(68):
   a=x.copy();b=x.copy();a[k]+=1e-6;b[k]-=1e-6;j[:,k]=(dc(a)-dc(b))/(2e-6)
  return j
 return dc,gradient,y
def control_problem(knob,r61,mask,sources):return configured_problem(knob,r61,mask,tuple(sources))
def scoped_check(knob):
 # Reuse the admitted evaluator's code without changing any module globals.
 local=types.FunctionType(evaluate.__code__,dict(evaluate.__globals__,problem=partial(control_problem,knob)))
 return types.FunctionType(selected_check.__code__,dict(selected_check.__globals__,evaluate=local))

CONTROL=np.dtype([('ticks','<u8'),('c18_v','<f8'),('tail_a','<f8'),('charge_c','<f8'),('kcl_a','<f8')])
def check(native):
 require(native['passed'] and len(native['profiles'])==4,'four completed trajectories');old=json.loads((ROOT/'evidence/voice_cutoff_opening_tests01.json').read_text(encoding='utf8'));inputs=json.loads((ROOT/'evidence/voice_cutoff_temporal_inputs01.json').read_text(encoding='utf8'));private={};profiles=[];shared={};independent=[];nominal=[]
 for p in native['profiles']:
  knob=p['cutoff_fraction'];maximum=p['maximum_half_ticks'];directory=Path(p['command'][3]);points=checkpoints(directory/'checkpoints.bin');require([c['ticks'] for c in points]==[0,*MARKS] and all(c['maximum']==maximum for c in points),'complete checkpoint clocks/settings');require(points[0]['raw_sha256']==next(s['sha256'] for s in inputs['profiles'] if s['cutoff_fraction']==knob and s['maximum_half_ticks']==maximum),'incoming memory by bytes');rows=trace(directory/'trace.bin');last=checkpoint((directory/'final.ckp').read_bytes());require(last==points[-1] and int(rows[-1]['ticks'])==MARKS[-1],'complete final clock');info=summary(p['stderr']);require(info['intervals']*2==len(rows) and info['ticks']==MARKS[-1] and info['restore_replays']==2 and info['crossings']==0,'native ledger');require((directory/'events.txt').read_bytes()==b'RFJEVENT01\n','no crossings')
  raw=(directory/'control.bin').read_bytes();require(raw[:8]==b'RFJCTL01' and len(raw)==8+CONTROL.itemsize*len(rows),'full control trace codec');ctl=np.frombuffer(raw,dtype=CONTROL,offset=8);require(np.array_equal(ctl['ticks'],rows['ticks']) and b'RFJCTL01'+ctl.tobytes()==raw,'control clock/byte roundtrip');require(all(np.isfinite(ctl[n]).all() for n in ['c18_v','tail_a','charge_c','kcl_a']) and np.max(abs(ctl['kcl_a']))<=1e-12,'finite control/KCL')
  lift=lambda cp:[D(h)+D(l) for h,l in zip(cp['high'],cp['low'])];initial=lift(points[0]);ledgers=[]
  for cp in points[1:]:
   state=lift(cp);indices=np.flatnonzero(ctl['ticks']==cp['ticks']);require(len(indices)==1,'unique control clock');c=ctl[indices[0]];require(float(state[195])==float(c['c18_v']),'control agrees with full state');tail=(state[138]-state[198])/D(680);require(abs(tail-D(c['tail_a']))<=D(1e-11),'tail physical observation');delta=D(100e-12)*(state[195]-initial[195]);error=abs(delta+D(c['charge_c']));gate=D(1e-12)*D(cp['ticks'])*D(TICK);require(error<=gate,'C18 integrated charge');ledgers.append(dict(ticks=cp['ticks'],c18_v=str(state[195]),tail_a=str(tail),c18_charge_change_c=str(delta),c18_dc_integral_c=float(c['charge_c']),c18_balance_error_c=str(error),c18_balance_gate_c=str(gate),native_dc_stage_integrals_not_independent_quadrature=True))
  delta=lift(last)[43]-initial[43];balance=abs(D(info['charge'])+D(1e-8)*delta)/D(info['absolute']);require(balance<=D(.002),'C1 integrated balance');means=[s for s in p['stderr'].splitlines() if s.startswith('MEAN_LEDGER,')];require(len(means)==1,'full mean ledger');full=ledger(initial,lift(last),[D(float(v)) for v in means[0].split(',')[1:]],D(MARKS[-1])*D(TICK))
  reference=scoped_check(knob)([p]);require(len(reference['root_checks'])==18 and len(reference['current_checks'])==12 and len(reference['temporal_checks'])==6,'selected per-profile coverage');independent.append(dict(cutoff_fraction=knob,maximum_half_ticks=maximum,**reference));private.update(reference['input_sha256']);stats={n:dict(min=float(rows[n].min()),max=float(rows[n].max()),final=float(rows[n][-1]),peak_to_peak=float(np.ptp(rows[n]))) for n in ['ramp','saw','bus','cursor','j7']}
  profiles.append(dict(cutoff_fraction=knob,maximum_half_ticks=maximum,intervals=int(info['intervals']),endpoints=len(rows),final_ticks=MARKS[-1],restore_bit_replays=2,minimum_half_ticks=int(rows['half_ticks'].min()),maximum_lte=float(rows['lte'].max()),sampled_voltage_stats=stats,control_ledgers=ledgers,maximum_control_kcl_a=float(np.max(abs(ctl['kcl_a']))),c1_integrated_balance_relative=str(balance),full_radau_mean_ledger=full));shared[knob,maximum]=points
  for name in ['trace.bin','checkpoints.bin','final.ckp','selected.txt','control.bin','events.txt','stderr.txt','stdout.txt']:
   path=(directory/name).relative_to(ROOT).as_posix();private[path]=sha(ROOT/path)
  if knob==.5:
   path=f'references-local/candidate-cycles01/{maximum}/checkpoints.bin';require(sha(ROOT/path)==old['private_input_sha256'][path],'old nominal identity');previous=checkpoints(ROOT/path);a=next(c for c in previous if c['ticks']==MARKS[0]);require(struct.pack('<400d',*a['high'],*a['low'])==struct.pack('<400d',*points[1]['high'],*points[1]['low']),'nominal 2us prefix by bits');b=next(c for c in previous if c['ticks']==MARKS[-1]);contrast=compare([points[0],points[-1]],[previous[0],b]);nominal.append(dict(maximum_half_ticks=maximum,prefix_bit_coordinates=400,final_same_clock=contrast,final_state_bit_equal=struct.pack('<400d',*b['high'],*b['low'])==struct.pack('<400d',*last['high'],*last['low'])));private[path]=sha(ROOT/path)
 refinement=[dict(cutoff_fraction=k,points=compare(shared[k,65536],shared[k,32768])) for k in [.5,1.]];effects=[]
 for maximum in [65536,32768]:
  a,b=[next(p for p in profiles if p['cutoff_fraction']==k and p['maximum_half_ticks']==maximum) for k in [.5,1.]];x,y=a['control_ledgers'][-1],b['control_ledgers'][-1];cv=Decimal(y['c18_v'])-Decimal(x['c18_v']);tail=Decimal(y['tail_a'])/Decimal(x['tail_a'])-1;admitted=cv>=D(.001) and tail>=D(.01);effects.append(dict(maximum_half_ticks=maximum,c18_voltage_change_v=str(cv),tail_relative_increase=str(tail),j7_final_difference_v=b['sampled_voltage_stats']['j7']['final']-a['sampled_voltage_stats']['j7']['final'],j7_sampled_peak_to_peak_ratio=b['sampled_voltage_stats']['j7']['peak_to_peak']/a['sampled_voltage_stats']['j7']['peak_to_peak'],electrical_control_effect_admitted=admitted,sampled_window_is_not_a_cycle=True))
 return dict(profiles=profiles,new_independent=independent,nominal_controls=nominal,same_clock_refinement=refinement,effects=effects,input_sha256=private,own_temporal_controls_admitted=True,control_effect_admitted=all(e['electrical_control_effect_admitted'] for e in effects),independent_nonlinear_rows=28800,independent_candidates=72,current_observations=48,lte_observations=24,restore_bit_replays=8,nominal_prefix_bit_coordinates=800,new_roots=0,independent_all_step_propagation=False,steady_periodicity_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 name='evidence/voice_cutoff_temporal_native01.json';out=ROOT/'evidence/voice_cutoff_temporal_reference01.json';require(not out.exists(),'exclusive reference');native=json.loads((ROOT/name).read_text(encoding='utf8'));names={name,'evidence/voice_cutoff_temporal_inputs01.json','evidence/voice_cutoff_opening_tests01.json','docs/VOZ_CUTOFF_TEMPORAL_PROTOCOLO.md','tools/check_cutoff_temporal.py'}
 for module in list(sys.modules.values()):
  f=getattr(module,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/cutoff-temporal-reference/v1',passed=False,source_sha256=before);start=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(check(native))
  require(time.perf_counter()-start<=300,'reference budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_cutoff_temporal.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;check(native)
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==r['source_sha256_after'],'unchanged reference');r['wall_s']=time.perf_counter()-start;out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CUTOFF_TEMPORAL_REFERENCE',r['passed'],r.get('failure',''),r.get('control_effect_admitted'),flush=True)
if __name__=='__main__':main()
