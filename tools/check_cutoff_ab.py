"""Audit accepted coarse/fine histories, controller clocks and charged contour."""
import argparse,json,math,re,struct,sys,time,traceback
from decimal import Decimal,localcontext
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_cutoff_ab import START,BOUNDARIES,KEY,SHORT,CUT,cuts,DECAY,ALPHA
from cutoff_control_reference import state,lift,packed,scoped,currents,ledger,D
from joint_cycles_analysis import require,TICK
CODEC=struct.Struct('<8sQ6IdQ2d458d')
def checkpoint(raw):
 require(len(raw)==3736,'adaptive229 size');r=CODEC.unpack(raw);magic,ticks,maximum,limit,next_full,phase,model,flags,key,reserved,decay,alpha,*v=r;require(magic==b'RFCTF001' and phase==0 and model==1 and maximum in [1048576,524288] and limit in range(1,21) and flags==1 and reserved==0 and decay==DECAY and alpha==ALPHA[phase] and ticks%8==0 and START+BOUNDARIES[phase]<=ticks<=START+BOUNDARIES[phase+1] and next_full>=8 and next_full<=2*maximum and next_full&(next_full-1)==0,'adaptive metadata');require(struct.pack('<d',key)==struct.pack('<d',KEY[phase]) and bool(flags&2)==SHORT[phase] and CODEC.pack(*r)==raw and all(math.isfinite(x) for x in v),'typed recipe/roundtrip')
 for k in range(229):
  x=D(v[k])+D(v[229+k]);h=float(x);l=float(x-D(h));require(struct.pack('<2d',h,l)==struct.pack('<2d',v[k],v[229+k]),'normalized state')
 return dict(ticks=ticks,maximum=maximum,limit=limit,next_full=next_full,phase=phase,model=model,key=key,short=bool(flags&2),on=bool(flags&1),decay_ohm=decay,cutoff_fraction=alpha,values=v,sha256=__import__('hashlib').sha256(raw).hexdigest())
def lte(a,b):return max(float(abs(a[k]-b[k])/D(2e-9 if 98<=k<133 else 2e-6)) for k in range(229))
def motor(x,da,db,h):
 branch=lambda a,b:x[a]-x[b];c27=D(1e-5)/D(h)*(D(-4.5)*(da[12]-da[139])+D(2.5)*(db[12]-db[139]));series=branch(12,39)/D(33000);return [float(x[k]) for k in [46,43,12,39,194]]+[float(branch(46,39)/D(12500)),float(series),float(c27),float(series+c27)]
