"""Reproducible WAV through the documented 100k->1k electrical control event."""
import argparse,json
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from render_decay_control import joined_trace,START,DECAY
from render_conditioned_recipe import adapt,save
from joint_cycles_analysis import require

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for n in ['held','release','controlled','output']:parser.add_argument('--'+n,type=Path,required=True)
 args=parser.parse_args();sidecar=args.output.with_suffix('.json');require(args.output.suffix.lower()=='.wav' and args.output.parent.exists(),'existing output directory and WAV suffix');require(not args.output.exists() and not sidecar.exists(),'preserve existing WAV and sidecar')
 paths=[args.held,args.release,args.controlled,args.controlled.with_name('control-event.txt')];inputs={str(p.resolve()):sha(p) for p in paths};t,v=joined_trace(args.held,args.release,args.controlled);pcm,meta=adapt(t,v,1);require(inputs=={str(p.resolve()):sha(p) for p in paths},'stable input traces');save(args.output,pcm)
 r=dict(schema='rf-d/electrical-decay-joined-wav/v1',input_sha256=inputs,wav_sha256=sha(args.output),joined_simulated_window_s=float(t[-1]),sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,decay_control_event_ticks=START,previous_decay_ohm=100000.,new_decay_ohm=DECAY,constant_extension_only_in_filter=True,dc_removed=False,peak_normalization=False,fades=False,physical_fidelity=False,real_time=False,renderer_sha256=sha(ROOT/'tools/render_decay_control.py'),filter_sha256=sha(ROOT/'tools/render_conditioned_recipe.py'),cli_sha256=sha(Path(__file__)),**meta);sidecar.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('DECAY_WAV',args.output,meta['frames'],meta['wav_duration_s'])
if __name__=='__main__':main()
