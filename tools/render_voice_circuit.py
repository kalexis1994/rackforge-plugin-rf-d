"""Actual coupled circuit cycles, admitted only within nominal prototype scope."""
import gzip
import json
import math
from pathlib import Path
import numpy as np

import vco1_circuit_reference as vco
import voice_circuit_reference as voice
from render_vco1_circuit import coefficients,synthesize,save

ROOT=vco.ROOT


def output_cycle(raw,edges):
    a,b=edges[-2:];earlier=edges[-3]
    phase=np.linspace(0,1,1025)
    col=voice.VECTORS.index('v(f4_main_output)')+1
    last=np.interp(a+phase*(b-a),raw[:,0],raw[:,col])
    prior=np.interp(earlier+phase*(a-earlier),raw[:,0],raw[:,col])
    difference=float(np.max(np.abs(last-prior)))
    if difference>.005:raise ValueError('5mV cycle repetition gate failed')
    t=np.r_[a,raw[(raw[:,0]>a)&(raw[:,0]<b),0],b]
    p=(t-a)/(b-a);p[0]=0;p[-1]=1
    frequency=1/(b-a)
    c=coefficients(p,np.interp(t,raw[:,0],raw[:,col]),math.floor(.45*48000/frequency))
    return c,frequency,difference


def main():
    validation=vco.read(ROOT/'evidence/voice_circuit_scoped_validation.json')
    archive=ROOT/'evidence/voice_circuit_klu_bank01.json.gz'
    if not validation['nominal_scope_passed'] or vco.sha(archive)!=validation['archive_sha256']:
        raise ValueError('scoped bank validation required')
    bank=json.loads(gzip.decompress(archive.read_bytes()))
    output=ROOT/'artifacts/voice-circuit';output.mkdir(parents=True,exist_ok=True)
    receipt=ROOT/'evidence/voice_circuit_listening.json'
    if receipt.exists():raise ValueError('preserve prior listening artifact')
    report=dict(schema='rf-d/voice-circuit-listening/v1',scenes={},passed=False,
        electrically_coupled=True,imposed_waveform=False,source_archive_sha256=vco.sha(archive),
        full_bank_passed=False,full_duration_spice_render=False,volts_per_full_scale=8,
        sample_rate_hz=48000,fade_s=.01,dc_removed=True,physical_fidelity=False,real_time=False)
    parts=[]
    try:
        for label,scene in [('sierra','nominal125'),('triangulo','triangle'),('pulso','pulse-narrow')]:
            case=bank['cases'][scene]
            if case.get('error') or scene not in validation['completed_trace_replay']:
                raise ValueError('completed audited scene required')
            path=ROOT/'references-local/voice-circuit'/bank['bank']/(scene+'.txt')
            if vco.sha(path)!=case['receipt']['raw_export_sha256']:raise ValueError('raw source digest')
            raw=np.loadtxt(path,skiprows=1)
            c,freq,difference=output_cycle(raw,case['measurements']['reset_crossings_s'])
            audio=synthesize(c,freq,duration=.75)
            path=output/f'rf-d-voz-{label}.wav';save(path,audio,48000)
            report['scenes'][label]=dict(scene=scene,frequency_hz=freq,prior_cycle_difference_v=difference,
                removed_dc_v=float(c[0].real),audio_path=path.relative_to(ROOT).as_posix(),
                audio_sha256=vco.sha(path),source_raw_sha256=case['receipt']['raw_export_sha256'])
            parts.extend([audio,np.zeros(7200)])
            print(label,'complete',freq,difference,flush=True)
        path=output/'rf-d-voz-sierra-triangulo-pulso.wav';save(path,np.concatenate(parts[:-1]),48000)
        report.update(passed=True,montage=dict(path=path.relative_to(ROOT).as_posix(),sha256=vco.sha(path)),
            renderer_sha256=vco.sha(Path(__file__)))
    except Exception as e:
        report['error']=type(e).__name__+': '+str(e);raise
    finally:
        receipt.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
