"""Render six native segments with explicit charged retrigger provenance."""
import argparse,json
from pathlib import Path
from prepare_vco1_portable import sha
from render_voice_retrigger import inputs,joined_trace,code_hashes
from render_conditioned_recipe import adapt,save
from render_release_voice import BASE_START
from prepare_voice_retrigger import START,SPAN,BOUNDARIES,KEY,SHORT,DECAY
from prepare_decay_control import START as CONTROL_START
from joint_cycles_analysis import require,TICK
def main():
 p=argparse.ArgumentParser()
 for n in ['held','release','controlled','extended','tail','retrigger']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();paths=[getattr(a,n) for n in ['held','release','controlled','extended','tail','retrigger']];output=a.output.resolve();sidecar=output.with_suffix('.json');require(output.parent.is_dir(),'output directory exists');require(not output.exists() and not sidecar.exists(),'preserve existing WAV and sidecar');sources={str(p.resolve()):sha(p) for p in inputs(*paths)};code=code_hashes();t,v=joined_trace(*paths);pcm,meta=adapt(t,v,1);require(sources=={str(p.resolve()):sha(p) for p in inputs(*paths)},'stable CLI inputs');save(output,pcm)
 receipt=dict(schema='rf-d/loaded-retrigger-joined-wav/v1',input_sha256=sources,code_sha256=code,wav_sha256=sha(output),initial_ticks=BASE_START,retrigger_start_ticks=START,final_ticks=START+SPAN,joined_window_s=(START+SPAN-BASE_START)*TICK,source_events=[dict(ticks=START+BOUNDARIES[i],keyboard_v=KEY[i],short=SHORT[i]) for i in [1,2]],decay_ohm=DECAY,previous_decay_ohm=100000.,control_event_ticks=CONTROL_START,new_source_event=True,segment_families=['conditioned','conditioned','decay','block','assembly','assembly'],sample_rate_hz=48000,cutoff_hz=18000,volts_per_full_scale=.01,dc_removed=False,peak_normalization=False,fades=False,real_time=False,physical_fidelity=False,**meta);sidecar.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n');print('RETRIGGER_WAV',output,meta['frames'])
if __name__=='__main__':main()
