"""24-ms electrical burst, fixed monitor gain and explicit limited-band adapter."""
import json,math,struct,wave
from prepare_dual_chain import ROOT,sha,write
def main():
    native='evidence/voice_sparse_native01.json';reference='evidence/voice_sparse_reference01.json';prefix='evidence/voice_cost_prefix01.json'
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed']
    for n in [reference,prefix]:assert json.loads((ROOT/n).read_text(encoding='utf8'))['passed']
    path=ROOT/r['output_directory']/'profile-524288.stdout';input=[]
    for line in path.read_text(encoding='utf8').splitlines():
        tag,*tokens=line.split(',');x=list(map(float,tokens))
        if tag=='DC':s=x[4:];input.append(s[248]+s[498])
        if tag=='GRID':input.append(x[1+248]+x[1+498])
    assert len(input)==193
    frames=[];gain=4.;output_rate=48000;cutoff=2800/8000
    for i in range(1152):
        position=i/6.;center=math.floor(position);value=0.;weight_sum=0.
        for k in range(center-31,center+33):
            distance=position-k
            if abs(distance)>=32:continue
            weight=(2*cutoff if distance==0 else math.sin(2*math.pi*cutoff*distance)/(math.pi*distance))*(.5+.5*math.cos(math.pi*distance/32))
            value+=weight*input[max(0,min(192,k))];weight_sum+=weight
        value=value/weight_sum*gain
        fade=min(1.,i/24.,(1151-i)/24.);frames.append(value*fade)
    peak=max(abs(v) for v in frames);assert peak<.98,'fixed monitor clipping'
    out=ROOT/'references-local/voice-cost-listening01';out.mkdir();wav=out/'voice24.wav'
    pcm=b''.join(struct.pack('<h',round(v*32767)) for v in frames)
    with wave.open(str(wav),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(output_rate);w.writeframes(pcm)
    with wave.open(str(wav),'rb') as w:assert w.getnframes()==1152 and w.getframerate()==48000 and w.readframes(1152)==pcm
    write(ROOT/'evidence/voice_cost_listening01.json',dict(schema='rf-d/voice-cost/listening-v1',passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/render_voice_cost.py',native,reference,prefix,'docs/VOZ_COSTO_TRAYECTORIA_PROTOCOLO.md']},trace_sha256=sha(path),private_sha256={wav.relative_to(ROOT).as_posix():sha(wav)},duration_s=.024,simulation_duration_s=.024,sample_rate=48000,frames=1152,channels=1,pcm_bits=16,source='J7 from new coupled VCO/dual-contour trajectory',source_grid_hz=8000,sinc_taps=64,hann_window=True,nominal_cutoff_hz=2800,monitor_samples_per_v=gain,peak_normalization=False,dc_removed=False,fade_s=.0005,repeated_cycles=False,concatenated=False,peak_sample=peak,rms_sample=math.sqrt(sum(v*v for v in frames)/len(frames)),physical_fidelity=False,real_time=False))
    print('VOICE_COST_LISTENING',wav,peak)
if __name__=='__main__':main()
