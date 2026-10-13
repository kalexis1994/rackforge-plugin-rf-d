"""Join the genuine trajectory through an explicit electrical decay event."""
import base64,json,struct,time,traceback
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_decay_control import START,SPAN,DECAY
from joint_cycles_analysis import require,TICK
from render_release_voice import joined_trace as release_trace,BASE_START
from render_conditioned_recipe import adapt,filtered,save,RATE

def joined_trace(held,release,controlled):
 t,v=release_trace(held,release);a=release.read_text(encoding='utf8').splitlines();b=controlled.read_text(encoding='utf8').splitlines();require(a[0]==b[0],'controlled resolution profile');old=list(map(float,a[-1].split(',')[1:]));new=list(map(float,b[1].split(',')[1:]));require(b[1].startswith('JOINT_STATE,') and len(old)==len(new)==458 and struct.pack('<458d',*old)==struct.pack('<458d',*new),'full controlled seam state')
 event=controlled.with_name('control-event.txt');require(event.read_text(encoding='utf8')==f'DECAY_CONTROL,{START},100000,1000\n','declared electrical event');boundaries=[line.split(',') for line in b if line.startswith('BOUNDARY,')];require(len(boundaries)==1 and boundaries[0][1:]==['0',str(START),'0.00000000000000000e0','0'],'inherited source voltages')
 rows=[list(map(float,line.split(',')[1:])) for line in b if line.startswith('OBS,')];require(rows and all(len(r)==24 for r in rows),'complete controlled observations');ticks=np.array([int(r[0]) for r in rows],dtype='<u8');x=np.array([r[4] for r in rows]);require(ticks[0]>START and ticks[-1]==START+SPAN and np.all(np.diff(ticks)>0) and np.isfinite(x).all() and b[-2].startswith('TOTAL,') and b[-1].startswith('JOINT_STATE,'),'complete controlled trace')
 require(t[-1]==(START-BASE_START)*TICK and v[-1].tobytes()==np.float64(new[194]+new[423]).tobytes(),'one shared controlled endpoint');joined_t=np.r_[t,(ticks-BASE_START).astype(float)*TICK];require(np.all(np.diff(joined_t)>0),'two unique seams');return joined_t,np.r_[v,x]

def derive():
 results=[];values=[]
 for maximum in [1048576,524288]:
  t,v=joined_trace(ROOT/f'references-local/sustained-voice01/{maximum}/selected.txt',ROOT/f'references-local/release-voice01/{maximum}/selected.txt',ROOT/f'references-local/decay-voice02/{maximum}/selected.txt');pcm,meta=adapt(t,v,1);require(meta['frames']==1728,'36 ms WAV');results.append((maximum,pcm,meta));values.append(filtered(t,v,(np.arange(1728)+.5)/RATE,16))
 error=float(np.max(abs(values[0]-values[1])));pcm_error=int(np.max(abs(results[0][1].astype(int)-results[1][1].astype(int))));require(error<=2e-6 and pcm_error<=7,'controlled native audio refinement');return results,error,pcm_error

def main():
 out='evidence/voice_decay_listening01.json';folder=ROOT/'artifacts/decay-voice01';require(not folder.exists() and not (ROOT/out).exists(),'exclusive control listening');ref='evidence/voice_decay_reference02.json';require(json.loads((ROOT/ref).read_text(encoding='utf8'))['passed'],'independent graph before listening')
 names=[ref,'tools/render_decay_control.py','tools/render_release_voice.py','tools/render_sustained_voice.py','tools/render_conditioned_recipe.py','tools/prepare_decay_control.py','docs/DECAY_CONTROL_PROTOCOLO.md'];sources={n:sha(ROOT/n) for n in names};paths=[f'references-local/{kind}/{maximum}/{file}' for maximum in [1048576,524288] for kind,file in [('sustained-voice01','selected.txt'),('release-voice01','selected.txt'),('decay-voice02','selected.txt'),('decay-voice02','control-event.txt')]];private={n:sha(ROOT/n) for n in paths};start=time.perf_counter();r=dict(passed=False,source_sha256=sources,private_used_sha256=private,files=[],joined_simulated_window_s=.036004,new_circuit_duration_s=.016,decay_ohm=DECAY,control_event_ticks=START,sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,repeated=False,dc_removed=False,peak_normalization=False,fades=False,constant_extension_only_in_filter=True,steady_periodicity_admitted=False,real_time=False,physical_fidelity=False)
 try:
  a,error,pcm_error=derive();b,e2,p2=derive();require(error==e2 and pcm_error==p2 and all(x[0]==y[0] and np.array_equal(x[1],y[1]) and x[2]==y[2] for x,y in zip(a,b)),'entire derived replay');folder.mkdir(parents=True)
  for maximum,pcm,meta in a:
   path=folder/f'rf-d-j7-decay-1k-{maximum}-nativo.wav';save(path,pcm);r['files'].append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,maximum_half_ticks=maximum,**meta))
  r.update(passed=True,identical_derived_replay=True,native_resolution_max_error_v=error,native_resolution_max_pcm_lsb=pcm_error)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
  try:derive();r['replay']='unexpected pass or publication failure'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start);require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable listening inputs');write(out,r);print('DECAY_LISTENING',r['passed'],r.get('failure',''));require(r['passed'],'controlled listening')
if __name__=='__main__':main()
