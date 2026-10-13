"""Listen to a genuine longer trajectory; repeat a held cycle only after its gate."""
import argparse,base64,json,math,platform,time,traceback
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_sustained_voice import START,BOUNDARIES
from joint_cycles_analysis import require,TICK
from render_conditioned_recipe import filtered,adapt,quantize,save,RATE,VOLTS_PER_FS
from render_vco1_circuit import coefficients,synthesize

def load_trace(path):
    lines=path.read_text(encoding='utf8').splitlines()
    require(lines[0] in ['PROFILE,1,1048576','PROFILE,1,524288'] and lines[1].startswith('JOINT_STATE,'),'ON recipe profile')
    initial=list(map(float,lines[1].split(',')[1:]));rows=[list(map(float,line.split(',')[1:])) for line in lines if line.startswith('OBS,')]
    require(len(initial)==458 and all(len(row)==24 for row in rows),'complete state/observable records')
    ticks=np.array([START]+[int(row[0]) for row in rows],dtype=np.uint64);volts=np.array([initial[194]+initial[423]]+[row[4] for row in rows])
    require(ticks[0]==START and ticks[-1]==START+BOUNDARIES[-1] and np.all(ticks[1:]>ticks[:-1]) and np.isfinite(volts).all(),'complete held trace')
    boundaries=[line.split(',') for line in lines if line.startswith('BOUNDARY,')]
    require(len(boundaries)==3,'three source events')
    for phase,row in enumerate(boundaries):
        require(int(row[1])==phase and int(row[2])==START+BOUNDARIES[phase] and float(row[3])==[0.,10.,0.][phase] and int(row[4])==[0,1,0][phase],'declared source calendar')
    require(lines[-2].startswith('TOTAL,') and lines[-1].startswith('JOINT_STATE,'),'complete trajectory')
    return (ticks-ticks[0]).astype(float)*TICK,volts

def trace(maximum):return load_trace(ROOT/f'references-local/sustained-voice01/{maximum}/selected.txt')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt
    out=f'evidence/voice_sustained_listening{attempt:02d}.json';folder=ROOT/f'artifacts/sustained-voice{attempt:02d}';require(not (ROOT/out).exists() and not folder.exists(),'exclusive listening')
    name='evidence/voice_sustained_reference01.json';ref=json.loads((ROOT/name).read_text(encoding='utf8'));require(ref['passed'] and ref['sustained_on_window_admitted'],'admitted extended trajectory')
    names=[name,'tools/render_sustained_voice.py','tools/render_conditioned_recipe.py','tools/render_vco1_circuit.py','tools/prepare_sustained_voice.py','docs/VOZ_SOSTENIDA_ESCUCHA.md','docs/VOZ_SOSTENIDA_PROTOCOLO.md']
    sources={n:sha(ROOT/n) for n in names};private={f'references-local/sustained-voice01/{m}/selected.txt':sha(ROOT/f'references-local/sustained-voice01/{m}/selected.txt') for m in [1048576,524288]}
    for p in ref['profiles']:
        for n,h in p['input_sha256'].items():
            if n in private:require(private[n]==h,'admitted source trace')
    r=dict(passed=False,source_sha256=sources,private_used_sha256=private,files=[],simulated_window_s=.012004,
        native_rate_hz=48000,native_cutoff_hz=18000,volts_per_full_scale=.01,
        native_repeated=False,native_dc_removed=False,native_fades=False,peak_normalization=False,
        constant_extension_only_in_native_filter=True,repetition_candidate=ref['repetition_candidate'],
        full_audio_duration_simulated=False,steady_periodicity_admitted=False,real_time=False,physical_fidelity=False,
        numpy_version=np.__version__,python_version=platform.python_version())
    started=time.perf_counter()
    def derive():
        sources=[trace(m) for m in [1048576,524288]];result=[];native_volts=[]
        for maximum,(t,v) in zip([1048576,524288],sources):
            pcm,meta=adapt(t,v,1);require(meta['frames']==576,'native frame count')
            centers=(np.arange(576)+.5)/RATE;native_volts.append(filtered(t,v,centers,16));result.append((f'rf-d-j7-sostenido-{maximum}-nativo.wav',pcm,dict(maximum_half_ticks=maximum,adaptation='native',**meta)))
        error=float(np.max(abs(native_volts[0]-native_volts[1])));pcm_error=int(np.max(abs(result[0][1].astype(int)-result[1][1].astype(int))));require(error<=2e-6 and pcm_error<=7,'native audio resolution gate')
        t,v=sources[-1];pcm,meta=adapt(t,v,100);require(meta['frames']==57619,'microscope frame count');result.append(('rf-d-j7-sostenido-tiempo100.wav',pcm,dict(maximum_half_ticks=524288,adaptation='microscope',**meta)))
        cycle_metadata=None
        if ref['repetition_candidate']:
            cs=[];rate=48000
            for maximum,(t,v),d in zip([1048576,524288],sources,ref['cycle_diagnostics']):
                a,b=[x-START*TICK for x in d['held_cycle_edges_s'][-2:]];knots=np.r_[a,t[(t>a)&(t<b)],b];phase=(knots-a)/(b-a);phase[0]=0.;phase[-1]=1.;freq=1/(b-a);harmonics=int(math.floor(.45*rate/freq));cs.append((coefficients(phase,np.interp(knots,t,v),harmonics),freq,[a,b]))
            require(len(cs[0][0])==len(cs[1][0]),'same harmonic count')
            coefficient_error=float(np.max(abs(cs[0][0]-cs[1][0])));require(coefficient_error<=2e-6,'cycle coefficient refinement')
            c,freq,window=cs[-1];audio=synthesize(c,freq,rate,duration=1.5,volts_per_full_scale=VOLTS_PER_FS);pcm=np.rint(audio*32767).astype('<i2')
            cycle_metadata=dict(maximum_half_ticks=524288,adaptation='observed-cycle-repeated',frames=72000,wav_duration_s=1.5,
                source_relative_window_s=window,frequency_hz=freq,harmonics=len(c)-1,removed_dc_v=float(c[0].real),fade_s=.01,
                peak_fs=float(np.max(abs(audio))),repeated=True,full_audio_duration_simulated=False,coefficient_difference_v=coefficient_error)
            result.append(('rf-d-j7-ciclo-sostenido-repetido.wav',pcm,cycle_metadata))
        return result,dict(native_resolution_max_error_v=error,native_resolution_max_pcm_lsb=pcm_error,cycle_repeated=cycle_metadata is not None)
    try:
        a,metrics=derive();b,metrics2=derive();require(metrics==metrics2 and all(x[0]==y[0] and np.array_equal(x[1],y[1]) and x[2]==y[2] for x,y in zip(a,b)),'identical listening derivation replay')
        folder.mkdir(parents=True)
        for filename,pcm,meta in a:
            path=folder/filename;save(path,pcm);r['files'].append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,**meta))
        r.update(passed=True,identical_derived_replay=True,**metrics)
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
        try:derive();r['unchanged_replay']='derivation passed; preserve publication failure'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    r.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-started)
    require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable listening inputs');write(out,r);print('SUSTAINED_LISTENING',r['passed'],r.get('cycle_repeated'),r['wall_s'],r.get('failure',''),flush=True);require(r['passed'],'extended listening')
if __name__=='__main__':main()
