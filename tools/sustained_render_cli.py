"""WAV and sidecar from a standalone sustained_voice selected.txt export."""
import argparse,json,platform
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from render_sustained_voice import load_trace
from render_conditioned_recipe import adapt,save,RATE,CUTOFF,SUPPORT,VOLTS_PER_FS

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--stretch',type=int,choices=[1,100],default=1);args=parser.parse_args()
    sidecar=args.output.with_suffix('.json');require(args.output.suffix.lower()=='.wav' and args.output.parent.exists(),'existing output directory and WAV suffix');require(not args.output.exists() and not sidecar.exists(),'preserve existing WAV and sidecar')
    source_sha=sha(args.source);t,v=load_trace(args.source);pcm,meta=adapt(t,v,args.stretch);require(sha(args.source)==source_sha,'source immutable during adaptation')
    save(args.output,pcm);metadata=dict(schema='rf-d/sustained-on-finite-wav/v1',recipe='rf-d/held8-release4-ca3046/v1',input_source=str(args.source.resolve()),input_source_sha256=source_sha,wav_sha256=sha(args.output),
        sample_rate_hz=RATE,cutoff_hz=CUTOFF,sinc_support_s=SUPPORT,window='Blackman',volts_per_full_scale=VOLTS_PER_FS,simulated_window_s=float(t[-1]),constant_extension_only_in_filter=True,
        dc_removed=False,peak_normalization=False,fades=False,physical_fidelity=False,real_time=False,python_version=platform.python_version(),numpy_version=np.__version__,
        source_parser_sha256=sha(ROOT/'tools/render_sustained_voice.py'),filter_sha256=sha(ROOT/'tools/render_conditioned_recipe.py'),cli_sha256=sha(Path(__file__)),**meta)
    sidecar.write_text(json.dumps(metadata,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('SUSTAINED_WAV',args.output,meta['frames'],meta['wav_duration_s'])
if __name__=='__main__':main()
