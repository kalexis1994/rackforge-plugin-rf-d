"""Join a verified release seam and adapt only the genuine 20.004 ms trajectory."""
import argparse,base64,json,platform,struct,time,traceback
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import START,SPAN
from joint_cycles_analysis import require,TICK
from render_sustained_voice import load_trace as parent_trace
from render_conditioned_recipe import adapt,filtered,save,RATE
BASE_START=4423942144

def joined_trace(parent,continuation):
 t,v=parent_trace(parent);before=parent.read_text(encoding='utf8').splitlines();after=continuation.read_text(encoding='utf8').splitlines();require(before[0]==after[0],'same ON resolution profile')
 old=list(map(float,before[-1].split(',')[1:]));new=list(map(float,after[1].split(',')[1:]));require(after[1].startswith('JOINT_STATE,') and len(old)==len(new)==458 and struct.pack('<458d',*old)==struct.pack('<458d',*new),'full inherited state at audio seam')
 boundaries=[line.split(',') for line in after if line.startswith('BOUNDARY,')];require(len(boundaries)==1 and boundaries[0][1:]==['0',str(START),'0.00000000000000000e0','0'],'inherited sources without a new event')
 rows=[list(map(float,line.split(',')[1:])) for line in after if line.startswith('OBS,')];require(rows and all(len(row)==24 for row in rows),'complete continuation observations')
 ticks=np.array([int(r[0]) for r in rows],dtype='<u8');x=np.array([r[4] for r in rows]);require(ticks[0]>START and ticks[-1]==START+SPAN and np.all(np.diff(ticks)>0) and np.isfinite(x).all() and after[-2].startswith('TOTAL,') and after[-1].startswith('JOINT_STATE,'),'complete continued clock/volts')
 require(t[-1]==(START-BASE_START)*TICK and v[-1].tobytes()==np.float64(new[194]+new[423]).tobytes(),'single shared J7 seam endpoint')
 result_t=np.r_[t,(ticks-BASE_START).astype(float)*TICK];result_v=np.r_[v,x];require(np.all(np.diff(result_t)>0),'no duplicate joined seam');return result_t,result_v

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt;out=f'evidence/voice_release_listening{attempt:02d}.json';folder=ROOT/f'artifacts/release-voice{attempt:02d}';require(not (ROOT/out).exists() and not folder.exists(),'exclusive joined listening')
 name='evidence/voice_release_reference01.json';ref=json.loads((ROOT/name).read_text(encoding='utf8'));require(ref['passed'] and ref['release_continuation_admitted'],'continuation graph before audio')
 names=[name,'tools/render_release_voice.py','tools/render_sustained_voice.py','tools/render_conditioned_recipe.py','tools/prepare_release_voice.py','docs/VOZ_LIBERACION_PROTOCOLO.md'];sources={n:sha(ROOT/n) for n in names}
 paths=[f'references-local/{kind}/{maximum}/selected.txt' for maximum in [1048576,524288] for kind in ['sustained-voice01','release-voice01']];private={n:sha(ROOT/n) for n in paths}
 r=dict(passed=False,source_sha256=sources,private_used_sha256=private,files=[],joined_simulated_window_s=.020004,new_continuation_window_s=.008,sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,
  repeated=False,dc_removed=False,peak_normalization=False,fades=False,constant_extension_only_in_filter=True,steady_periodicity_admitted=False,real_time=False,physical_fidelity=False,python_version=platform.python_version(),numpy_version=np.__version__)
 start=time.perf_counter()
 def derive():
  result=[];values=[]
  for maximum in [1048576,524288]:
   t,v=joined_trace(ROOT/f'references-local/sustained-voice01/{maximum}/selected.txt',ROOT/f'references-local/release-voice01/{maximum}/selected.txt');pcm,meta=adapt(t,v,1);require(meta['frames']==960,'20 ms native WAV')
   values.append(filtered(t,v,(np.arange(960)+.5)/RATE,16));result.append((maximum,pcm,meta))
  error=float(np.max(abs(values[0]-values[1])));pcm_error=int(np.max(abs(result[0][1].astype(int)-result[1][1].astype(int))));require(error<=2e-6 and pcm_error<=7,'joined native resolution gate');return result,error,pcm_error
 try:
  a,error,pcm_error=derive();b,error2,pcm_error2=derive();require(error==error2 and pcm_error==pcm_error2 and all(x[0]==y[0] and np.array_equal(x[1],y[1]) and x[2]==y[2] for x,y in zip(a,b)),'identical joined listening replay');folder.mkdir(parents=True)
  for maximum,pcm,meta in a:
   path=folder/f'rf-d-j7-gatillo-liberacion-{maximum}-nativo.wav';save(path,pcm);r['files'].append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,maximum_half_ticks=maximum,**meta))
  r.update(passed=True,identical_derived_replay=True,native_resolution_max_error_v=error,native_resolution_max_pcm_lsb=pcm_error)
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
  try:derive();r['unchanged_replay']='derivation passed; preserve publication failure'
  except Exception:r['unchanged_replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start);require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable joined audio inputs');write(out,r);print('RELEASE_LISTENING',r['passed'],r.get('failure',''));require(r['passed'],'joined listening')
if __name__=='__main__':main()
