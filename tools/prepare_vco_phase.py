"""Derive nominal phase/source coefficients from admitted circuit evidence."""
import base64,gzip,json,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from vco1_radau_joined_trace import blocks
TICK=125e-9/65536
def voice(maximum):
    r=json.loads((ROOT/'evidence/observed_note_native01.json').read_text(encoding='utf8'))
    p=ROOT/r['output_directory']/f'profile-{maximum}.stdout.gz';rows=[]
    for line in gzip.decompress(p.read_bytes()).decode('utf8').splitlines():
        z=line.split(',')
        if z[0]=='GRID':
            a=np.array(list(map(float,z[2:502])));rows.append([int(z[1])*TICK,*(a[:250]+a[250:])])
    return np.array(rows),p
def crossings(x):
    t=x[:,0];v=x[:,44];k=np.flatnonzero((v[:-1]>-2)&(v[1:]<=-2))
    return t[k]+(-2-v[k])*(t[k+1]-t[k])/(v[k+1]-v[k])
def derive():
    listen=json.loads((ROOT/'evidence/voice_vco1_radau_listening01.json').read_text(encoding='utf8'));assert listen['passed']
    a,b=listen['window_s'];entries=[dict(path=ROOT/e['path'],skip_rows=e['skip_rows'],take_rows=e['take_rows']) for e in listen['source_segments']]
    cycle=[]
    for block in blocks(entries):
        t=block[:,0]*TICK;v=block[:,49]+block[:,183]
        selected=(t>=a)&(t<=b)
        if selected.any():cycle.extend(zip(t[selected].tolist(),v[selected].tolist()))
    cycle=np.array(cycle);k=np.flatnonzero((cycle[:-1,1]>-2)&(cycle[1:,1]<=-2));assert len(k)==1
    k=int(k[0]);down=cycle[k,0]+(-2-cycle[k,1])*(cycle[k+1,0]-cycle[k,0])/(cycle[k+1,1]-cycle[k,1])
    down_phase=(down-a)/(b-a)
    x,path=voice(8388608);c=crossings(x);idx=np.arange(len(c));train=(c>=.008)&(c<.04)
    period,origin=np.linalg.lstsq(np.column_stack([idx[train],np.ones(sum(train))]),c[train],rcond=None)[0]
    epoch=origin-down_phase*period
    saw=np.array([complex(*v) for v in listen['coefficients']['sierra']]);tri=np.array([complex(*v) for v in listen['coefficients']['triangulo']]);assert len(saw)==len(tri)==53
    conductance=1/4700+1/4300+1/57000+1/25000+.25/39250
    drive=4300*(conductance*saw-tri/57000)
    text='//! Generated nominal CA3046 periodic sources; prepare_vco_phase.py.\n//! DC retained, 52 harmonics, no general CV calibration.\n'
    text+=f'pub const FREQUENCY_HZ:f64={1/period:.17e};\npub const EPOCH_S:f64={epoch:.17e};\n'
    for name,array in [('DRIVE',drive),('TRIANGLE',tri)]:
        text+=f'pub const {name}:[[f64;2];53]=[\n'+''.join(f'    [{v.real:.17e},{v.imag:.17e}],\n' for v in array)+'];\n'
    source='crates/rf-d-circuit/src/vco_phase_profile.rs';assert not (ROOT/source).exists();(ROOT/source).write_text(text,encoding='utf8',newline='\n')
    return dict(passed=True,frequency_hz=float(1/period),epoch_s=float(epoch),training_window_s=[.008,.04],training_crossings=int(sum(train)),source_cycle_down_phase=float(down_phase),source_cycle_window_s=listen['window_s'],source_isolated_frequency_hz=listen['frequency_hz'],generated_source=source,generated_source_sha256=sha(ROOT/source),private_used_sha256={**{e['path']:sha(ROOT/e['path']) for e in listen['source_segments']},path.relative_to(ROOT).as_posix():sha(path)},source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_vco_phase.py','tools/vco1_radau_joined_trace.py','tools/vco1_radau_trace.py','evidence/voice_vco1_radau_listening01.json','evidence/observed_note_native01.json','docs/VCO_FASE_NOMINAL_PROTOCOLO.md']},new_private_sound_inputs=0,new_native_trajectory=False)
def main():
    out=ROOT/'evidence/vco_phase_profile01.json';assert not out.exists()
    try:r=derive()
    except Exception:
        r=dict(passed=False,failure=traceback.format_exc(),source_base64=base64.b64encode((ROOT/'tools/prepare_vco_phase.py').read_bytes()).decode())
        try:derive();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    write(out,r);print('VCO_PHASE_PROFILE',r['passed'],r.get('frequency_hz'),r.get('epoch_s'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
