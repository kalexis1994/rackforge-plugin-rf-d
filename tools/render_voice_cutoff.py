"""Join seven actual traces, preserving complete cutoff events and native level."""
import base64,json,struct,sys,time,traceback
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_voice_cutoff import START,SPAN,BOUNDARIES,KEY,SHORT,DECAY,ALPHA
from joint_cycles_analysis import require,TICK
from render_voice_retrigger import joined_trace as previous_trace,inputs as previous_inputs
CODEC=struct.Struct('<8sQ6IdQ2d458d')
from render_release_voice import BASE_START
from render_conditioned_recipe import adapt,filtered,save,RATE
KINDS=['sustained-voice01','release-voice01','decay-voice02','extended-release01','long-tail01','voice-retrigger01','voice-cutoff01']
def inputs(held,release,controlled,extended,tail,retrigger,cutoff):
 return [*previous_inputs(held,release,controlled,extended,tail,retrigger),cutoff,*[cutoff.with_name(n) for n in ['incoming-original.ckp','final.ckp','event1-before.ckp','event1-after.ckp','event2-before.ckp','event2-after.ckp']]]
def recipe(raw,tick,phase,state):
 require(len(raw)==3736,'cutoff codec size');q=CODEC.unpack(raw);maximum=q[2]
 require(q[:2]==(b'RFCTF001',tick) and maximum in [1048576,524288] and q[3]==20 and 8<=q[4]<=2*maximum and q[4]&(q[4]-1)==0 and q[5:12]==(phase,1,1+2*int(SHORT[phase]),KEY[phase],0,DECAY,ALPHA[phase]) and raw[72:]==struct.pack('<458d',*state),'cutoff checkpoint recipe and complete state')
 return q
def joined_trace(held,release,controlled,extended,tail,retrigger,cutoff):
 t,v=previous_trace(held,release,controlled,extended,tail,retrigger);a=retrigger.read_text(encoding='utf8').splitlines();b=cutoff.read_text(encoding='utf8').splitlines();require(a[0]==b[0],'cutoff resolution profile');old=list(map(float,a[-1].split(',')[1:]));new=list(map(float,b[1].split(',')[1:]));require(b[1].startswith('JOINT_STATE,') and len(old)==len(new)==458 and struct.pack('<458d',*old)==struct.pack('<458d',*new),'full cutoff seam state')
 rows=[list(map(float,line.split(',')[1:])) for line in b if line.startswith('OBS,')];require(rows and all(len(r)==24 for r in rows),'complete cutoff observations');ticks=np.array([int(r[0]) for r in rows],dtype='<u8');x=np.array([r[4] for r in rows]);require(ticks[0]>START and ticks[-1]==START+SPAN and np.all(np.diff(ticks)>0) and np.isfinite(np.array(rows)).all() and b[-2].startswith('TOTAL,') and b[-1].startswith('JOINT_STATE,'),'complete cutoff trace')
 boundary_indices=[i for i,line in enumerate(b) if line.startswith('BOUNDARY,')];require(len(boundary_indices)==3,'all cutoff boundaries');last=list(map(float,b[-1].split(',')[1:]));maximum=int(b[0].split(',')[2]);require(len(last)==458,'full cutoff final state')
 for phase,i in enumerate(boundary_indices):
  fields=b[i].split(',');require(fields[1:3]==[str(phase),str(START+BOUNDARIES[phase])] and float(fields[3])==KEY[phase] and int(fields[4])==SHORT[phase],'exact cutoff source clock')
  state=list(map(float,b[i+1].split(',')[1:]));require(len(state)==458 and np.isfinite(state).all(),'complete event state')
  if phase==0:require(struct.pack('<458d',*state)==struct.pack('<458d',*new),'initial boundary state')
  else:
   before=cutoff.with_name(f'event{phase}-before.ckp').read_bytes();after=cutoff.with_name(f'event{phase}-after.ckp').read_bytes();u=recipe(before,START+BOUNDARIES[phase],phase-1,state);q=recipe(after,START+BOUNDARIES[phase],phase,state);require(u[2]==q[2]==maximum and before[8:28]==after[8:28] and before[56:64]==after[56:64] and before[72:]==after[72:] and before[32:56]==after[32:56],'event preserves clock proposal resistance and charge')
   require(b[i-2].startswith('LEDGER,') and b[i-1].startswith('JOINT_STATE,') and struct.pack('<458d',*map(float,b[i-1].split(',')[1:]))==after[72:],'preceding phase state at event')
 original=cutoff.with_name('incoming-original.ckp').read_bytes();require(len(original)==3728 and original[:8]==b'RFDCY001' and original[28:32]==struct.pack('<I',2),'own previous cutoff codec');converted=bytearray(original[:64]+struct.pack('<d',1.)+original[64:]);converted[:8]=b'RFCTF001';converted[28:32]=struct.pack('<I',0);recipe(converted,START,0,new);recipe(cutoff.with_name('final.ckp').read_bytes(),START+SPAN,2,last)
 require(t[-1]==(START-BASE_START)*TICK and v[-1].tobytes()==np.float64(new[194]+new[423]).tobytes() and np.float64(x[-1]).tobytes()==np.float64(last[194]+last[423]).tobytes(),'cutoff shared endpoint and final J7');clock=np.r_[t,(ticks-BASE_START).astype(float)*TICK];require(np.all(np.diff(clock)>0),'unique real endpoints');return clock,np.r_[v,x]
