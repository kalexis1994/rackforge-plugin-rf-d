"""Listening adapter for the measured stationary VCO cycle, not a voice.

Exact Fourier integrals of the exported piecewise-linear circuit trajectory
avoid sampling its fast reset directly at the audio rate. No ideal saw,
triangle or pulse replaces the circuit waveforms. DC removal, band limit,
fixed volts-to-full-scale mapping and fades belong only to this adapter.
"""
import json
import math
from pathlib import Path
import wave

import numpy as np

from vco1_circuit_reference import ROOT, sha
from validate_vco1_circuit_bank import load, audit


def coefficients(phase, voltage, count):
    phase,voltage=np.asarray(phase,float),np.asarray(voltage,float)
    if phase.ndim!=1 or phase.shape!=voltage.shape or len(phase)<3 or not np.isfinite(phase).all() or not np.isfinite(voltage).all():
        raise ValueError("finite one-dimensional cycle required")
    if phase[0]!=0 or phase[-1]!=1 or np.any(np.diff(phase)<=0) or not isinstance(count,int) or count<1:
        raise ValueError("complete increasing unit cycle and positive harmonic count required")
    lengths=np.diff(phase)
    delta=np.diff(voltage)
    result=[complex(np.trapezoid(voltage,phase))]
    for n in range(1,count+1):
        z=2j*np.pi*n*lengths
        a0=-np.expm1(-z)/z
        a1=np.empty_like(z)
        small=np.abs(z)<.001
        # Integral of u*exp(-z*u) on [0,1]; series avoids cancellation.
        a1[small]=sum((-z[small])**k/(math.factorial(k)*(k+2)) for k in range(8))
        a1[~small]=(-np.expm1(-z[~small])-z[~small]*np.exp(-z[~small]))/z[~small]**2
        value=np.sum(np.exp(-2j*np.pi*n*phase[:-1])*lengths*(voltage[:-1]*a0+delta*a1))
        result.append(complex(value))
    return np.asarray(result)


def synthesize(c, frequency, rate=48000, duration=.75, volts_per_full_scale=8):
    if not all(math.isfinite(v) and v>0 for v in (frequency,rate,duration,volts_per_full_scale)):
        raise ValueError("positive finite listening parameters required")
    c=np.asarray(c,complex)
    if c.ndim!=1 or len(c)<2 or not np.isfinite(c).all() or (len(c)-1)*frequency>=rate/2:
        raise ValueError("finite harmonics strictly below Nyquist required")
    t=np.arange(int(round(rate*duration)))/rate
    audio=np.zeros_like(t)
    for n,coefficient in enumerate(c[1:],1):
        audio+=2*np.real(coefficient*np.exp(2j*np.pi*n*frequency*t))
    audio/=volts_per_full_scale
    # Ten millisecond endpoint fades; no amplitude normalization or clipping.
    fade=min(int(.01*rate),len(audio)//2)
    if fade:
        envelope=.5-.5*np.cos(np.pi*np.arange(fade)/fade)
        audio[:fade]*=envelope
        audio[-fade:]*=envelope[::-1]
    if np.max(np.abs(audio))>=1: raise ValueError("fixed voltage scale clips")
    return audio


def save(path,audio,rate):
    if path.exists(): raise ValueError("preserve previous listening artifact")
    pcm=np.rint(audio*32767).astype("<i2")
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(pcm.tobytes())
    with wave.open(str(path),"rb") as w:
        if w.getnframes()!=len(audio) or w.getframerate()!=rate or w.getnchannels()!=1:
            raise ValueError("WAV round-trip format check failed")


def main():
    report=load();audit(report)
    label="c4-10-gear125"
    raw_path=ROOT/"references-local/vco1-circuit"/report["bank"]/(label+".txt")
    if sha(raw_path)!=report["cases"][label]["receipt"]["raw_export_sha256"]:
        raise ValueError("measured circuit export changed")
    validation=json.loads((ROOT/"evidence/vco1_circuit_validation.json").read_text(encoding="utf-8"))
    if not validation["passed"]: raise ValueError("audited circuit bank required")
    raw=np.loadtxt(raw_path,skiprows=1)
    edges=report["cases"][label]["measurements"]["reset_crossings_s"]
    a,b=edges[-2:]
    t=raw[:,0]
    knots=np.r_[a,t[(t>a)&(t<b)],b]
    phase=(knots-a)/(b-a);phase[0]=0;phase[-1]=1
    frequency=1/(b-a);rate=48000
    harmonics=int(math.floor(.45*rate/frequency))
    output=ROOT/"artifacts/vco1-circuit"
    output.mkdir(parents=True,exist_ok=True)
    meta=dict(schema="rf-d/vco1-circuit-listening/v1",scene=label,frequency_hz=frequency,
        sample_rate_hz=rate,harmonics=harmonics,highest_harmonic_hz=harmonics*frequency,
        duration_per_wave_s=.75,volts_per_full_scale=8.0,fade_s=.01,
        source_raw_sha256=sha(raw_path),source_renderer_sha256=sha(Path(__file__)),
        removed_dc_v={},files={},
        method="Stationary measured cycle, exact piecewise-linear Fourier integrals; omit DC and harmonics above .45 Fs. Fixed 8V/FS, 10ms fades, no peak normalization.",
        full_duration_spice_render=False,full_voice=False,physical_fidelity=False)
    parts=[]
    for name,column in (("sierra",3),("triangulo",4),("pulso",5)):
        voltage=np.interp(knots,t,raw[:,column])
        c=coefficients(phase,voltage,harmonics)
        audio=synthesize(c,frequency,rate)
        path=output/f"rf-d-vco1-{name}.wav"
        save(path,audio,rate)
        parts.append(audio)
        meta["removed_dc_v"][name]=float(c[0].real)
        meta["files"][name]=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),peak=float(np.max(np.abs(audio))))
    montage=np.concatenate([parts[0],np.zeros(int(.15*rate)),parts[1],np.zeros(int(.15*rate)),parts[2]])
    path=output/"rf-d-vco1-sierra-triangulo-pulso.wav"
    save(path,montage,rate)
    meta["files"]["montaje"]=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),duration_s=len(montage)/rate)
    meta_path=ROOT/"evidence/vco1_circuit_listening.json"
    if meta_path.exists(): raise ValueError("preserve prior listening receipt")
    meta_path.write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(meta,indent=2))


if __name__=="__main__": main()