def profile(p,inp):
 on,maximum=p['final_decay'],p['maximum_half_ticks'];directory=Path(p['command'][2]);lines=(directory/'selected.txt').read_text(encoding='utf8').splitlines();require(lines[0]==f'PROFILE,{int(on)},{maximum}','profile');initial,iv=state(lines[1]);published=json.loads((ROOT/'evidence/voice_cutoff_reference01.json').read_text(encoding='utf8'));own=next(q for q in published['profiles'] if q['final_decay'] and q['maximum_half_ticks']==maximum);require(on and packed(iv)==packed(own['grids'][1]['values']),'own458 public history by bits');raw=(directory/'checkpoints.bin').read_bytes();require(len(raw)==12*3736,'all grid/boundary checkpoints');points=[checkpoint(raw[k:k+3736]) for k in range(0,len(raw),3736)];require(points[0]['ticks']==START and points[0]['maximum']==maximum and points[0]['next_full']==struct.unpack('<8sQ6IdQ2d458d',(ROOT/f'references-local/voice-cutoff01/{maximum}/event1-before.ckp').read_bytes())[4] and points[0]['limit']==20 and points[0]['key']==0. and not points[0]['short'] and packed(points[0]['values'])==packed(iv),'own seed metadata/bits');grid=[dict(ticks=START,values=iv)];pc=1;i=2;last=iv;phases=[];roots=[];ports=[];selected_errors=[];total_count=0;expected_replays=0;half_hist={};attempt_hist={};rollbacks=1;boundary_states=[];resets=[];last_ramp=float(initial[43]);last_ticks=START;replay_points=[];selected_accepted_count=0
 all_transition_count=0
 for phase in range(1):
  transition_cps=[(p.name,checkpoint(p.read_bytes())) for p in sorted(directory.glob(f'phase{phase}-transition*.ckp'))];transition_by_tick={q['ticks']:(name,q) for name,q in transition_cps};require(len(transition_by_tick)==len(transition_cps),'unique transition checkpoints')
  all_transition_count+=len(transition_cps)
  row=lines[i].split(',');require(row[0]=='BOUNDARY' and int(row[1])==phase and int(row[2])==START+BOUNDARIES[phase] and float(row[3])==KEY[phase] and int(row[4])==int(SHORT[phase]),'source clock');before,br=state(lines[i+1]);require(packed(br)==packed(last) and packed(br)==packed(points[pc]['values']) and points[pc]['phase']==phase,'boundary history');start_cp=points[pc];pc+=1;boundary_states.append(br);require(checkpoint((directory/f'phase{phase}-start.ckp').read_bytes())==start_cp,'restore start');i+=2
  count=0;inside_count=None;clock=START+BOUNDARIES[phase];next_full=start_cp['next_full'];targets=cuts(phase);gi=0;checks=[];obs=[];phase_traces=[];selected=0;previous_end=None;reset_indices=[];selection_indices=[];golden_index=None;transition_indices=[];selected_starts={}
  while not lines[i].startswith('LEDGER,'):
   if lines[i].startswith('GRID,'):
    row=lines[i].split(',');require(int(row[1])==phase and int(row[2])==targets[gi]==clock,'observation grid');x,v=state(lines[i+1]);point=points[pc];require(point['ticks']==clock and point['phase']==phase and point['next_full']==next_full and packed(point['values'])==packed(v),'grid checkpoint');grid.append(dict(ticks=clock,values=v));pc+=1;gi+=1;i+=2;last=v
    if gi==1:
     inside_count=count;inside=checkpoint((directory/f'phase{phase}-inside.ckp').read_bytes());require(inside==point,'inside checkpoint')
    continue
   row=lines[i].split(',');require(row[0]=='STEP' and len(row)==8,'accepted trace');_,ph,t0,t1,half,error,attempts,following=row;ph,t0,t1,half,attempts,following=map(int,[ph,t0,t1,half,attempts,following]);error=float(error);require(ph==phase and t0==clock and t1==t0+2*half and t1<=targets[gi] and half>=4 and half<=maximum and half&(half-1)==0 and 0<=error<=1 and 1<=attempts<=20,'accepted calendar/LTE')
   ticks=next_full
   while ticks>targets[gi]-clock:ticks//=2
   if t0 in transition_by_tick:transition_indices.append(count)
   require(2*half==ticks//(2**(attempts-1)) and following==(min(4*half,2*maximum) if error<=.25 else 2*half),'controller decisions');next_full=following;clock=t1;i+=1;triples=None;h=half*TICK
   if lines[i].startswith('SELECT,'):
    require(lines[i]==f'SELECT,{phase}','selected phase');i+=1;triples=[]
    for dt in [2*h,h,h]:
     row=lines[i].split(',');require(row[0]=='JOINT_ROOT' and int(row[1])==0 and float(row[2])==dt,'selected pair clock');states=[state(s)[0] for s in lines[i+1:i+6]];checks.append(scoped(KEY[phase],on,SHORT[phase],ALPHA[phase])((0,dt,*states)));triples.append(states);i+=6
    selected_starts[t0]=triples[0][0];coarse,mid,end=triples;require(coarse[0]==mid[0] and mid[-1]==end[0],'coarse/fine history');actual=lte(coarse[-1],end[-1]);require(abs(actual-error)<=2e-9 and actual<=1,'independent LTE from stored histories');selected_errors.append(dict(phase=phase,ticks=t1,native_ratio=error,independent_ratio=actual));selected+=1;selection_indices.append(count);selected_accepted_count+=1
   for k in range(2):
    row=lines[i].split(',');require(row[0]=='OBS','fine endpoint');ob=list(map(float,row[1:]));require(len(ob)==24 and int(ob[0])==t0+(k+1)*half and int(ob[1])==phase,'fine clock/codec');obs.append(ob);i+=1
    if triples is not None:
     q=triples[k+1];x=q[-1];v=[float(x[k]) for k in [205,203,194,221,217]]+[float(x[223])-float(x[225])]+[float(x[k]) for k in range(225,229)];require(v==ob[2:12],'native contour voltages');expected=currents(x,KEY[phase],on,SHORT[phase]);errors=[abs(a-b) for a,b in zip(expected,ob[12:15])];require(max(errors)<=1e-9,'actual contour currents');m=motor(x,q[1],q[2],h);me=[abs(a-b) for a,b in zip(m,ob[15:])];require(max(me[:5])==0 and max(me[5:])<=2e-11 and abs(ob[23])<=2e-11,'BUS currents and KCL');ports.append(dict(phase=phase,ticks=int(ob[0]),current_errors_a=errors,motor_current_errors_a=me[5:]))
    ramp=ob[16];tick=int(ob[0]);crossed=last_ramp< -2. and ramp>= -2.
    if crossed:
     record=lines[i].split(',');require(len(record)==6 and record[0]=='RESET' and int(record[1])==phase and int(record[2])==last_ticks and int(record[3])==tick and float(record[4])==last_ramp and float(record[5])==ramp,'reset endpoints');i+=1
     require(triples is not None,'reset stages selected');name=f'phase{phase}-reset{len(resets)}.ckp';cp_reset=checkpoint((directory/name).read_bytes());require(cp_reset['ticks']==t0 and cp_reset['phase']==phase,'reset incoming clock')
     require(lift(cp_reset['values'])==triples[0][0],'reset incoming history');alpha=(D(-2)-D(last_ramp))/(D(ramp)-D(last_ramp));time_s=(D(last_ticks)+alpha*D(tick-last_ticks))*D(TICK);resets.append(dict(phase=phase,bracket_ticks=[last_ticks,tick],bracket_ramp_v=[last_ramp,ramp],interpolated_time_s=str(time_s),accepted_start_ticks=t0,accepted_end_ticks=t1,half_ticks=half,checkpoint_path=name));reset_indices.append(count)
    else:require(not lines[i].startswith('RESET,'),'no false reset')
    last_ramp=ramp;last_ticks=tick
   phase_traces.append(dict(start_ticks=t0,end_ticks=t1,half_ticks=half,lte_ratio=error,attempts=attempts,next_full_ticks=following));count+=1;total_count+=1;half_hist[str(half)]=half_hist.get(str(half),0)+1;attempt_hist[str(attempts)]=attempt_hist.get(str(attempts),0)+1
  require(gi==len(targets) and selected==len(set([0,count-1,*reset_indices,*transition_indices]+([golden_index] if golden_index is not None else []))) and len(checks)==3*selected and len(obs)==2*count and clock==START+BOUNDARIES[phase+1],'phase completeness');row=lines[i].split(',');require(len(row)==12 and int(row[1])==phase and int(row[2])==clock,'ledger clock');integrals=list(map(float,row[3:]));after,ar=state(lines[i+1]);require(packed(ar)==packed(last),'phase end state');balance=ledger(before,after,integrals,BOUNDARIES[phase+1]-BOUNDARIES[phase]);i+=2;require(selection_indices==sorted(set([0,count-1,*reset_indices,*transition_indices]+([golden_index] if golden_index is not None else []))),'all reset/edge selections');starts=[(0,f'phase{phase}-start.ckp')]+([(inside_count,f'phase{phase}-inside.ckp')] if inside_count is not None else [])+[(k,r['checkpoint_path']) for k,r in zip(reset_indices,[r for r in resets if r['phase']==phase])];starts.extend((k,transition_by_tick[phase_traces[k]['start_ticks']][0]) for k in transition_indices);require(len(transition_indices)==len(transition_cps) and all(lift(q['values'])==selected_starts[q['ticks']] for _,q in transition_cps),'all transitions selected with incoming history');replay_points.extend(dict(phase=phase,start_index=k,path=n,accepted_replayed=min(16,count-k)) for k,n in starts);expected_replays+=sum(min(16,count-k) for k,n in starts);phases.append(dict(phase=phase,duration_ticks=BOUNDARIES[phase+1]-BOUNDARIES[phase],accepted_steps=count,fine_steps=2*count,final_voltages_v=dict(zip(['C2','LOUDNESS','J7','C7','RESET_DRIVER','C4','Q25_B','Q25_C','Q15_B','Q15_C'],obs[-1][2:12])),native_integrals_c=integrals,ledger=balance,accepted_trace=phase_traces,final_high_low=ar));roots.extend(checks)
 row=lines[i].split(',');require(row[0]=='TOTAL' and len(row)==10 and i+2==len(lines) and pc==12,'total completeness');total=list(map(float,row[1:]));final,fr=state(lines[i+1]);require(packed(fr)==packed(last) and checkpoint((directory/'final.ckp').read_bytes())==points[-1],'final identity');balance=ledger(initial,final,total,BOUNDARIES[-1])
 for k in range(9):require(abs(sum(D(p['native_integrals_c'][k]) for p in phases)-D(total[k]))<=D(1e-18),'ledger composition')
 summary=re.search(r'COMPLETED,on=(\d+),max=(\d+),accepted=(\d+),restores=(\d+),replays=(\d+),corruptions=(\d+),rollbacks=(\d+),crossings=(\d+)',p['stderr']);require(summary is not None and tuple(map(int,summary.groups()))==(int(on),maximum,total_count,2+len(resets)+all_transition_count,expected_replays,4,1,len(resets)),'native replay/rollback coverage');require(len(resets)>=2,'continued oscillator resets');
 replay_lines=(directory/'replays.txt').read_text(encoding='utf8').splitlines();actual=[]
 for line in replay_lines:
  marker,phase,name,tick,count=line.split(',');require(marker=='REPLAY','replay codec');actual.append((int(phase),name,int(tick),int(count)))
 expected=[]
 for point in replay_points:
  q=checkpoint((directory/point['path']).read_bytes());expected.append((point['phase'],point['path'],q['ticks'],point['accepted_replayed']))
 require(sorted(actual)==sorted(expected),'all local replay counts/checkpoints')
 maximum_probes=int(re.search(r'max_probes=(\d+)',p['stderr']).group(1));require(1<=maximum_probes<=3,'bounded replay slots')
 return dict(maximum_active_replay_probes=maximum_probes,final_decay=on,maximum_half_ticks=maximum,grids=grid,phases=phases,total_ledger=balance,root_checks=roots,port_checks=ports,selected_lte=selected_errors,half_tick_histogram=half_hist,attempt_histogram=attempt_hist,accepted_steps=total_count,fine_steps=2*total_count,replayed_accepted_steps=expected_replays,restores=2+len(resets)+all_transition_count,selected_accepted_count=selected_accepted_count,resets=resets,replay_points=replay_points,corruptions=4,rollbacks=1,input_sha256={f.relative_to(ROOT).as_posix():sha(f) for f in directory.iterdir() if f.is_file()})



import numpy as np
"""Original graph, full-state refinement, control event and finite discharge."""
from release_audit_body import flux_audit as _unused  # Source identity only; no reuse of its experiment globals.


def seam(p):
 m=p['maximum_half_ticks'];d=ROOT/f'references-local/cutoff-ab01/{m}';parent=ROOT/f'references-local/voice-cutoff01/{m}/event1-before.ckp';a=parent.read_bytes();require(a==(d/'incoming-original.ckp').read_bytes()==(d/'checkpoints.bin').read_bytes()[:3736],'exact common origin including proposal and complete recipe');require((d/'seam-old.bin').read_bytes()==(d/'seam-new.bin').read_bytes(),'four complete open advances by bits');return dict(maximum_half_ticks=m,parent_sha256=sha(parent),preserved_values=458,complete_accepted_bit_comparisons=4)
def flux_audit(p):
 import inspect
 from release_audit_body import flux_audit as original
 body=inspect.getsource(original).replace('release-voice01','cutoff-ab01').replace('D(100000)','D(DECAY)');ns=dict(globals());exec(compile(body,'<unchanged open flux gates>','exec'),ns);return ns['flux_audit'](p)
def audit():
 native=json.loads((ROOT/'evidence/cutoff_ab_native01.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/cutoff_ab_inputs01.json').read_text(encoding='utf8'));old=json.loads((ROOT/'evidence/voice_cutoff_reference01.json').read_text(encoding='utf8'));require(native['passed'] and old['passed'],'admitted parent and open native');profiles=[profile(p,inp) for p in native['profiles']];compares=[];a,b=profiles;require(len(a['grids'])==len(b['grids'])==11 and len(a['resets'])==len(b['resets']),'open shared clocks and resets')
 for x,y in zip(a['grids'],b['grids']):
  require(x['ticks']==y['ticks'],'open common clock');u,v=lift(x['values']),lift(y['values']);ratio=lte(u,v);require(ratio<=1,'229 open refinement');compares.append(dict(ticks=x['ticks'],gate_ratio=ratio,max_voltage_error_v=max(float(abs(u[k]-v[k])) for k in range(229) if not 98<=k<133)))
 for x,y in zip(a['resets'],b['resets']):require(abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']))<=D(1e-8),'open reset refinement')
 flux=[flux_audit(p) for p in profiles];require(len(flux[0]['events'])==len(flux[1]['events']),'open transition counts')
 for x,y in zip(flux[0]['events'],flux[1]['events']):require(x['kind']==y['kind'] and x['direction']==y['direction'] and abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']))<=D(1e-7),'open transition refinement')
 forks=[]
 for p in profiles:
  m=p['maximum_half_ticks'];closed=next(q for q in old['profiles'] if q['maximum_half_ticks']==m);grid=[g for g in closed['grids'] if START<=g['ticks']<=START+BOUNDARIES[-1]];require(len(grid)==11 and packed(grid[0]['values'])==packed(p['grids'][0]['values']),'closed/open common 458 state and window');d=ROOT/f'references-local/voice-cutoff01/{m}';before=(d/'event1-before.ckp').read_bytes();after=(d/'event1-after.ckp').read_bytes();require(before[:28]==after[:28] and before[32:64]==after[32:64] and before[72:]==after[72:] and struct.unpack_from('<d',before,64)[0]==1. and struct.unpack_from('<d',after,64)[0]==.5,'only phase and cutoff differ at fork');differences=[]
  for x,y in zip(p['grids'],grid):
   require(x['ticks']==y['ticks'],'A/B identical observation clocks');u,v=lift(x['values']),lift(y['values']);differences.append(dict(ticks=x['ticks'],c2_difference_v=float(u[205]-v[205]),loudness_difference_v=float(u[203]-v[203]),j7_difference_v=float(u[194]-v[194]),q26_base_difference_v=float(u[195]-v[195]),tail_current_open_a=float((u[138]-u[198])/D(680)),tail_current_closed_a=float((v[138]-v[198])/D(680)),max_voltage_difference_v=max(float(abs(u[k]-v[k])) for k in range(229) if not 98<=k<133)))
  forks.append(dict(maximum_half_ticks=m,start_ticks=START,end_ticks=START+BOUNDARIES[-1],common_state_values=458,common_proposal=struct.unpack_from('<I',before,24)[0],open_alpha=1.,closed_alpha=.5,closed_accepted_steps=closed['phases'][1]['accepted_steps'],closed_fine_steps=closed['phases'][1]['fine_steps'],closed_selected_accepted_count=sum(q['phase']==1 for q in closed['selected_lte']),closed_ledger=closed['phases'][1]['ledger'],same_clock_differences=differences))
 return dict(profiles=profiles,seams=[seam(p) for p in profiles],flux_checks=flux,same_clock_refinement=compares,forks=forks,independent_candidates=6*sum(p['selected_accepted_count'] for p in profiles),independent_nonlinear_rows=1374*sum(p['selected_accepted_count'] for p in profiles),accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_steps=sum(p['fine_steps'] for p in profiles),restores=sum(p['restores'] for p in profiles),replayed_accepted_steps=sum(p['replayed_accepted_steps'] for p in profiles),maximum_active_replay_probes=max(p['maximum_active_replay_probes'] for p in profiles),rejected_corruptions=8,atomic_rollbacks=2,seam_compared_accepted=8,open_duration_s=.008,closed_coverage_inherited=True,closed_equations_reexecuted=False,new_continuous_history_duration_s=0,new_source_event=False,physical_fidelity=False,real_time=False)
def main():
 names={'tools/check_cutoff_ab.py','tools/prepare_cutoff_ab.py','tools/cutoff_ab_audit.py','evidence/cutoff_ab_native01.json','evidence/cutoff_ab_inputs01.json','evidence/voice_cutoff_reference01.json','docs/VOZ_CUTOFF_AB_PROTOCOLO.md'}
 for module in list(sys.modules.values()):
  f=getattr(module,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=before);started=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(audit())
  require(time.perf_counter()-started<=600,'oracle budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:__import__('base64').b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith('.py')}
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in sorted(names)},wall_s=time.perf_counter()-started);require(before==r['source_sha256_after'],'stable auditor');write('evidence/cutoff_ab_reference01.json',r);print('CUTOFF_AB_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''));require(r['passed'],'original open branch and common-origin A/B')
if __name__=='__main__':main()
