"""Reproduce the genuine 68 ms J7 WAV with all input identities in a sidecar."""
import argparse,json
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from render_extended_release import joined_trace,inputs,START,SPAN,DECAY
from prepare_decay_control import START as CONTROL_START
from render_conditioned_recipe import adapt,save
from joint_cycles_analysis import require
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for n in ['held','release','controlled','extended','output']:parser.add_argument('--'+n,type=Path,required=True)
 args=parser.parse_args();sidecar=args.output.with_suffix('.json');require(args.output.suffix.lower()=='.wav' and args.output.parent.exists(),'existing output directory and WAV suffix');require(not args.output.exists() and not sidecar.exists(),'preserve existing WAV and sidecar');paths=inputs(args.held,args.release,args.controlled,args.extended);identities={str(p.resolve()):sha(p) for p in paths};t,v=joined_trace(args.held,args.release,args.controlled,args.extended);pcm,meta=adapt(t,v,1);require(identities=={str(p.resolve()):sha(p) for p in paths},'stable input traces');save(args.output,pcm)
 r=dict(schema='rf-d/extended-release-joined-wav/v1',input_sha256=identities,wav_sha256=sha(args.output),joined_simulated_window_s=float(t[-1]),extended_start_ticks=START,extended_end_ticks=START+SPAN,new_source_event=False,decay_ohm=DECAY,inherited_control_event_ticks=CONTROL_START,previous_decay_ohm=100000.,sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,constant_extension_only_in_filter=True,dc_removed=False,peak_normalization=False,fades=False,physical_fidelity=False,real_time=False,renderer_sha256=sha(ROOT/'tools/render_extended_release.py'),filter_sha256=sha(ROOT/'tools/render_conditioned_recipe.py'),cli_sha256=sha(Path(__file__)),**meta);sidecar.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('EXTENDED_WAV',args.output,meta['frames'],meta['wav_duration_s'])
if __name__=='__main__':main()
