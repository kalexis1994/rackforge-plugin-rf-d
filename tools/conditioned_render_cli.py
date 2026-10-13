"""Adapt one raw public-recipe render to WAV with its explicit sidecar."""
import argparse,json,platform
from pathlib import Path
import numpy as np
from render_conditioned_recipe import load_trace,adapt,save,RATE,CUTOFF,SUPPORT,VOLTS_PER_FS
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--stretch',type=int,choices=[1,100],default=1)
    args=parser.parse_args();sidecar=args.output.with_suffix('.json')
    require(args.output.suffix.lower()=='.wav' and args.output.parent.exists(),'existing output directory and WAV suffix')
    require(not args.output.exists() and not sidecar.exists(),'preserve existing WAV and sidecar')
    before=sha(args.trace);t,v=load_trace(args.trace);pcm,meta=adapt(t,v,args.stretch)
    require(sha(args.trace)==before,'unchanged trace');save(args.output,pcm)
    metadata=dict(schema='rf-d/finite-conditioned-j7-wav/v1',recipe='rf-d/conditioned-j7-ca3046/v1',
        input_trace=str(args.trace.resolve()),input_trace_sha256=before,
        wav_sha256=sha(args.output),sample_rate_hz=RATE,cutoff_hz=CUTOFF,
        sinc_support_s=SUPPORT,window='Blackman',volts_per_full_scale=VOLTS_PER_FS,
        simulated_window_s=float(t[-1]),constant_extension_only_in_filter=True,
        dc_removed=False,peak_normalization=False,fades=False,
        physical_fidelity=False,real_time=False,numpy_version=np.__version__,
        python_version=platform.python_version(),
        renderer_sha256=sha(ROOT/'tools/render_conditioned_recipe.py'),
        cli_sha256=sha(Path(__file__)),**meta)
    sidecar.write_text(json.dumps(metadata,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    print('CONDITIONED_WAV',args.output,meta['frames'],meta['wav_duration_s'])
if __name__=='__main__':main()
