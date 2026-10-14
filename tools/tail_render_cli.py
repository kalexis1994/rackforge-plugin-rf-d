"""Reproduce the actual joined 132 ms waveform with a complete input sidecar."""
import argparse,json,sys
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from render_long_tail import joined_trace,inputs,START,SPAN,DECAY,BASE_START
from prepare_decay_control import START as CONTROL_START
from render_conditioned_recipe import adapt,save
from joint_cycles_analysis import require
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for n in ['held','release','controlled','extended','tail','output']:parser.add_argument('--'+n,type=Path,required=True)
 a=parser.parse_args();sidecar=a.output.with_suffix('.json');require(a.output.suffix.lower()=='.wav' and a.output.parent.exists(),'existing output directory and WAV suffix');require(not a.output.exists() and not sidecar.exists(),'preserve existing WAV and sidecar');traces=[a.held,a.release,a.controlled,a.extended,a.tail];paths=inputs(*traces);identities={str(p.resolve()):sha(p) for p in paths};t,v=joined_trace(*traces);pcm,meta=adapt(t,v,1);require(identities=={str(p.resolve()):sha(p) for p in paths},'stable input traces');save(a.output,pcm);code={}
 for m in list(sys.modules.values()):
  file=getattr(m,'__file__',None)
  if file:
   p=Path(file).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':code[p.relative_to(ROOT/'tools').as_posix()]=sha(p)
 r=dict(schema='rf-d/long-tail-joined-wav/v1',input_sha256=identities,code_sha256=code,wav_sha256=sha(a.output),joined_simulated_window_s=float(t[-1]),initial_ticks=BASE_START,tail_start_ticks=START,final_ticks=START+SPAN,new_source_event=False,decay_ohm=DECAY,inherited_control_event_ticks=CONTROL_START,previous_decay_ohm=100000.,sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,constant_extension_only_in_filter=True,dc_removed=False,peak_normalization=False,fades=False,physical_fidelity=False,real_time=False,**meta);sidecar.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('TAIL_WAV',a.output,meta['frames'],meta['wav_duration_s'])
if __name__=='__main__':main()
