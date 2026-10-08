"""First native VCO listening: repeat one admitted circuit cycle, scoped adapter."""
import json,math,wave
import numpy as np
from vco1_radau_cycles_resume import ROOT,sha,TICK
from vco1_radau_joined_trace import blocks
from render_vco1_circuit import coefficients,synthesize,save
OUT='evidence/voice_vco1_radau_listening01.json'

def signals(profile):
    arrays=[]
    entries=[dict(path=ROOT/e['path'],skip_rows=e['skip_rows'],take_rows=e['take_rows']) for e in profile['segments']]
    for block in blocks(entries):arrays.append(np.column_stack([block[:,0]*TICK,*[block[:,6+i]+block[:,140+i] for i in (46,54,44)]]))
    raw=np.concatenate(arrays);a,b=profile['measurements']['reset_crossings_s'][-2:];t=raw[:,0]
    knots=np.r_[a,t[(t>a)&(t<b)],b];phase=(knots-a)/(b-a);phase[0]=0;phase[-1]=1
    return phase,np.column_stack([np.interp(knots,t,raw[:,i]) for i in (1,2,3)]),(a,b)

def main():
    out=ROOT/OUT;folder=ROOT/'artifacts/vco1-radau-native01'
    if out.exists() or folder.exists():raise ValueError('preserve listening attempt')
    names=['tools/render_vco1_radau.py','docs/VCO1_RADAU_ESCUCHA_PROTOCOLO.md','tools/render_vco1_circuit.py','evidence/voice_vco1_radau_cycles04.json','evidence/voice_vco1_radau_conformance01.json']
    before={n:sha(ROOT/n) for n in names};bank=json.loads((ROOT/names[-2]).read_text());external=json.loads((ROOT/names[-1]).read_text())
    if not bank['passed'] or not external['passed']:raise ValueError('admitted native and method banks required')
    profile=bank['profiles'][1]
    if profile['maximum_accepted_half_ticks']!=65536:raise ValueError('finest nominal profile')
    phase,voltage,window=signals(profile);frequency=1/(window[1]-window[0]);rate=48000;harmonics=int(math.floor(.45*rate/frequency));folder.mkdir(parents=True)
    r=dict(schema='rf-d/native-vco-periodic-listening/v1',passed=False,source_sha256=before,source_segments=profile['segments'],source_logical_sha256=profile['coverage']['uncompressed_sha256'],simulated_circuit_s=.03,window_s=list(window),knots=len(phase),frequency_hz=frequency,sample_rate_hz=rate,harmonics=harmonics,highest_harmonic_hz=harmonics*frequency,duration_per_wave_s=.75,volts_per_full_scale=8.,fade_s=.01,files={},removed_dc_v={},coefficients={},new_native_trajectories=0,new_spice_processes=0,periodic_cycle_repeated=True,full_duration_circuit_render=False,full_voice=False,physical_fidelity=False,real_time=False)
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');parts=[]
    for i,name in enumerate(('sierra','triangulo','pulso')):
        c=coefficients(phase,voltage[:,i],harmonics);audio=synthesize(c,frequency,rate);path=folder/f'rf-d-vco1-nativo-{name}.wav';save(path,audio,rate);parts.append(audio)
        r['removed_dc_v'][name]=float(c[0].real);r['coefficients'][name]=[[float(v.real),float(v.imag)] for v in c]
        with wave.open(str(path),'rb') as w:
            payload=w.readframes(w.getnframes());r['files'][name]=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,frames=w.getnframes(),peak=float(np.max(np.abs(audio))),rms=float(np.sqrt(np.mean(audio**2))),pcm_roundtrip_exact=payload==np.rint(audio*32767).astype('<i2').tobytes())
    montage=np.concatenate([parts[0],np.zeros(int(.15*rate)),parts[1],np.zeros(int(.15*rate)),parts[2]]);path=folder/'rf-d-vco1-nativo-sierra-triangulo-pulso.wav';save(path,montage,rate)
    r['files']['montaje']=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,frames=len(montage),duration_s=len(montage)/rate)
    r['source_sha256_after']={n:sha(ROOT/n) for n in names};r['passed']=before==r['source_sha256_after'] and all(r['files'][n]['pcm_roundtrip_exact'] for n in ('sierra','triangulo','pulso'))
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('Native VCO listening',r['passed'],frequency,'Hz',path,flush=True)

if __name__=='__main__':main()
