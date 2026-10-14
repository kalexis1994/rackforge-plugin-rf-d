"""Unadapted electrical observations from the full 8-ms VCO/contour voice."""
import json
from prepare_dual_chain import ROOT,sha,write
from audit_dual_voice import di,N
def main():
    native='evidence/dual_voice_native02.json';ref='evidence/dual_voice_reference01.json'
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed'] and json.loads((ROOT/ref).read_text(encoding='utf8'))['passed']
    path=ROOT/r['output_directory']/'profile-524288.stdout';trace=[]
    for line in path.read_text(encoding='utf8').splitlines():
        if line.startswith('GRID,'):
            x=list(map(float,line.split(',')[1:]));trace.append((x[0]/524288*1e-6,[x[1+k]+x[1+N+k] for k in range(N)],x[-2:]))
    signals={}
    for k,name in [(43,'RAMP_C1_v'),(46,'SAW_v'),(12,'BUS_v'),(di(5),'C2_v'),(di(38),'C5_v'),(di(54),'VCA_BASE_v'),(di(115),'J7_v')]:
        v=[x[1][k] for x in trace];signals[name]=dict(minimum=min(v),maximum=max(v),final=v[-1])
    write(ROOT/'evidence/dual_voice_observations01.json',dict(schema='rf-d/dual-voice/observations-v1',native_receipt=native,native_receipt_sha256=sha(ROOT/native),reference_receipt_sha256=sha(ROOT/ref),source_sha256={'tools/summarize_dual_voice.py':sha(ROOT/'tools/summarize_dual_voice.py')},trace_sha256=sha(path),duration_s=.008,grid_interval_s=.000125,observations=64,signals=signals,events=[dict(clock_s=x[0],r59_a=x[2][0],r60_a=x[2][1]) for x in trace if round(x[0]*1e6) in [1000,6000,8000]],sampled_extrema=True,continuous_extrema=False,imposed_audio_source=False,normalization=False,dc_removed=False,new_audio=False))
    print('DUAL_VOICE_OBSERVATIONS',signals)
if __name__=='__main__':main()
