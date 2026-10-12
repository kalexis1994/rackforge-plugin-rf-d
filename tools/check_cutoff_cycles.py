"""Join only exact continuation seams; independently audit actual cycle candidates."""
import argparse,json,math,struct,sys,time,traceback,types
from decimal import Decimal,localcontext
from functools import partial
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,trace,checkpoint,checkpoints,compare,TICK
from prepare_cutoff_cycles import MARKS
from check_cutoff_temporal import scoped_check,CONTROL
from check_joint_corrected_cycles import events,ledger
from check_joint_conditioned_cycles import cycle_changes
from analyze_joint_cycles import summary
from check_joint_reference import D
from render_vco1_circuit import coefficients
START=131072000;GOAL=2752512000
def controls(directory,rows):
 raw=(directory/'control.bin').read_bytes();require(raw[:8]==b'RFJCTL01' and len(raw)==8+CONTROL.itemsize*len(rows),'full control codec');ctl=np.frombuffer(raw,dtype=CONTROL,offset=8);require(np.array_equal(ctl['ticks'],rows['ticks']) and b'RFJCTL01'+ctl.tobytes()==raw,'control clocks/roundtrip');require(all(np.isfinite(ctl[n]).all() for n in ['c18_v','tail_a','charge_c','kcl_a']) and np.max(abs(ctl['kcl_a']))<=1e-12,'control finite/KCL');return ctl
def point_ledger(a,b,seconds,integral):
 v=lambda q,k:D(q['high'][k])+D(q['low'][k]);delta=D(100e-12)*(v(b,195)-v(a,195));error=abs(delta+integral);gate=D(1e-12)*seconds;require(error<=gate,'C18 segment/full charge ledger');return dict(delta_charge_c=str(delta),dc_integral_c=str(integral),error_c=str(error),gate_c=str(gate),native_stage_integrals=True)
