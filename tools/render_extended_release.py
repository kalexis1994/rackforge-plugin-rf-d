"""Append a genuine unchanged release trajectory to the admitted 36 ms trace."""
import base64,json,struct,time,traceback
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_extended_release import START,SPAN,DECAY
from joint_cycles_analysis import require,TICK
from render_decay_control import joined_trace as controlled_trace
from render_release_voice import BASE_START
from render_conditioned_recipe import adapt,filtered,save,RATE
CODEC=struct.Struct('<8sQ6IdQd458d')
def inputs(held,release,controlled,extended):
 return [held,release,controlled,controlled.with_name('control-event.txt'),extended,extended.with_name('incoming-original.ckp'),extended.with_name('final.ckp')]
def joined_trace(held,release,controlled,extended):
 t,v=controlled_trace(held,release,controlled);a=controlled.read_text(encoding='utf8').splitlines();b=extended.read_text(encoding='utf8').splitlines();require(a[0]==b[0],'extended resolution profile');old=list(map(float,a[-1].split(',')[1:]));new=list(map(float,b[1].split(',')[1:]));require(b[1].startswith('JOINT_STATE,') and len(old)==len(new)==458 and struct.pack('<458d',*old)==struct.pack('<458d',*new),'full extended seam state')
 boundaries=[line.split(',') for line in b if line.startswith('BOUNDARY,')];require(len(boundaries)==1 and boundaries[0][1:]==['0',str(START),'0.00000000000000000e0','0'],'unchanged source voltages');rows=[list(map(float,line.split(',')[1:])) for line in b if line.startswith('OBS,')];require(rows and all(len(r)==24 for r in rows),'complete extended observations');ticks=np.array([int(r[0]) for r in rows],dtype='<u8');x=np.array([r[4] for r in rows]);require(ticks[0]>START and ticks[-1]==START+SPAN and np.all(np.diff(ticks)>0) and np.isfinite(np.array(rows)).all() and b[-2].startswith('TOTAL,') and b[-1].startswith('JOINT_STATE,'),'complete extended trace')
 maximum=int(b[0].split(',')[2]);tail=list(map(float,b[-1].split(',')[1:]));require(len(tail)==458,'final full state');states=[]
 for name,tick,state in [('incoming-original.ckp',START,new),('final.ckp',START+SPAN,tail)]:
  raw=extended.with_name(name).read_bytes();require(len(raw)==3728,'extended codec size');q=CODEC.unpack(raw);require(q[:2]==(b'RFDCY001',tick) and q[2]==maximum and q[3]==20 and 8<=q[4]<=2*maximum and q[4]&(q[4]-1)==0 and q[5:11]==(0,1,1,0.,0,DECAY) and raw[64:]==struct.pack('<458d',*state),'unchanged checkpoint recipe and full state');states.append(raw)
 require(t[-1]==(START-BASE_START)*TICK and v[-1].tobytes()==np.float64(new[194]+new[423]).tobytes() and np.float64(x[-1]).tobytes()==np.float64(tail[194]+tail[423]).tobytes(),'shared seam/final J7 bits');joined=np.r_[t,(ticks-BASE_START).astype(float)*TICK];require(np.all(np.diff(joined)>0),'unique trajectory endpoints');return joined,np.r_[v,x]
def derive():
 results=[];values=[]
 for maximum in [1048576,524288]:
  t,v=joined_trace(ROOT/f'references-local/sustained-voice01/{maximum}/selected.txt',ROOT/f'references-local/release-voice01/{maximum}/selected.txt',ROOT/f'references-local/decay-voice02/{maximum}/selected.txt',ROOT/f'references-local/extended-release01/{maximum}/selected.txt');pcm,meta=adapt(t,v,1);require(meta['frames']==3264,'68 ms WAV');results.append((maximum,pcm,meta));values.append(filtered(t,v,(np.arange(3264)+.5)/RATE,16))
 error=float(np.max(abs(values[0]-values[1])));pcm_error=int(np.max(abs(results[0][1].astype(int)-results[1][1].astype(int))));require(error<=2e-6 and pcm_error<=7,'extended native audio refinement');return results,error,pcm_error
def main():
 out='evidence/voice_extended_listening01.json';folder=ROOT/'artifacts/extended-release01';require(not folder.exists() and not (ROOT/out).exists(),'exclusive extended audio');ref='evidence/voice_extended_reference01.json';require(json.loads((ROOT/ref).read_text(encoding='utf8'))['passed'],'independent graph before listening');names=[ref,'tools/render_extended_release.py','tools/render_decay_control.py','tools/render_release_voice.py','tools/render_sustained_voice.py','tools/render_conditioned_recipe.py','tools/prepare_extended_release.py','docs/VOZ_LIBERACION_EXTENDIDA_PROTOCOLO.md'];sources={n:sha(ROOT/n) for n in names};paths=[]
 for maximum in [1048576,524288]:paths+=inputs(ROOT/f'references-local/sustained-voice01/{maximum}/selected.txt',ROOT/f'references-local/release-voice01/{maximum}/selected.txt',ROOT/f'references-local/decay-voice02/{maximum}/selected.txt',ROOT/f'references-local/extended-release01/{maximum}/selected.txt')
 private={p.relative_to(ROOT).as_posix():sha(p) for p in paths};started=time.perf_counter();r=dict(passed=False,source_sha256=sources,private_used_sha256=private,files=[],joined_simulated_window_s=.068004,new_circuit_duration_s=.032,decay_ohm=DECAY,new_source_event=False,sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,repeated=False,dc_removed=False,peak_normalization=False,fades=False,constant_extension_only_in_filter=True,steady_periodicity_admitted=False,real_time=False,physical_fidelity=False)
 try:
  a,error,pcm_error=derive();b,e2,p2=derive();require(error==e2 and pcm_error==p2 and all(x[0]==y[0] and np.array_equal(x[1],y[1]) and x[2]==y[2] for x,y in zip(a,b)),'entire extended audio replay');folder.mkdir(parents=True)
  for maximum,pcm,meta in a:
   path=folder/f'rf-d-j7-release-68ms-{maximum}-nativo.wav';save(path,pcm);r['files'].append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,maximum_half_ticks=maximum,**meta))
  r.update(passed=True,identical_derived_replay=True,native_resolution_max_error_v=error,native_resolution_max_pcm_lsb=pcm_error)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith('.py')}
  try:derive();r['replay']='unexpected pass or publication failure'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-started);require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable extended audio inputs');write(out,r);print('EXTENDED_LISTENING',r['passed'],r.get('failure',''),flush=True);require(r['passed'],'extended listening')
if __name__=='__main__':main()
