"""Publish a same-origin pair of native WAVs and its complete comparison sidecar."""
import argparse,json
from pathlib import Path
from prepare_vco1_portable import sha
from render_cutoff_ab import inputs,pair_audio,code_hashes
from render_conditioned_recipe import save
from prepare_cutoff_ab import START,SPAN
from joint_cycles_analysis import require
def main():
 p=argparse.ArgumentParser();p.add_argument('--open',type=Path,required=True);p.add_argument('--closed',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();side=a.output.resolve().with_suffix('.json');paths=[side.with_name(side.stem+'-'+branch+'.wav') for branch in ['open','closed']];require(side.parent.is_dir(),'output directory exists');require(not any(f.exists() for f in [side,*paths]),'preserve existing WAVs and sidecar');before={str(f.resolve()):sha(f) for f in inputs(a.open,a.closed)};m,pcm,meta,_,metrics=pair_audio(a.open,a.closed);require(before=={str(f.resolve()):sha(f) for f in inputs(a.open,a.closed)},'stable CLI branch inputs')
 for path,signal in zip(paths,pcm):save(path,signal)
 r=dict(schema='rf-d/same-origin-cutoff-ab/v1',input_sha256=before,code_sha256=code_hashes(),maximum_half_ticks=m,start_ticks=START,end_ticks=START+SPAN,open_alpha=1.,closed_alpha=.5,branch_duration_s=.008,new_continuous_history_duration_s=0,source_controls=dict(keyboard_v=0.,short=False,final_decay=True,decay_ohm=1000.),resampling_cutoff_hz=18000,volts_per_full_scale=.01,dc_removed=False,peak_normalization=False,fades=False,repeated=False,physical_fidelity=False,real_time=False,metrics=metrics,files=[dict(branch=branch,sha256=sha(path),**md) for branch,path,md in zip(['open','closed'],paths,meta)]);side.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('CUTOFF_AB_PAIR',m,384)
if __name__=='__main__':main()