def derive():
 results=[];values=[]
 for m in [1048576,524288]:
  t,v=joined_trace(*[ROOT/f'references-local/{kind}/{m}/selected.txt' for kind in KINDS]);pcm,meta=adapt(t,v,1);require(meta['frames']==7872,'164 ms WAV');results.append((m,pcm,meta));values.append(filtered(t,v,(np.arange(7872)+.5)/RATE,16))
 error=float(np.max(abs(values[0]-values[1])));pcm_error=int(np.max(abs(results[0][1].astype(int)-results[1][1].astype(int))));require(error<=2e-6 and pcm_error<=7,'whole cutoff audio refinement');return results,error,pcm_error
def code_hashes():
 names=set()
 for module in list(sys.modules.values()):
  f=getattr(module,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 return {n:sha(ROOT/n) for n in sorted(names)}
def main():
 out='evidence/voice_cutoff_listening01.json';folder=ROOT/'artifacts/voice-cutoff01';require(not folder.exists() and not (ROOT/out).exists(),'exclusive cutoff audio');ref='evidence/voice_cutoff_reference01.json';require(json.loads((ROOT/ref).read_text(encoding='utf8'))['passed'],'original graph before audio');before={**code_hashes(),ref:sha(ROOT/ref),'docs/VOZ_CUTOFF_PROTOCOLO.md':sha(ROOT/'docs/VOZ_CUTOFF_PROTOCOLO.md')};paths=[]
 for m in [1048576,524288]:paths+=inputs(*[ROOT/f'references-local/{kind}/{m}/selected.txt' for kind in KINDS])
 private={p.relative_to(ROOT).as_posix():sha(p) for p in paths};start=time.perf_counter();r=dict(passed=False,source_sha256=before,private_used_sha256=private,files=[],joined_simulated_window_s=.164012,new_circuit_duration_s=.016004,decay_ohm=DECAY,new_source_event=True,source_events=[dict(ticks=START+BOUNDARIES[i],keyboard_v=KEY[i],short=SHORT[i],cutoff_fraction=ALPHA[i],previous_cutoff_fraction=ALPHA[i-1]) for i in [1,2]],sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,repeated=False,dc_removed=False,peak_normalization=False,fades=False,constant_extension_only_in_filter=True,steady_periodicity_admitted=False,real_time=False,physical_fidelity=False)
 try:
  a,error,pcm_error=derive();b,e2,p2=derive();require(error==e2 and pcm_error==p2 and all(x[0]==y[0] and np.array_equal(x[1],y[1]) and x[2]==y[2] for x,y in zip(a,b)),'entire audio replay');folder.mkdir(parents=True)
  for m,pcm,meta in a:
   path=folder/f'rf-d-j7-cutoff-164ms-{m}-nativo.wav';save(path,pcm);r['files'].append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,maximum_half_ticks=m,**meta))
  r.update(passed=True,identical_derived_replay=True,native_resolution_max_error_v=error,native_resolution_max_pcm_lsb=pcm_error)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in before if n.endswith('.py')}
  try:derive();r['replay']='unexpected pass or publication failure'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in before},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start);require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable cutoff audio inputs');write(out,r);print('CUTOFF_LISTENING',r['passed'],r.get('failure',''));require(r['passed'],'whole cutoff listening')
if __name__=='__main__':main()
