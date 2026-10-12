"""Audit adaptive candidates and observe three returns without assuming settling."""
import json,struct,sys,time,traceback
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,trace,checkpoint,checkpoints,compare,TICK,ANCHOR
from analyze_joint_cycles import summary
from check_joint_reference import D,decode
from check_joint_cycles import check as selected_check,bank
from check_joint_conditioned_cycles import cycle_changes
from check_joint_corrected_cycles import ledger

def event_bank(directory,rows):
 lines=(directory/'events.txt').read_text(encoding='utf8').splitlines();require(lines[0]=='RFJEVENT01' and len(lines)==13,'four complete event ledgers')
 ids=np.flatnonzero((rows['ramp'][:-1]<-2)&(rows['ramp'][1:]>=-2))+1;require(len(ids)==4,'four own trace crossings');cases=bank(directory/'selected.txt');halves=[p for i,p in enumerate(cases) if i%3!=0];out=[]
 for n,i in enumerate(ids):
  raw=lines[1+3*n].split(',');require(raw[0]=='EVENT' and len(raw)==10,'event mean codec');begin,end=map(int,raw[1:3]);before,after=decode(lines[2+3*n]),decode(lines[3+3*n]);require((begin,end)==(int(rows[i-1]['ticks']),int(rows[i]['ticks'])),'event exact clocks')
  require(before[43]<Decimal(-2)<=after[43] and float(before[43])==float(rows[i-1]['ramp']) and float(after[43])==float(rows[i]['ramp']),'event phase voltage')
  packed=struct.pack('<400d',*map(float,lines[3+3*n].split(',')[1:]));require(any(case[2]==before and struct.pack('<400d',*values)==packed for case,values in halves),'event belongs to selected actual half pair')
  alpha=(Decimal(-2)-before[43])/(after[43]-before[43]);phase=[a+alpha*(b-a) for a,b in zip(before,after)];require(0<=alpha<=1 and abs(phase[43]+2)<Decimal('1e-90'),'phase observation')
  out.append(dict(begin_ticks=begin,end_ticks=end,bracket_width_s=(end-begin)*TICK,alpha_decimal=str(alpha),interpolated_time_s=str((D(begin)+alpha*D(end-begin))*D(TICK)),native_cumulative_c1_charge_c=raw[3],native_cumulative_absolute_c=raw[4],native_cumulative_mean_integrals=raw[5:],before_state=list(map(str,before)),endpoint_state=list(map(str,after)),interpolated_phase_state=list(map(str,phase))))
 return out

