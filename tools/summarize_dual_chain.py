"""Voltages and load currents on the declared 250-us observation grid."""
import json
from prepare_dual_chain import ROOT,sha,write
from dual_chain_reference import N,ci
def main():
    native='evidence/dual_chain_native04.json';r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed']
    path=ROOT/r['output_directory']/'profile-4.stdout';rows={}
    for line in path.read_text(encoding='utf8').splitlines():
        if line.startswith('GRID,'):
            x=list(map(float,line.split(',')[1:]));rows[int(x[0])//1073741824]=([x[1+k]+x[1+N+k] for k in range(N)],x[-2:])
    signals={}
    for i,name in [(5,'C2_v'),(38,'C5_v'),(54,'VCA_base_v'),(55,'TAIL_v'),(ci(61),'J7_v'),(ci(66),'BUS_v')]:
        v=[s[i] for s,_ in rows.values()];signals[name]=dict(minimum=min(v),maximum=max(v),final=v[-1])
    events=[dict(clock_s=t*1e-6,C2_v=rows[t][0][5],C5_v=rows[t][0][38],r59_a=rows[t][1][0],r60_a=rows[t][1][1]) for t in [1000,10000,20000,30000,36000]]
    write(ROOT/'evidence/dual_chain_observations01.json',dict(schema='rf-d/dual-chain/observations-v1',native_receipt=native,native_receipt_sha256=sha(ROOT/native),trace_sha256=sha(path),source_sha256={'tools/summarize_dual_chain.py':sha(ROOT/'tools/summarize_dual_chain.py')},grid_interval_s=.00025,observations=144,duration_s=.036,sampled_extrema=True,continuous_extrema=False,normalization=False,dc_removed=False,signals=signals,events=events,source='imposed 100 Hz, 0.2 V peak at mixer OSC1; not a VCO model',new_audio=False))
    print('JOINT_OBSERVATIONS',signals)
if __name__=='__main__':main()
