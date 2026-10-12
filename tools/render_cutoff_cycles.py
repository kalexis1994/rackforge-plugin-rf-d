"""Conditional listening adapter; preserve volts, gain, source window and PCM."""
import json,time,traceback,wave
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require,trace,TICK
from render_vco1_circuit import coefficients,synthesize,save

def actual_signal(reference,maximum):
 p=next(p for p in reference['profiles'] if p['maximum_half_ticks']==maximum);prefix=ROOT/f'references-local/cutoff-temporal01/1.0-{maximum}/trace.bin';path=ROOT/f'references-local/cutoff-cycles01/{maximum}/trace.bin'
 for file in [prefix,path]:require(sha(file)==reference['input_sha256'][file.relative_to(ROOT).as_posix()],'admitted source trace')
 rows=np.concatenate([trace(prefix),trace(path,start_ticks=131072000)]);a,b=[float(e['interpolated_time_s']) for e in p['events']];t=rows['ticks'].astype(float)*TICK;knots=np.r_[a,t[(t>a)&(t<b)],b];phase=(knots-a)/(b-a);phase[0]=0.;phase[-1]=1.;return phase,np.interp(knots,t,rows['j7']),1/float(p['period_s']),[a,b]
def main():
 name='evidence/voice_cutoff_cycles_reference02.json';q=json.loads((ROOT/name).read_text(encoding='utf8'));out=ROOT/'evidence/voice_cutoff_cycles_listening01.json';folder=ROOT/'artifacts/cutoff-open-native01';require(q['passed'] and not out.exists() and not folder.exists(),'admitted/exclusive listening');names=[name,'tools/render_cutoff_cycles.py','tools/render_vco1_circuit.py','tools/joint_cycles_analysis.py','docs/VOZ_CUTOFF_CICLOS_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names};r=dict(schema='rf-d/open-cutoff-periodic-listening/v1',passed=False,source_sha256=before,listening_admitted=False,files=[],source_trace_sha256={},simulated_circuit_s=.00525,new_trajectories=0,new_initial_roots_applied=0,new_spice_processes=0,periodic_observed_interval_repeated=True,full_audio_duration_simulated=False,complete_voice=False,physical_fidelity=False,real_time=False);start=time.perf_counter()
 r['electrical_boundary']=dict(node='J7',cutoff_fraction=1.,range_fraction=.1,r61_ohm=200.,loudness_v=2.,q21_base_v=2.,r20_lower_ohm=2500.,r21_lower_ohm=2000.,hi_load_ohm=10000.,lo_load_ohm=100000.,tip_load_ohm=32.,ring_load_ohm=32.,osc1_panel_alpha=.5,other_mixer_sources_on=False)
 if not q['listening_candidate_admitted']:
  r['passed']=True;r['reason']='Prior seam/RMS gate rejects interval repetition; preserve numeric scene without WAV.'
 else:
  try:
   cs=[]
   for maximum in [65536,32768]:
    phase,v,frequency,window=actual_signal(q,maximum);c=coefficients(phase,v,q['listening_proposal']['harmonics']);expected=np.array([complex(*a) for a in q['listening_proposal']['coefficients'][0 if maximum==65536 else 1]]);require(np.array_equal(c.view('<u8'),expected.view('<u8')),'coefficients recomputed by bits');cs.append((maximum,c,frequency,window,len(phase)))
   maximum,c,frequency,window,knots=cs[-1];audio=synthesize(c,frequency,48000,duration=2.,volts_per_full_scale=.1);folder.mkdir(parents=True);path=folder/'rf-d-j7-cutoff-abierto-inspeccion.wav';save(path,audio,48000)
   with wave.open(str(path),'rb') as w:
    payload=w.readframes(w.getnframes());require(w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==48000 and w.getnframes()==96000 and payload==np.rint(audio*32767).astype('<i2').tobytes(),'full PCM16 byte roundtrip')
   require(np.any(np.frombuffer(payload,dtype='<i2')!=0),'nonzero PCM payload');r.update(passed=True,listening_admitted=True,source_maximum_half_ticks=maximum,window_s=window,knots=knots,frequency_hz=frequency,harmonics=len(c)-1,highest_harmonic_hz=(len(c)-1)*frequency,sample_rate_hz=48000,duration_s=2.,volts_per_full_scale=.1,gain_relative_to_8v_adapter=80.,removed_dc_v=float(c[0].real),fade_s=.01,peak=float(np.max(abs(audio))),rms=float(np.sqrt(np.mean(audio**2))),pcm_roundtrip_exact=True,files=[dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,frames=96000)])
   for maximum,_,_,_,_ in cs:
    for p in [f'references-local/cutoff-temporal01/1.0-{maximum}/trace.bin',f'references-local/cutoff-cycles01/{maximum}/trace.bin']:r['source_trace_sha256'][p]=sha(ROOT/p)
  except Exception:
   r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/render_cutoff_cycles.py').read_text(encoding='utf8')
   # Deterministic replay of the derivation; do not replace a partial WAV.
   try:
    phase,v,frequency,window=actual_signal(q,32768);c=coefficients(phase,v,q['listening_proposal']['harmonics']);synthesize(c,frequency,48000,duration=2.,volts_per_full_scale=.1);r['replay']='Derivation passed; preserve publication failure for exact artifact inspection.'
   except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==r['source_sha256_after'],'unchanged renderer inputs');r['wall_s']=time.perf_counter()-start;out.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CUTOFF_LISTENING',r['passed'],r['listening_admitted'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