def check(native):
 require(native['passed'] and len(native['profiles'])==2,'completed native profiles');inputs=json.loads((ROOT/'evidence/voice_candidate_cycles_inputs01.json').read_text(encoding='utf8'));old=json.loads((ROOT/'evidence/voice_dynamic_direction_reference01.json').read_text(encoding='utf8'));require(old['passed'],'admitted direction');baseline=np.array(old['candidate']['baseline_capacitor_drift_v']);base_j7=old['candidate']['j7_baseline_drift_v'];private={};profiles=[];cps=[]
 for p in sorted(native['profiles'],key=lambda p:-p['maximum_half_ticks']):
  maximum=p['maximum_half_ticks'];directory=Path(p['command'][3]);points=checkpoints(directory/'checkpoints.bin');seed=next(s for s in inputs['outputs'] if s['maximum_half_ticks']==maximum);require(points[0]['raw_sha256']==seed['sha256'],'initial candidate checkpoint by bytes');require(len(points)==43 and [q['ticks'] for q in points]==[0,1048576]+[k*ANCHOR for k in range(1,42)],'every common checkpoint')
  require(all(point['maximum']==maximum for point in points),'unchanged step setting');rows=trace(directory/'trace.bin');last=checkpoint((directory/'final.ckp').read_bytes());require(last==points[-1] and last['ticks']==5373952000 and int(rows[-1]['ticks'])==last['ticks'],'complete final clock');info=summary(p['stderr']);require(int(info['intervals'])*2==len(rows) and int(info['ticks'])==last['ticks'] and info['restore_replays']==3 and info['crossings']==4,'native ledger')
  delta=D(last['high'][43])+D(last['low'][43])-D(points[0]['high'][43])-D(points[0]['low'][43]);balance=abs(D(info['charge'])+D(1e-8)*delta)/D(info['absolute']);require(balance<=D(.002),'full C1 integral')
  events=event_bank(directory,rows);cycles=[]
  for i in range(3):
   a,b=events[i:i+2];changes=cycle_changes([a,b]);period=Decimal(b['interpolated_time_s'])-Decimal(a['interpolated_time_s']);require(period>0,'growing event period');drift=np.array([float(v['interpolated_phase_voltage_change_v']) for v in changes['capacitor_changes']]);j7=float(changes['phase_state_difference'][194]);l2=float(np.linalg.norm(drift)/np.linalg.norm(baseline));mx=float(np.max(abs(drift))/np.max(abs(baseline)));jratio=abs(j7/base_j7)
   integrals=[D(float(y))-D(float(x)) for x,y in zip(a['native_cumulative_mean_integrals'],b['native_cumulative_mean_integrals'])];means=ledger(list(map(Decimal,a['endpoint_state'])),list(map(Decimal,b['endpoint_state'])),integrals,D(b['end_ticks']-a['end_ticks'])*D(TICK))
   cycles.append(dict(interval=i+1,period_s=str(period),frequency_hz=str(Decimal(1)/period),**changes,radau_mean_ledger=means,capacitor_l2_ratio_to_original_base=l2,capacitor_max_ratio_to_original_base=mx,j7_drift_v=j7,j7_ratio_to_original_base=jratio,worsened_vs_fixed_candidate=[k for k,(x,y) in enumerate(zip(drift,old['candidate']['capacitor_drift_v'])) if abs(x)>abs(y)+2e-8],improvement_persists=l2<=.01 and mx<=.01 and jratio<=.01))
  means=[line for line in p['stderr'].splitlines() if line.startswith('MEAN_LEDGER,')];require(len(means)==1,'final mean ledger');lift=lambda q:[D(h)+D(l) for h,l in zip(q['high'],q['low'])];full=ledger(lift(points[0]),lift(last),[D(float(s)) for s in means[0].split(',')[1:]],D(last['ticks'])*D(TICK))
  profiles.append(dict(maximum_half_ticks=maximum,intervals=int(info['intervals']),endpoints=len(rows),events=events,cycles=cycles,full_c1_balance_relative=str(balance),full_radau_mean_ledger=full,min_half_ticks=int(rows['half_ticks'].min()),maximum_lte=float(rows['lte'].max()),max_bus_kcl_a=float(np.max(abs(rows['bus_kcl']))),max_c1_kcl_a=float(np.max(abs(rows['c1_kcl']))),restore_bit_replays=3));cps.append(points)
  for name in ['trace.bin','checkpoints.bin','final.ckp','events.txt','selected.txt','stdout.txt','stderr.txt']:
   path=(directory/name).relative_to(ROOT).as_posix();private[path]=sha(ROOT/path)
 shared=compare(*cps);refinement=[]
 for a,b in zip(profiles[0]['cycles'],profiles[1]['cycles']):
  cents=1200*abs(float(np.log2(float(a['period_s'])/float(b['period_s']))));require(cents<=1,'period refinement');da=np.array([float(c['interpolated_phase_voltage_change_v']) for c in a['capacitor_changes']]);db=np.array([float(c['interpolated_phase_voltage_change_v']) for c in b['capacitor_changes']]);ratios=abs(da-db)/(2e-8+1e-4*abs(db));require(np.max(ratios)<=1,'capacitor drift refinement');jratio=abs(a['j7_drift_v']-b['j7_drift_v'])/(1e-8+1e-4*abs(b['j7_drift_v']));require(jratio<=1,'J7 drift refinement');refinement.append(dict(interval=a['interval'],period_cents=cents,capacitor_drift_max_ratio=float(ratios.max()),worst_branch=int(ratios.argmax()),j7_drift_ratio=jratio))
 independent=selected_check(native['profiles']);require(len(independent['root_checks'])==36 and sum(x['rows'] for x in independent['root_checks'])==14400 and len(independent['current_checks'])==24 and len(independent['temporal_checks'])==12,'selected coverage');private.update(independent['input_sha256'])
 with (ROOT/inputs['candidate_path']).open('rb') as f:f.seek(24);original=f.read(3200)
 for seed in inputs['outputs']:require((ROOT/seed['path']).read_bytes()[24:]==original,'same candidate state');private[seed['path']]=sha(ROOT/seed['path'])
 private[inputs['candidate_path']]=sha(ROOT/inputs['candidate_path'])
 return dict(profiles=profiles,shared_clock_points=shared,return_refinement=refinement,new_independent=independent,input_sha256=private,adaptive_cycles_admitted=True,refinement_admitted=True,improvement_persists=all(c['improvement_persists'] for p in profiles for c in p['cycles']),steady_periodicity_admitted=False,global_settling_bound=False,physical_fidelity=False,real_time=False,independent_roots=0,independent_all_step_propagation=False,new_audio=False,new_spice_processes=0)

def main():
 out=ROOT/'evidence/voice_candidate_cycles_reference01.json';require(not out.exists(),'exclusive reference');name='evidence/voice_candidate_cycles_native01.json';native=json.loads((ROOT/name).read_text(encoding='utf8'));names={name,'evidence/voice_candidate_cycles_inputs01.json','evidence/voice_dynamic_direction_reference01.json','tools/check_candidate_cycles.py','docs/VOZ_CANDIDATO_CICLOS_PROTOCOLO.md'}
 for module in list(sys.modules.values()):
  f=getattr(module,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/candidate-cycles-reference/v1',passed=False,source_sha256=before);start=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(check(native))
  require(time.perf_counter()-start<=300,'reference budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_candidate_cycles.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;check(native)
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['wall_s']=time.perf_counter()-start;r['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==r['source_sha256_after'],'unchanged reference');out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CANDIDATE_REFERENCE',r['passed'],r.get('failure',''),r.get('improvement_persists'),flush=True)
if __name__=='__main__':main()