def check(native):
 require(native['passed'] and len(native['profiles'])==2,'two complete continuations');parent=json.loads((ROOT/'evidence/voice_cutoff_temporal_native01.json').read_text(encoding='utf8'));old=json.loads((ROOT/'evidence/voice_cutoff_temporal_tests01.json').read_text(encoding='utf8'));require(parent['passed'] and old['passed'],'admitted prefix');private={};profiles=[];shared=[];independent=[];signals=[]
 for p in sorted(native['profiles'],key=lambda p:-p['maximum_half_ticks']):
  maximum=p['maximum_half_ticks'];directory=Path(p['command'][3]);prefix=next(c for c in parent['profiles'] if c['cutoff_fraction']==1. and c['maximum_half_ticks']==maximum);pd=Path(prefix['command'][3]);before=checkpoints(pd/'checkpoints.bin');points=checkpoints(directory/'checkpoints.bin');require([q['ticks'] for q in points]==[START,*MARKS] and all(q['maximum']==maximum for q in points),'continuation clocks/settings');require(points[0]==before[-1] and points[0]['raw_sha256']==sha(pd/'final.ckp'),'exact typed seam');rows=trace(directory/'trace.bin',start_ticks=START);pr=trace(pd/'trace.bin');all_rows=np.concatenate([pr,rows]);require(np.all(np.diff(all_rows['ticks'])>0),'joined endpoint timeline');final=checkpoint((directory/'final.ckp').read_bytes());require(final==points[-1] and int(rows[-1]['ticks'])==GOAL,'complete final clock');info=summary(p['stderr']);prior=summary(prefix['stderr']);require(info['intervals']*2==len(rows) and info['ticks']==GOAL and info['crossings']==2 and info['restore_replays']==2,'continuation native ledger');ctl=controls(directory,rows);pc=controls(pd,pr)
  v=lambda cp,k:D(cp['high'][k])+D(cp['low'][k]);short_seconds=D(START)*D(TICK);long_seconds=D(GOAL-START)*D(TICK);full_seconds=D(GOAL)*D(TICK);segment=point_ledger(points[0],final,long_seconds,D(ctl['charge_c'][-1]));full=point_ledger(before[0],final,full_seconds,D(pc['charge_c'][-1])+D(ctl['charge_c'][-1]));checks=[]
  for cp in points[1:]:
   ids=np.flatnonzero(ctl['ticks']==cp['ticks']);require(len(ids)==1,'unique control checkpoint');r=ctl[ids[0]];require(float(v(cp,195))==float(r['c18_v']),'control full-state identity');tail=(v(cp,138)-v(cp,198))/D(680.);require(abs(tail-D(r['tail_a']))<=D(1e-11),'tail observation');checks.append(dict(ticks=cp['ticks'],c18_v=str(v(cp,195)),tail_a=str(tail),**point_ledger(points[0],cp,D(cp['ticks']-START)*D(TICK),D(r['charge_c']))))
  charge=D(info['charge']);absolute=D(info['absolute']);balance=abs(charge+D(1e-8)*(v(final,43)-v(points[0],43)))/absolute;total_charge=charge+D(prior['charge']);total_absolute=absolute+D(prior['absolute']);total_balance=abs(total_charge+D(1e-8)*(v(final,43)-v(before[0],43)))/total_absolute;require(max(balance,total_balance)<=D(.002),'C1 segment/full balance')
  def means(profile):
   lines=[s for s in profile['stderr'].splitlines() if s.startswith('MEAN_LEDGER,')];require(len(lines)==1,'Radau mean ledger');return [D(float(s)) for s in lines[0].split(',')[1:]]
  lift=lambda q:[v(q,k) for k in range(200)];mi=means(p);pm=means(prefix);long_mean=ledger(lift(points[0]),lift(final),mi,long_seconds);full_mean=ledger(lift(before[0]),lift(final),[a+b for a,b in zip(mi,pm)],full_seconds)
  observer=types.FunctionType(events.__code__,dict(events.__globals__,trace=partial(trace,start_ticks=START)));ev=observer(directory);changes=cycle_changes(ev)
  for c in changes['capacitor_changes']:c['physical_b']='PLUS' if c['index']==11 else 'GROUND' if c['b'] is None else c['b'];c['fixed_reference_cancels_in_changes']=c['b'] is None
  period=Decimal(ev[1]['interpolated_time_s'])-Decimal(ev[0]['interpolated_time_s']);require(period>0,'own growing-cross period');reference=scoped_check(1.)([p]);require(len(reference['root_checks'])==69 and len(reference['current_checks'])==46 and len(reference['temporal_checks'])==23,'selected coverage');independent.append(dict(maximum_half_ticks=maximum,**reference));private.update(reference['input_sha256'])
  a,b=map(float,[e['interpolated_time_s'] for e in ev]);t=all_rows['ticks'].astype(float)*TICK;knots=np.r_[a,t[(t>a)&(t<b)],b];phase=(knots-a)/(b-a);phase[0]=0.;phase[-1]=1.;voltage=np.interp(knots,t,all_rows['j7']);ptp=float(np.ptp(voltage));seam=float(abs(voltage[-1]-voltage[0]));require(ptp>0,'nonconstant observed J7 interval');signals.append((phase,voltage,float(period)));profiles.append(dict(maximum_half_ticks=maximum,new_intervals=int(info['intervals']),new_endpoints=len(rows),inherited_intervals=int(prior['intervals']),total_simulated_s=float(full_seconds),new_restore_bit_replays=2,exact_checkpoint_seam=True,minimum_half_ticks=int(rows['half_ticks'].min()),maximum_lte=float(rows['lte'].max()),events=ev,period_s=str(period),**changes,control_checkpoint_ledgers=checks,c18_segment_ledger=segment,c18_full_ledger=full,c1_segment_balance_relative=str(balance),c1_full_balance_relative=str(total_balance),segment_radau_mean_ledger=long_mean,full_radau_mean_ledger=full_mean,j7_cycle_min_v=float(voltage.min()),j7_cycle_max_v=float(voltage.max()),j7_cycle_ptp_v=ptp,j7_phase_seam_v=seam,j7_seam_relative=seam/ptp))
  shared.append([*before,*points[1:]])
  for d in [pd,directory]:
   for name in ['trace.bin','control.bin','checkpoints.bin','final.ckp','selected.txt','events.txt','stdout.txt','stderr.txt']:
    path=(d/name).relative_to(ROOT).as_posix();private[path]=sha(ROOT/path)
    if d==pd:require(private[path]==old['private_input_sha256'][path],'inherited data identity')
 refinement=compare(*shared);cents=1200*abs(math.log2(float(profiles[0]['period_s'])/float(profiles[1]['period_s'])));require(cents<=1,'period refinement');count=min(int(math.floor(.45*48000/p)) for _,_,period in signals for p in [1/period]);cs=[coefficients(phase,v,count) for phase,v,_ in signals];rms=float(np.sqrt(2*np.sum(abs(cs[1][1:])**2)));error=float(np.sqrt(2*np.sum(abs(cs[0][1:]-cs[1][1:])**2)));gate=.01*rms+1e-7;listen=all(p['j7_seam_relative']<=.01 for p in profiles) and error<=gate
 return dict(profiles=profiles,new_independent=independent,same_clock_refinement=refinement,period_refinement_cents=cents,input_sha256=private,independent_candidates=138,independent_nonlinear_rows=55200,current_observations=92,lte_observations=46,new_restore_bit_replays=4,inherited_prefix_reexecuted=False,continuation_admitted=True,new_initial_roots_applied=0,native_auxiliary_vco_startup_solves=0,inherited_prefix_native_auxiliary_vco_startup_calls=2,inherited_prefix_startup_result_used=False,independent_all_step_propagation=False,steady_periodicity_admitted=False,physical_fidelity=False,real_time=False,new_audio=False,listening_candidate_admitted=listen,listening_proposal=dict(harmonics=count,phase_aligned_rms_error_v=error,rms_gate_v=gate,fine_rms_v=rms,coefficients=[[[float(c.real),float(c.imag)] for c in values] for values in cs],sample_rate_hz=48000,volts_per_full_scale=.1,duration_s=2.,gain_relative_to_8v_adapter=80.))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args();name='evidence/voice_cutoff_cycles_native01.json';out=ROOT/f'evidence/voice_cutoff_cycles_reference{args.attempt:02d}.json';require(not out.exists(),'exclusive reference');native=json.loads((ROOT/name).read_text(encoding='utf8'));names={name,'evidence/voice_cutoff_cycles_inputs01.json','evidence/voice_cutoff_temporal_native01.json','evidence/voice_cutoff_temporal_tests01.json','tools/check_cutoff_cycles.py','docs/VOZ_CUTOFF_CICLOS_PROTOCOLO.md'}
 for module in list(sys.modules.values()):
  f=getattr(module,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(schema='rf-d/cutoff-cycles-reference/v1',passed=False,source_sha256=before);start=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(check(native))
  require(time.perf_counter()-start<=300,'reference budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_cutoff_cycles.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;check(native)
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==r['source_sha256_after'],'unchanged reference');r['wall_s']=time.perf_counter()-start;out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CUTOFF_CYCLES_REFERENCE',r['passed'],r.get('failure',''),r.get('listening_candidate_admitted'),flush=True)
if __name__=='__main__':main()
