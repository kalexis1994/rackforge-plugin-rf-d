"""Listening adaptation of the entire measured 350ms electrical note.

Finite sine input; physical loudness circuit and both VCAs resolved together.
Fixed scale, global DC removal, zero-phase FIR and 10ms fades. No cycle loop.
"""
import gzip
import json
import math
from pathlib import Path
import wave
import numpy as np
import loudness_board4_circuit as c
import loudness_board4_probes as p
import vco1_circuit_reference as vco

ROOT=vco.ROOT


def adapt(raw,scenario):
    fs=48000;up=8;high_fs=fs*up;n=round(scenario.oscillator.duration_s*fs)
    x=raw[:,scenario.vectors.index('v(f4_main_output)')+1]
    dc=float(np.trapezoid(x,raw[:,0])/scenario.oscillator.duration_s)
    clock=np.arange(n*up)/high_fs
    hi=np.interp(clock,raw[:,0],x)-dc
    taps=1025;center=(taps-1)//2;k=np.arange(taps)-center
    normalized=.45*fs/high_fs
    kernel=2*normalized*np.sinc(2*normalized*k)*np.kaiser(taps,8.6);kernel/=kernel.sum()
    padded=np.pad(hi,(center,center),mode='reflect');length=len(padded)+taps-1
    size=1<<(length-1).bit_length()
    full=np.fft.irfft(np.fft.rfft(padded,size)*np.fft.rfft(kernel,size),size)
    audio=full[taps-1:taps-1+len(hi):up]/8
    fade=round(.01*fs);audio[:fade]*=np.linspace(0,1,fade);audio[-fade:]*=np.linspace(1,0,fade)
    if len(audio)!=n or not np.isfinite(audio).all() or np.max(np.abs(audio))>=1:
        raise ValueError('audio frame/finiteness/clipping gate')
    return audio,dc


def save(path,audio):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
        f.writeframes(np.rint(audio*32767).astype('<i2').tobytes())


def main():
    validation=vco.read(ROOT/'evidence/loudness_board4_validation.json')
    archive=ROOT/'evidence/loudness_board4_bank02.json.gz';bank=json.loads(gzip.decompress(archive.read_bytes()))
    if not validation['passed'] or vco.sha(archive)!=validation['archive_sha256']:raise ValueError('audited source required')
    receipt=ROOT/'evidence/loudness_board4_listening.json'
    if receipt.exists():raise ValueError('preserve prior render')
    output=ROOT/'artifacts/loudness-board4';output.mkdir(parents=True,exist_ok=True)
    report=dict(schema='rf-d/loudness-board4-listening/v1',passed=False,scenes={},
        archive_sha256=vco.sha(archive),sample_rate_hz=48000,volts_per_full_scale=8,
        removed_dc=True,fade_s=.01,full_duration_spice_render=True,cycle_repetition=False,
        vco_electrically_coupled=False,input_waveform='imposed laboratory sine 440Hz, 0.1V peak through 1kohm',
        band_adaptation=dict(oversampling=8,interpolation='linear at nonuniform clock',
            fir_taps=1025,fir_cutoff_hz=21600,kaiser_beta=8.6,phase='symmetric delay removed',padding='reflect'),
        physical_fidelity=False,real_time=False,renderer_sha256=vco.sha(Path(__file__)))
    parts=[]
    try:
        for label in ('nominal2','attack1000','final-decay-off'):
            source=ROOT/'references-local/voice-circuit'/bank['bank']/(label+'.txt')
            if vco.sha(source)!=bank['cases'][label]['receipt']['raw_export_sha256']:raise ValueError('raw identity')
            raw=np.loadtxt(source,skiprows=1);audio,dc=adapt(raw,p.scenes()[label])
            path=output/('rf-d-contorno-'+label+'.wav');save(path,audio)
            report['scenes'][label]=dict(path=path.relative_to(ROOT).as_posix(),sha256=vco.sha(path),
                source_raw_sha256=vco.sha(source),removed_dc_v=dc,frames=len(audio),
                peak_full_scale=float(np.max(np.abs(audio))))
            parts += [audio,np.zeros(7200)]
        path=output/'rf-d-contorno-nominal-ataque-rapido-decay-off.wav';save(path,np.concatenate(parts[:-1]))
        report.update(passed=True,montage=dict(path=path.relative_to(ROOT).as_posix(),sha256=vco.sha(path),duration_s=1.35))
    finally:receipt.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('full electrical note listening complete',flush=True)


if __name__=='__main__':main()
