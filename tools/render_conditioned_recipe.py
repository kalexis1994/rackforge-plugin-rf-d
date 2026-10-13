"""Finite J7 transient; no periodic continuation or additional circuit duration."""
import argparse,base64,json,math,platform,time,traceback,wave
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

RATE=48000; CUTOFF=18000.0; SUPPORT=32/RATE; VOLTS_PER_FS=.01
DTYPE=np.dtype([('ticks','<u8'),('volts','<f8',(5,))])

def load_trace(path):
    raw=path.read_bytes();require(raw[:8]==b'RFJ7TR01' and (len(raw)-8)%48==0,'trace format')
    a=np.frombuffer(raw[8:],dtype=DTYPE);ticks=a['ticks']
    require(len(a)>=3 and np.all(ticks[1:]>ticks[:-1]) and np.isfinite(a['volts']).all(),'trace clock/finite volts')
    require(ticks[0]==4423942144 and ticks[-1]==5998903296,'recipe endpoints')
    return (ticks-ticks[0]).astype(float)*(125e-9/65536),a['volts'][:,0]

def kernel(offset):
    x=offset/SUPPORT
    return 2*CUTOFF*np.sinc(2*CUTOFF*offset)*(.42+.5*np.cos(np.pi*x)+.08*np.cos(2*np.pi*x))

def partition(t,v):
    # Constant padding is used only by the observation filter, never the solver.
    t=np.r_[t[0]-SUPPORT,t,t[-1]+SUPPORT];v=np.r_[v[0],v,v[-1]]
    pieces=np.maximum(1,np.ceil(np.diff(t)*4*CUTOFF).astype(int))
    knots=np.concatenate([np.linspace(a,b,int(n)+1)[:-1] for a,b,n in zip(t[:-1],t[1:],pieces)])
    knots=np.r_[knots,t[-1]]
    return knots,np.interp(knots,t,v)

def filtered(times,volts,centers,order=16):
    t=np.asarray(times,float);v=np.asarray(volts,float);centers=np.asarray(centers,float)
    require(t.ndim==v.ndim==centers.ndim==1 and len(t)==len(v)>=3,'filter arrays')
    require(np.isfinite(t).all() and np.isfinite(v).all() and np.isfinite(centers).all() and np.all(np.diff(t)>0),'filter domain')
    require(order in [8,16] and np.all((centers>=t[0])&(centers<=t[-1])),'finite filter interval')
    t,v=partition(t,v);nodes,weights=np.polynomial.legendre.leggauss(order)
    bins=np.linspace(-SUPPORT,SUPPORT,int(math.ceil(2*SUPPORT*4*CUTOFF))+1)
    half=np.diff(bins)/2;mid=(bins[:-1]+bins[1:])/2
    normalization=float(np.sum(half[:,None]*weights*kernel(mid[:,None]+half[:,None]*nodes)))
    require(math.isfinite(normalization) and normalization>0,'kernel normalization')
    result=np.empty(len(centers))
    for k,c in enumerate(centers):
        first=max(0,int(np.searchsorted(t,c-SUPPORT,side='right'))-1)
        last=min(len(t)-1,int(np.searchsorted(t,c+SUPPORT,side='left')))
        a=t[first:last];b=t[first+1:last+1];va=v[first:last];vb=v[first+1:last+1]
        left=np.maximum(a,c-SUPPORT);right=np.minimum(b,c+SUPPORT)
        half=(right-left)/2;mid=(left+right)/2;x=mid[:,None]+half[:,None]*nodes
        voltage=va[:,None]+((vb-va)/(b-a))[:,None]*(x-a[:,None])
        result[k]=np.sum(half[:,None]*weights*voltage*kernel(x-c))/normalization
    require(np.isfinite(result).all(),'finite filtered output')
    return result

