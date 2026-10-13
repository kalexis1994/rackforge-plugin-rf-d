
def seam(p):
 maximum=p['maximum_half_ticks'];directory=ROOT/f'references-local/release-voice01/{maximum}';parent=ROOT/f'references-local/sustained-voice01/{maximum}/final.ckp';raw=parent.read_bytes();copy=(directory/'incoming-original.ckp').read_bytes();new=(directory/'checkpoints.bin').read_bytes()[:3720]
 expected=bytearray(raw);expected[:8]=b'RFREL001';expected[28:32]=struct.pack('<I',0)
 require(raw==copy and bytes(expected)==new,'only recipe magic/phase change at seam')
 return dict(maximum_half_ticks=maximum,parent_path=parent.relative_to(ROOT).as_posix(),parent_sha256=sha(parent),source_copy_sha256=sha(directory/'incoming-original.ckp'),converted_sha256=__import__('hashlib').sha256(new).hexdigest(),preserved_state_bits=458,preserved_next_full_ticks=4096,source_event_applied=False)

def flux_audit(p):
 maximum=p['maximum_half_ticks'];directory=ROOT/f'references-local/release-voice01/{maximum}';raw=(directory/'flux.bin').read_bytes();dtype=np.dtype([('tick','<u8'),('x','<f8',(7,))]);require(raw[:8]==b'RFRELFX1' and (len(raw)-8)%64==0,'flux stream');rows=np.frombuffer(raw[8:],dtype=dtype);require(len(rows)==p['fine_steps']+1 and rows[0]['tick']==START and rows[-1]['tick']==START+BOUNDARIES[-1] and np.all(np.diff(rows['tick'])>0) and np.isfinite(rows['x']).all(),'complete finite flux clock')
 dc=(rows['x'][:,2]+rows['x'][:,3]-rows['x'][:,4])/1e-5;errors=abs(rows['x'][:,1]-dc);require(np.max(errors)<=2e-6,'C2 derivative current balance')
 times=[START];native_c2=[p['grids'][0]['values'][205]+p['grids'][0]['values'][434]];selected={};lines=(directory/'selected.txt').read_text(encoding='utf8').splitlines();i=2
 while i<len(lines):
  if lines[i].startswith('SELECT,'):
   pairs=[[state(line)[0] for line in lines[i+1+6*k+1:i+1+6*k+6]] for k in range(3)]
   # Root triples occupy nineteen lines; OBS endpoints follow the triple.
   obs=[];j=i+19
   while len(obs)<2:
    require(j<len(lines) and lines[j].startswith(('OBS,','RESET,')),'selected fine endpoint layout')
    if lines[j].startswith('OBS,'):obs.append(lines[j].split(','))
    j+=1
   for o,x in zip(obs,[pairs[1][-1],pairs[2][-1]]):selected[int(o[1])]=x
  if lines[i].startswith('OBS,'):
   v=list(map(float,lines[i].split(',')[1:]));times.append(int(v[0]));native_c2.append(v[2])
  i+=1
 require(np.array_equal(rows['tick'],np.array(times,dtype='<u8')) and np.array_equal(rows['x'][:,0].view('<u8'),np.array(native_c2).view('<u8')),'OBS/flux clocks and C2 by bits')
 selected[START]=lift(p['grids'][0]['values']);independent=[]
 for tick,x in sorted(selected.items()):
  r=rows[np.searchsorted(rows['tick'],tick)]['x'];expect=[(x[208]-x[205])/D(10000),(x[211]-x[205])/D(100000),(x[205]-x[200])/D(10000)]
  currents_error=[float(abs(D(actual)-value)) for actual,value in zip(r[2:5],expect)];require(max(currents_error)<=1e-14 and abs(D(r[5])-(x[226]-x[228]))<=D(2e-14) and abs(D(r[6])-x[218])<=D(2e-14),'selected component currents/collector voltages')
  slope=(expect[0]+expect[1]-expect[2])/D(1e-5);error=float(abs(D(r[1])-slope));require(error<=2e-6,'independent C2 current derivative');independent.append(dict(ticks=tick,current_errors_a=currents_error,derivative_error_v_per_s=error,attack_into_c2_a=float(expect[0]),decay_into_c2_a=float(expect[1]),follower_from_c2_a=float(expect[2])))
 detected=[]
 for k in range(1,len(rows)):
  a,b=rows[k-1],rows[k];xa,xb=a['x'],b['x']
  for name,index,condition in [('TURN',1,xa[1]>0 and xb[1]<=0),('LATCH',5,(xa[5]<0 and xb[5]>=0) or (xa[5]>=0 and xb[5]<0))]:
   if condition:
    detected.append((name,int(a['tick']),int(b['tick']),float(xa[index]),float(xb[index]),float(xa[0]),float(xb[0])))
 records=[(r[0],int(r[1]),int(r[2]),*map(float,r[3:])) for r in [line.split(',') for line in (directory/'transitions.txt').read_text(encoding='utf8').splitlines()]]
 require(records==detected,'all transition observations match flux records')
 events=[]
 for name,a,b,va,vb,ca,cb in records:
  alpha=-D(va)/(D(vb)-D(va));clock=D(a)+alpha*D(b-a);events.append(dict(kind=name,bracket_ticks=[a,b],bracket_width_s=float(D(b-a)*D(TICK)),bracket_quantity=[va,vb],interpolated_time_s=str(clock*D(TICK)),interpolated_c2_v=float(D(ca)+alpha*(D(cb)-D(ca))),direction='falling' if vb<va else 'rising'))
 peak_index=int(np.argmax(rows['x'][:,0]));return dict(maximum_half_ticks=maximum,records=len(rows),selected_independent_endpoints=len(independent),independent_components=independent,max_derivative_balance_error_v_per_s=float(np.max(errors)),events=events,
  turn_observed=any(e['kind']=='TURN' for e in events),latch_observed=any(e['kind']=='LATCH' for e in events),sampled_c2_max_v=float(rows['x'][peak_index,0]),sampled_c2_max_ticks=int(rows['tick'][peak_index]),final_c2_v=float(rows[-1]['x'][0]),final_slope_v_per_s=float(rows[-1]['x'][1]))

