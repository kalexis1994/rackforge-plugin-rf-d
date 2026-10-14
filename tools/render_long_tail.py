"""Join the admitted 68 ms trajectory with actual assembly-family continuation."""
import base64,json,struct,time,traceback
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_long_tail import START,SPAN,DECAY
from joint_cycles_analysis import require,TICK
from render_extended_release import joined_trace as previous_trace,inputs as previous_inputs
from render_release_voice import BASE_START
from render_conditioned_recipe import adapt,filtered,save,RATE
CODEC=struct.Struct('<8sQ6IdQd458d')
def inputs(held,release,controlled,extended,tail):return [*previous_inputs(held,release,controlled,extended),tail,tail.with_name('incoming-original.ckp'),tail.with_name('final.ckp')]
def joined_trace(held,release,controlled,extended,tail):
 t,v=previous_trace(held,release,controlled,extended);a=extended.read_text(encoding='utf8').splitlines();b=tail.read_text(encoding='utf8').splitlines();require(a[0]==b[0],'tail resolution profile');old=list(map(float,a[-1].split(',')[1:]));new=list(map(float,b[1].split(',')[1:]));require(b[1].startswith('JOINT_STATE,') and len(old)==len(new)==458 and struct.pack('<458d',*old)==struct.pack('<458d',*new),'full tail seam state');boundaries=[line.split(',') for line in b if line.startswith('BOUNDARY,')];require(len(boundaries)==1 and boundaries[0][1:]==['0',str(START),'0.00000000000000000e0','0'],'unchanged tail sources');rows=[list(map(float,line.split(',')[1:])) for line in b if line.startswith('OBS,')];require(rows and all(len(r)==24 for r in rows),'complete tail observations');ticks=np.array([int(r[0]) for r in rows],dtype='<u8');x=np.array([r[4] for r in rows]);require(ticks[0]>START and ticks[-1]==START+SPAN and np.all(np.diff(ticks)>0) and np.isfinite(np.array(rows)).all() and b[-2].startswith('TOTAL,') and b[-1].startswith('JOINT_STATE,'),'complete tail trace');maximum=int(b[0].split(',')[2]);last=list(map(float,b[-1].split(',')[1:]));require(len(last)==458,'full tail final state')
 for name,tick,state in [('incoming-original.ckp',START,new),('final.ckp',START+SPAN,last)]:
  raw=tail.with_name(name).read_bytes();require(len(raw)==3728,'tail codec size');q=CODEC.unpack(raw);require(q[:2]==(b'RFDCY001',tick) and q[2]==maximum and q[3]==20 and 8<=q[4]<=2*maximum and q[4]&(q[4]-1)==0 and q[5:11]==(0,1,1,0.,0,DECAY) and raw[64:]==struct.pack('<458d',*state),'tail checkpoint recipe and state')
 require(t[-1]==(START-BASE_START)*TICK and v[-1].tobytes()==np.float64(new[194]+new[423]).tobytes() and np.float64(x[-1]).tobytes()==np.float64(last[194]+last[423]).tobytes(),'tail shared endpoint and final J7');clock=np.r_[t,(ticks-BASE_START).astype(float)*TICK];require(np.all(np.diff(clock)>0),'unique real endpoints');return clock,np.r_[v,x]
def derive():
 results=[];values=[]
 for maximum in [1048576,524288]:
  traces=[ROOT/f'references-local/{kind}/{maximum}/selected.txt' for kind in ['sustained-voice01','release-voice01','decay-voice02','extended-release01','long-tail01']];t,v=joined_trace(*traces);pcm,meta=adapt(t,v,1);require(meta['frames']==6336,'132 ms WAV');results.append((maximum,pcm,meta));values.append(filtered(t,v,(np.arange(6336)+.5)/RATE,16))
 error=float(np.max(abs(values[0]-values[1])));pcm_error=int(np.max(abs(results[0][1].astype(int)-results[1][1].astype(int))));require(error<=2e-6 and pcm_error<=7,'whole audio refinement');return results,error,pcm_error
def main():
 out='evidence/voice_tail_listening01.json';folder=ROOT/'artifacts/long-tail01';require(not folder.exists() and not (ROOT/out).exists(),'exclusive tail audio');ref='evidence/voice_tail_reference01.json';require(json.loads((ROOT/ref).read_text(encoding='utf8'))['passed'],'original graph before audio');names=[ref,'tools/render_long_tail.py','tools/render_extended_release.py','tools/render_decay_control.py','tools/render_release_voice.py','tools/render_sustained_voice.py','tools/render_conditioned_recipe.py','tools/prepare_long_tail.py','docs/VOZ_COLA_LARGA_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names};paths=[]
 for maximum in [1048576,524288]:paths+=inputs(*[ROOT/f'references-local/{kind}/{maximum}/selected.txt' for kind in ['sustained-voice01','release-voice01','decay-voice02','extended-release01','long-tail01']])
 private={p.relative_to(ROOT).as_posix():sha(p) for p in paths};start=time.perf_counter();r=dict(passed=False,source_sha256=before,private_used_sha256=private,files=[],joined_simulated_window_s=.132004,new_circuit_duration_s=.064,decay_ohm=DECAY,new_source_event=False,sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,repeated=False,dc_removed=False,peak_normalization=False,fades=False,constant_extension_only_in_filter=True,steady_periodicity_admitted=False,real_time=False,physical_fidelity=False)
 try:
  a,error,pcm_error=derive();b,e2,p2=derive();require(error==e2 and pcm_error==p2 and all(x[0]==y[0] and np.array_equal(x[1],y[1]) and x[2]==y[2] for x,y in zip(a,b)),'entire audio replay');folder.mkdir(parents=True)
  for maximum,pcm,meta in a:
   path=folder/f'rf-d-j7-tail-132ms-{maximum}-nativo.wav';save(path,pcm);r['files'].append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,maximum_half_ticks=maximum,**meta))
  r.update(passed=True,identical_derived_replay=True,native_resolution_max_error_v=error,native_resolution_max_pcm_lsb=pcm_error)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith('.py')}
  try:derive();r['replay']='unexpected pass or publication failure'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start);require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable audio inputs');write(out,r);print('TAIL_LISTENING',r['passed'],r.get('failure',''),flush=True);require(r['passed'],'whole tail listening')
if __name__=='__main__':main()