def adapt(t,v,stretch):
    require(stretch in [1,100],'declared time mapping')
    times=t*stretch;frames=int(math.floor((times[-1]-times[0])*RATE));centers=times[0]+(np.arange(frames)+.5)/RATE
    require(frames>0,'nonempty frames')
    fine=filtered(times,v,centers,16);coarse=filtered(times,v,centers,8)
    error=float(np.max(np.abs(fine-coarse)));lsb=VOLTS_PER_FS/32767
    require(error<=.25*lsb,'quadrature gate in volts')
    pcm=quantize(fine);coarse_pcm=quantize(coarse)
    require(np.max(np.abs(pcm.astype(int)-coarse_pcm.astype(int)))<=1,'quadrature PCM gate')
    return pcm,dict(stretch=stretch,frames=frames,wav_duration_s=frames/RATE,
        mapped_window_s=float(times[-1]-times[0]),truncated_tail_s=float(times[-1]-times[0]-frames/RATE),
        quadrature_max_error_v=error,peak_fs=float(np.max(abs(fine))/VOLTS_PER_FS),
        rms_fs=float(np.sqrt(np.mean(fine**2))/VOLTS_PER_FS),new_circuit_duration_s=0,
        repeated=False,full_audio_duration_simulated=stretch==1)

def quantize(volts):
    require(np.isfinite(volts).all() and np.max(np.abs(volts))<VOLTS_PER_FS,'fixed voltage scale must not clip')
    return np.rint(volts/VOLTS_PER_FS*32767).astype('<i2')

def save(path,pcm):
    require(not path.exists(),'exclusive WAV')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(pcm.tobytes())
    with wave.open(str(path),'rb') as w:
        require(w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==RATE and w.getnframes()==len(pcm) and w.readframes(len(pcm))==pcm.tobytes(),'entire PCM roundtrip')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt
    output=f'evidence/voice_conditioned_recipe_listening{attempt:02d}.json';folder=ROOT/f'artifacts/conditioned-recipe{attempt:02d}'
    require(not (ROOT/output).exists() and not folder.exists(),'exclusive listening')
    native='evidence/voice_conditioned_recipe_native02.json';q=json.loads((ROOT/native).read_text(encoding='utf8'));require(q['passed'] and q['identical_replay'],'native before listening')
    names=['tools/render_conditioned_recipe.py','docs/RECETA_CONDICIONADA_PROTOCOLO.md',native]
    sources={n:sha(ROOT/n) for n in names};private={f'references-local/conditioned-recipe-render02/{on}-{maximum}/j7.bin':None for on in [1,0] for maximum in [1048576,524288]}
    for n in private:
        private[n]=sha(ROOT/n);require(private[n]==next(f['sha256'] for f in q['outputs'] if f['path']==n),'native trace SHA')
    r=dict(passed=False,source_sha256=sources,private_used_sha256=private,files=[],
        sample_rate_hz=RATE,cutoff_hz=CUTOFF,sinc_support_s=SUPPORT,window='Blackman',
        volts_per_full_scale=VOLTS_PER_FS,dc_removed=False,peak_normalization=False,
        fades=False,repetition=False,constant_extension_only_in_filter=True,
        simulated_window_s=.003004,history_start_s=.008438,history_end_s=.011442,
        new_extended_duration_s=0,real_time=False,physical_fidelity=False,
        numpy_version=np.__version__,python_version=platform.python_version())
    started=time.perf_counter()
    def derive():
        result=[]
        for on in [1,0]:
            t,v=load_trace(ROOT/f'references-local/conditioned-recipe-render02/{on}-524288/j7.bin')
            for stretch in [1,100]:result.append((on,stretch,*adapt(t,v,stretch)))
        return result
    try:
        a=derive();b=derive();require(all(np.array_equal(x[2],y[2]) and x[3]==y[3] for x,y in zip(a,b)),'identical derived replay')
        r['identical_derived_replay']=True;folder.mkdir(parents=True)
        for on,stretch,pcm,meta in a:
            path=folder/f"rf-d-j7-{'on' if on else 'off'}-{'nativo' if stretch==1 else 'tiempo100'}.wav"
            save(path,pcm);r['files'].append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,**meta))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
        try:derive();r['unchanged_failure_replay']='derivation passed; preserve partial publication'
        except Exception:r['unchanged_failure_replay']=traceback.format_exc()
    r.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-started)
    require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable listening inputs')
    write(output,r);print('RECIPE_LISTENING',r['passed'],r['wall_s'],r.get('failure',''),flush=True);require(r['passed'],'listening')
if __name__=='__main__':main()
