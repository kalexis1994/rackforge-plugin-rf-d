"""Audit accepted coarse/fine histories, controller clocks and charged contour."""
import argparse,json,math,re,struct,sys,time,traceback
from decimal import localcontext
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_contour_engine import START,BOUNDARIES,KEY,SHORT
from check_latch_charge import state,lift,packed,scoped,currents,ledger,D,checkpoint as old_checkpoint
from joint_cycles_analysis import require,TICK
CODEC=struct.Struct('<8sQ6IdQ458d');CUT=5242880
def checkpoint(raw):
 require(len(raw)==3720,'adaptive229 size');r=CODEC.unpack(raw);magic,ticks,maximum,limit,next_full,phase,model,flags,key,reserved,*v=r;require(magic==b'RFCTRE01' and phase in range(3) and model==1 and maximum in [131072,65536] and limit in range(1,21) and flags in range(4) and reserved==0 and ticks%8==0 and START+BOUNDARIES[phase]<=ticks<=START+BOUNDARIES[phase+1] and next_full>=8 and next_full<=2*maximum and next_full&(next_full-1)==0,'adaptive metadata');require(struct.pack('<d',key)==struct.pack('<d',KEY[phase]) and bool(flags&2)==SHORT[phase] and CODEC.pack(*r)==raw and all(math.isfinite(x) for x in v),'typed recipe/roundtrip')
 for k in range(229):
  x=D(v[k])+D(v[229+k]);h=float(x);l=float(x-D(h));require(struct.pack('<2d',h,l)==struct.pack('<2d',v[k],v[229+k]),'normalized state')
 return dict(ticks=ticks,maximum=maximum,limit=limit,next_full=next_full,phase=phase,model=model,key=key,short=bool(flags&2),on=bool(flags&1),values=v,sha256=__import__('hashlib').sha256(raw).hexdigest())
def lte(a,b):return max(float(abs(a[k]-b[k])/D(2e-9 if 98<=k<133 else 2e-6)) for k in range(229))
def motor(x,da,db,h):
 branch=lambda a,b:x[a]-x[b];c27=D(1e-5)/D(h)*(D(-4.5)*(da[12]-da[139])+D(2.5)*(db[12]-db[139]));series=branch(12,39)/D(33000);return [float(x[k]) for k in [46,43,12,39,194]]+[float(branch(46,39)/D(12500)),float(series),float(c27),float(series+c27)]
