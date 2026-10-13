"""Native WAV/sidecar from public held and release-continuation exports."""
import argparse,json
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from render_release_voice import joined_trace
from render_conditioned_recipe import adapt,save

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parent',type=Path,required=True);parser.add_argument('--continuation',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();sidecar=args.output.with_suffix('.json')
 require(args.output.suffix.lower()=='.wav' and args.output.parent.exists(),'existing output directory/WAV suffix');require(not args.output.exists() and not sidecar.exists(),'preserve existing WAV and sidecar')
 inputs={str(p.resolve()):sha(p) for p in [args.parent,args.continuation]};t,v=joined_trace(args.parent,args.continuation);pcm,meta=adapt(t,v,1);require(inputs=={str(p.resolve()):sha(p) for p in [args.parent,args.continuation]},'stable input traces');save(args.output,pcm)
 r=dict(schema='rf-d/restored-release-joined-wav/v1',input_sha256=inputs,wav_sha256=sha(args.output),joined_simulated_window_s=float(t[-1]),sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,constant_extension_only_in_filter=True,
  dc_removed=False,peak_normalization=False,fades=False,physical_fidelity=False,real_time=False,renderer_sha256=sha(ROOT/'tools/render_release_voice.py'),filter_sha256=sha(ROOT/'tools/render_conditioned_recipe.py'),cli_sha256=sha(Path(__file__)),**meta)
 sidecar.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('RELEASE_WAV',args.output,meta['frames'],meta['wav_duration_s'])
if __name__=='__main__':main()