def audit():
 native=json.loads((ROOT/'evidence/voice_release_native01.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_release_inputs01.json').read_text(encoding='utf8'));parent=json.loads((ROOT/'evidence/voice_sustained_reference01.json').read_text(encoding='utf8'));require(native['passed'] and parent['passed'],'continuation and parent')
 profiles=[profile(p,inp) for p in native['profiles']];a,b=profiles;compares=[]
 require(len(a['grids'])==len(b['grids'])==28 and len(a['resets'])==len(b['resets']),'common clock/reset counts')
 for x,y in zip(a['grids'],b['grids']):
  require(x['ticks']==y['ticks'],'same clocks');u,v=lift(x['values']),lift(y['values']);ratio=lte(u,v);require(ratio<=1,'229 continuation refinement');compares.append(dict(ticks=x['ticks'],gate_ratio=ratio,max_voltage_error_v=max(float(abs(u[k]-v[k])) for k in range(229) if not 98<=k<133)))
 for x,y in zip(a['resets'],b['resets']):require(abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']))<=D(1e-8),'oscillator reset refinement')
 seams=[seam(p) for p in profiles];flux=[flux_audit(p) for p in profiles];event_refinement=[];require(len(flux[0]['events'])==len(flux[1]['events']),'transition counts')
 for x,y in zip(flux[0]['events'],flux[1]['events']):
  require(x['kind']==y['kind'] and x['direction']==y['direction'],'matching transition kinds/directions');delta=abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']));require(delta<=D(1e-7),'transition time refinement');event_refinement.append(dict(kind=x['kind'],difference_s=str(delta)))
 joined=[]
 for p in profiles:
  before=next(q for q in parent['profiles'] if q['maximum_half_ticks']==p['maximum_half_ticks']);old_integrals=[sum(D(phase['native_integrals_c'][k]) for phase in before['phases']) for k in range(9)];new_integrals=[D(p['phases'][0]['native_integrals_c'][k]) for k in range(9)];duration=START+BOUNDARIES[-1]-before['grids'][0]['ticks'];balance=ledger(lift(before['grids'][0]['values']),lift(p['grids'][-1]['values']),[float(x+y) for x,y in zip(old_integrals,new_integrals)],duration);joined.append(dict(maximum_half_ticks=p['maximum_half_ticks'],duration_s=duration*TICK,ledger=balance))
 return dict(profiles=profiles,seams=seams,same_clock_refinement=compares,flux_checks=flux,transition_refinement=event_refinement,joined_ledgers=joined,
  release_continuation_admitted=True,continued_duration_s=.008,joined_duration_s=.020004,release_since_source_off_s=.012,
  independent_candidates=6*sum(p['selected_accepted_count'] for p in profiles),independent_nonlinear_rows=1374*sum(p['selected_accepted_count'] for p in profiles),accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_steps=sum(p['fine_steps'] for p in profiles),
  restores=sum(p['restores'] for p in profiles),replayed_accepted_steps=sum(p['replayed_accepted_steps'] for p in profiles),maximum_active_replay_probes=max(p['maximum_active_replay_probes'] for p in profiles),rejected_corruptions=8,atomic_rollbacks=2,
  new_source_event=False,turn_observed=all(f['turn_observed'] for f in flux),latch_observed=all(f['latch_observed'] for f in flux),steady_periodicity_admitted=False,full_contour_from_silence_admitted=False,physical_fidelity=False,real_time=False)

def main():
 names={'tools/check_release_voice.py','tools/release_audit_body.py','tools/prepare_release_auditor.py','tools/prepare_release_voice.py','evidence/voice_release_native01.json','evidence/voice_release_inputs01.json','evidence/voice_sustained_reference01.json','docs/VOZ_LIBERACION_PROTOCOLO.md'}
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
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
 r.update(source_sha256_after={n:sha(ROOT/n) for n in sorted(names)},wall_s=time.perf_counter()-started);require(before==r['source_sha256_after'],'stable auditor');write('evidence/voice_release_reference01.json',r);print('RELEASE_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True);require(r['passed'],'continuation graph/flux/refinement')
if __name__=='__main__':main()