def profile(p,inp):
 on,maximum=p['final_decay'],p['maximum_half_ticks'];directory=Path(p['command'][2]);lines=(directory/'selected.txt').read_text(encoding='utf8').splitlines();require(lines[0]==f'PROFILE,{int(on)},{maximum}','profile');initial,iv=state(lines[1]);seed=next(s for s in inp['seeds'] if s['final_decay']==on and s['maximum_half_ticks']==maximum);cp=checkpoint((ROOT/seed['path']).read_bytes());old=old_checkpoint((ROOT/seed['origin_path']).read_bytes());require(cp['ticks']==START and packed(iv)==packed(cp['values'])==packed(old['values']),'own458 history by bits');raw=(directory/'checkpoints.bin').read_bytes();require(len(raw)==15*3720,'all grid/boundary checkpoints');points=[checkpoint(raw[k:k+3720]) for k in range(0,len(raw),3720)];require(points[0]['sha256']==seed['sha256'],'seed identity');grid=[dict(ticks=START,values=iv)];pc=1;i=2;last=iv;phases=[];roots=[];ports=[];selected_errors=[];total_count=0;expected_replays=0;half_hist={};attempt_hist={};rollbacks=1;boundary_states=[]
 for phase in range(3):
  row=lines[i].split(',');require(row[0]=='BOUNDARY' and int(row[1])==phase and int(row[2])==START+BOUNDARIES[phase] and float(row[3])==KEY[phase] and int(row[4])==int(SHORT[phase]),'source clock');before,br=state(lines[i+1]);require(packed(br)==packed(last) and packed(br)==packed(points[pc]['values']) and points[pc]['phase']==phase,'boundary history');start_cp=points[pc];pc+=1;boundary_states.append(br);require(checkpoint((directory/f'phase{phase}-start.ckp').read_bytes())==start_cp,'restore start');i+=2
  if phase==1:
   require(lines[i].startswith('ROLLBACK,AttemptLimit('),'induced attempt rejection');failed=checkpoint((directory/'attempt-rollback.ckp').read_bytes());require(failed['limit']==1 and failed['ticks']==start_cp['ticks'] and packed(failed['values'])==packed(br),'forced rollback bytes');i+=1;rollbacks+=1
  count=0;inside_count=None;clock=START+BOUNDARIES[phase];next_full=start_cp['next_full'];targets=[START+BOUNDARIES[phase+1]] if phase==0 else [START+BOUNDARIES[phase]+k*CUT for k in range(1,6)];gi=0;checks=[];obs=[];phase_traces=[];selected=0;previous_end=None
  while not lines[i].startswith('LEDGER,'):
   if lines[i].startswith('GRID,'):
    row=lines[i].split(',');require(int(row[1])==phase and int(row[2])==targets[gi]==clock,'observation grid');x,v=state(lines[i+1]);point=points[pc];require(point['ticks']==clock and point['phase']==phase and point['next_full']==next_full and packed(point['values'])==packed(v),'grid checkpoint');grid.append(dict(ticks=clock,values=v));pc+=1;gi+=1;i+=2;last=v
    if phase>0 and gi==1:
     inside_count=count;inside=checkpoint((directory/f'phase{phase}-inside.ckp').read_bytes());require(inside==point,'inside checkpoint')
    continue
   row=lines[i].split(',');require(row[0]=='STEP' and len(row)==8,'accepted trace');_,ph,t0,t1,half,error,attempts,following=row;ph,t0,t1,half,attempts,following=map(int,[ph,t0,t1,half,attempts,following]);error=float(error);require(ph==phase and t0==clock and t1==t0+2*half and t1<=targets[gi] and half>=4 and half<=maximum and half&(half-1)==0 and 0<=error<=1 and 1<=attempts<=20,'accepted calendar/LTE')
   ticks=next_full
   while ticks>targets[gi]-clock:ticks//=2
   require(2*half==ticks//(2**(attempts-1)) and following==(min(4*half,2*maximum) if error<=.25 else 2*half),'controller decisions');next_full=following;clock=t1;i+=1;triples=None;h=half*TICK
   if lines[i].startswith('SELECT,'):
    require(lines[i]==f'SELECT,{phase}','selected phase');i+=1;triples=[]
    for dt in [2*h,h,h]:
     row=lines[i].split(',');require(row[0]=='JOINT_ROOT' and int(row[1])==0 and float(row[2])==dt,'selected pair clock');states=[state(s)[0] for s in lines[i+1:i+6]];checks.append(scoped(KEY[phase],on,SHORT[phase])((0,dt,*states)));triples.append(states);i+=6
    coarse,mid,end=triples;require(coarse[0]==mid[0] and mid[-1]==end[0],'coarse/fine history');actual=lte(coarse[-1],end[-1]);require(abs(actual-error)<=2e-9 and actual<=1,'independent LTE from stored histories');selected_errors.append(dict(phase=phase,ticks=t1,native_ratio=error,independent_ratio=actual));selected+=1
   for k in range(2):
    row=lines[i].split(',');require(row[0]=='OBS','fine endpoint');ob=list(map(float,row[1:]));require(len(ob)==24 and int(ob[0])==t0+(k+1)*half and int(ob[1])==phase,'fine clock/codec');obs.append(ob);i+=1
    if triples is not None:
     q=triples[k+1];x=q[-1];v=[float(x[k]) for k in [205,203,194,221,217]]+[float(x[223])-float(x[225])]+[float(x[k]) for k in range(225,229)];require(v==ob[2:12],'native contour voltages');expected=currents(x,KEY[phase],on,SHORT[phase]);errors=[abs(a-b) for a,b in zip(expected,ob[12:15])];require(max(errors)<=1e-9,'actual contour currents');m=motor(x,q[1],q[2],h);me=[abs(a-b) for a,b in zip(m,ob[15:])];require(max(me[:5])==0 and max(me[5:])<=2e-11 and abs(ob[23])<=2e-11,'BUS currents and KCL');ports.append(dict(phase=phase,ticks=int(ob[0]),current_errors_a=errors,motor_current_errors_a=me[5:]))
   phase_traces.append(dict(start_ticks=t0,end_ticks=t1,half_ticks=half,lte_ratio=error,attempts=attempts,next_full_ticks=following));count+=1;total_count+=1;half_hist[str(half)]=half_hist.get(str(half),0)+1;attempt_hist[str(attempts)]=attempt_hist.get(str(attempts),0)+1
  require(gi==len(targets) and selected==2 and len(checks)==6 and len(obs)==2*count and clock==START+BOUNDARIES[phase+1],'phase completeness');row=lines[i].split(',');require(len(row)==12 and int(row[1])==phase and int(row[2])==clock,'ledger clock');integrals=list(map(float,row[3:]));after,ar=state(lines[i+1]);require(packed(ar)==packed(last),'phase end state');balance=ledger(before,after,integrals,BOUNDARIES[phase+1]-BOUNDARIES[phase]);i+=2;expected_replays+=count+(count-inside_count if inside_count is not None else 0);phases.append(dict(phase=phase,duration_ticks=BOUNDARIES[phase+1]-BOUNDARIES[phase],accepted_steps=count,fine_steps=2*count,final_voltages_v=dict(zip(['C2','LOUDNESS','J7','C7','RESET_DRIVER','C4','Q25_B','Q25_C','Q15_B','Q15_C'],obs[-1][2:12])),native_integrals_c=integrals,ledger=balance,accepted_trace=phase_traces,final_high_low=ar));roots.extend(checks)
 row=lines[i].split(',');require(row[0]=='TOTAL' and len(row)==10 and i+2==len(lines) and pc==15,'total completeness');total=list(map(float,row[1:]));final,fr=state(lines[i+1]);require(packed(fr)==packed(last) and checkpoint((directory/'final.ckp').read_bytes())==points[-1],'final identity');balance=ledger(initial,final,total,BOUNDARIES[-1])
 for k in range(9):require(abs(sum(D(p['native_integrals_c'][k]) for p in phases)-D(total[k]))<=D(1e-18),'ledger composition')
 summary=re.search(r'COMPLETED,on=(\d+),max=(\d+),accepted=(\d+),restores=(\d+),replays=(\d+),corruptions=(\d+),rollbacks=(\d+)',p['stderr']);require(summary is not None and tuple(map(int,summary.groups()))==(int(on),maximum,total_count,5,expected_replays,4,2),'native replay/rollback coverage');return dict(final_decay=on,maximum_half_ticks=maximum,grids=grid,phases=phases,total_ledger=balance,root_checks=roots,port_checks=ports,selected_lte=selected_errors,half_tick_histogram=half_hist,attempt_histogram=attempt_hist,accepted_steps=total_count,fine_steps=2*total_count,replayed_accepted_steps=expected_replays,restores=5,corruptions=4,rollbacks=2,input_sha256={f.relative_to(ROOT).as_posix():sha(f) for f in directory.iterdir() if f.is_file()})
def audit():
 native=json.loads((ROOT/'evidence/voice_contour_engine_native01.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_contour_engine_inputs01.json').read_text(encoding='utf8'));require(native['passed'] and len(native['profiles'])==4,'native campaign');profiles=[profile(p,inp) for p in native['profiles']];compares=[]
 for on in [True,False]:
  a,b=[next(p for p in profiles if p['final_decay']==on and p['maximum_half_ticks']==h) for h in [131072,65536]]
  for x,y in zip(a['grids'],b['grids']):
   require(x['ticks']==y['ticks'],'same clocks');u,v=lift(x['values']),lift(y['values']);ratio=lte(u,v);require(ratio<=1,'229 global refinement');compares.append(dict(final_decay=on,ticks=x['ticks'],gate_ratio=ratio,max_voltage_error_v=max(float(abs(u[k]-v[k])) for k in range(229) if not 98<=k<133)))
 return dict(profiles=profiles,same_clock_refinement=compares,independent_candidates=144,independent_nonlinear_rows=32976,native_current_endpoint_vectors=48,native_current_values=144,accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_steps=sum(p['fine_steps'] for p in profiles),replayed_accepted_steps=sum(p['replayed_accepted_steps'] for p in profiles),restores=20,rejected_corruptions=16,atomic_rollbacks=8,inherited_bit_coordinates=458,source_boundary_bit_coordinates=458,adaptive229_window_admitted=True,full_contour_trajectory_admitted=False,all_board2_junction_charge_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);a=parser.parse_args();names={'tools/check_contour_engine.py','evidence/voice_contour_engine_native01.json','evidence/voice_contour_engine_inputs01.json','docs/VOZ_CONTORNO_ADAPTATIVO_PROTOCOLO.md'}
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=before);t=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(audit())
  require(time.perf_counter()-t<=300,'oracle budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_contour_engine.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};r['wall_s']=time.perf_counter()-t;require(before==r['source_sha256_after'],'stable auditor');write(f'evidence/voice_contour_engine_reference{a.attempt:02d}.json',r);print('CONTOUR_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
