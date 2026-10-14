"""Render actual J7 histories; no cycle repetition, DC removal or peak fitting."""
import json,math,struct,wave
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from audit_observed_note import trace,absolute

def render(input):
    frames=[];last=len(input)-1
    for i in range(last*6):
        position=i/6.;center=math.floor(position);value=0.;total=0.
        for k in range(center-31,center+33):
            distance=position-k
            if abs(distance)>=32:continue
            cutoff=2800/8000
            weight=(2*cutoff if distance==0 else math.sin(2*math.pi*cutoff*distance)/(math.pi*distance))*(.5+.5*math.cos(math.pi*distance/32))
            value+=weight*input[max(0,min(last,k))];total+=weight
        fade=min(1.,i/24.,(last*6-1-i)/24.)
        frames.append(4.*value/total*fade)
    return frames

def main():
    native='evidence/observed_note_native01.json';audit='evidence/observed_note_audit01.json'
    r=json.loads((ROOT/native).read_text(encoding='utf8'));a=json.loads((ROOT/audit).read_text(encoding='utf8'))
    assert r['passed'] and a['passed'] and r['duration_us']==100000 and r['gate_end_us']==75000
    out=ROOT/'references-local/observed-note-listening01';out.mkdir();records=[];signals=[]
    for maximum in [16777216,8388608]:
        path=ROOT/r['output_directory']/f'profile-{maximum}.stdout'
        g,_,_=trace(path);assert len(g)==801
        frames=render([absolute(g[k][0])[248] for k in sorted(g)])
        assert len(frames)==4800 and max(abs(v) for v in frames)<.98
        pcm=b''.join(struct.pack('<h',round(v*32767)) for v in frames)
        wav=out/f'note100-{maximum}.wav'
        with wave.open(str(wav),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(pcm)
        with wave.open(str(wav),'rb') as w:
            assert w.getnframes()==4800 and w.getframerate()==48000 and w.readframes(4800)==pcm
        assert max(abs(v-struct.unpack_from('<h',pcm,2*i)[0]/32767) for i,v in enumerate(frames))<=.5/32767+1e-16
        records.append(dict(maximum_half_ticks=maximum,path=wav.relative_to(ROOT).as_posix(),sha256=sha(wav),frames=4800,peak=max(abs(v) for v in frames),rms=math.sqrt(sum(v*v for v in frames)/4800)))
        signals.append(np.array(frames))
    error=signals[0]-signals[1]
    rms=float(np.sqrt(np.mean(error*error))/np.sqrt(np.mean(signals[1]*signals[1])))
    peak=float(np.max(abs(error))/np.max(abs(signals[1])))
    dc=float(abs(np.mean(error))/4.)
    assert rms<=.005 and peak<=.015 and dc<=5e-6,(rms,peak,dc)
    write(ROOT/'evidence/observed_note_listening01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in [native,audit,'tools/render_observed_note.py','tools/audit_observed_note.py','docs/VOZ_NOTA_OBSERVABLE_PROTOCOLO.md']},private_used_sha256={n:h for n,h in r['private_sha256'].items() if n.endswith('.stdout.gz')},private_sha256={v['path']:v['sha256'] for v in records},profiles=records,simulation_duration_s=.1,duration_s=.1,frames=4800,sample_rate=48000,source_grid_hz=8000,nominal_cutoff_hz=2800,sinc_taps=64,monitor_samples_per_v=4,fade_s=.0005,dc_removed=False,peak_normalization=False,repeated_cycles=False,concatenated=False,own_circuit_history=True,physical_fidelity=False,real_time=False,refinement_rms_relative=rms,refinement_peak_relative=peak,refinement_mean_error_v=dc))
    print('OBSERVED_NOTE_AUDIO',records,rms,peak)
if __name__=='__main__':main()
