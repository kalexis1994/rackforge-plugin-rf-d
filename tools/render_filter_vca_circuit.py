"""Measured VCO saw as an explicit boundary, loaded panel and board-4 audio.

No claim of a completed coupled VCO or full-duration WAV circuit solve.
The 80 ms electrical trace, its phase comparison and the repeated-cycle
listening adaptation have separate identities.
"""
from dataclasses import replace
import gzip
import json
import math
from pathlib import Path

import numpy as np

import filter_vca_circuit_reference as f
import voice_circuit_reference as voice
import vco1_circuit_reference as vco
from render_vco1_circuit import coefficients, synthesize, save

ROOT=f.ROOT
INPUT=ROOT/'references-local/filter-vca-circuit/listening01/input.txt'
INPUT_META=INPUT.with_suffix('.json')


def prepare():
    if INPUT.exists() or INPUT_META.exists(): raise ValueError('preserve prior input')
    validation=ROOT/'evidence/vco1_circuit_validation.json'
    if not vco.read(validation)['passed']: raise ValueError('audited VCO bank required')
    archive=ROOT/'evidence/vco1_circuit_convergence_v1.json.gz'
    bank=json.loads(gzip.decompress(archive.read_bytes()))
    case=bank['cases']['c4-10-gear125']
    path=ROOT/'references-local/vco1-circuit'/bank['bank']/'c4-10-gear125.txt'
    if vco.sha(path)!=case['receipt']['raw_export_sha256']: raise ValueError('VCO input digest mismatch')
    raw=np.loadtxt(path,skiprows=1)
    a,b=case['measurements']['reset_crossings_s'][-2:]
    knots=np.r_[a,raw[(raw[:,0]>a)&(raw[:,0]<b),0],b]
    phase=(knots-a)/(b-a);phase[0]=0;phase[-1]=1
    freq=1/(b-a)
    c=coefficients(phase,np.interp(knots,raw[:,0],raw[:,3]),52)
    # Synthesis here retains DC and has no fade/volts scaling: electrical source.
    time=np.r_[np.arange(0,.08,1/192000),.08]
    value=np.full_like(time,c[0].real)
    for n,co in enumerate(c[1:],1): value+=2*np.real(co*np.exp(2j*np.pi*n*freq*time))
    INPUT.parent.mkdir(parents=True,exist_ok=True)
    np.savetxt(INPUT,np.column_stack([time,value]),fmt='%.17g')
    meta=dict(schema='rf-d/filter-vca-measured-input/v1',frequency_hz=freq,
        original_raw_sha256=vco.sha(path),input_sha256=vco.sha(INPUT),source_archive_sha256=vco.sha(archive),
        harmonics=52,knot_rate_hz=192000,retained_dc_v=float(c[0].real),
        scope='measured selected saw voltage boundary, not re-solved loaded VCO',
        original_input_commit=case['receipt']['git_commit'],
        generator_sha256=vco.sha(Path(__file__)))
    INPUT_META.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    return meta


def netlist(s,export):
    text,meta=f.netlist(s,export)
    inp=vco.read(INPUT_META)
    if vco.sha(INPUT)!=inp['input_sha256']: raise ValueError('frozen electrical input changed')
    raw=np.loadtxt(INPUT)
    pairs=[f'{t:.17g} {v:.17g}' for t,v in raw]
    waveform='Vfixture FIXTURE 0 PWL(\n'+'\n'.join('+ '+' '.join(pairs[i:i+8]) for i in range(0,len(pairs),8))+'\n+)'
    old=f'Vfixture FIXTURE 0 SIN(0 {s.amplitude_v:.17g} {s.frequency_hz:.17g})'
    if old not in text: raise ValueError('sine fixture replacement failed')
    text=text.replace(old,waveform,1)
    old=f'Rfixture FIXTURE MIX_BUS_BOARD4_PIN4 {s.source_ohm:.17g}'
    text=text.replace(old,'R6panel_high FIXTURE PANEL_WIPER 12500\nR6panel_low PANEL_WIPER 0 12500\nR45panel PANEL_WIPER MIX_BUS_BOARD4_PIN4 33000',1)
    meta.update(input_port=inp,panel=dict(r6_ohm=25000,level_fraction=.5,r45_ohm=33000),
                input_waveform='bandlimited measured VCO cycle, piecewise linear electrical source')
    for p in (INPUT,INPUT_META,Path(__file__),ROOT/'tools/render_vco1_circuit.py'):
        meta['source_sha256'][p.relative_to(ROOT).as_posix()]=vco.sha(p)
    return text,meta


def output_cycle(raw,frequency):
    b=raw[-1,0];a=b-1/frequency
    phase=np.linspace(0,1,1025)
    col=f.VECTORS.index('v(f4_main_output)')+1
    last=np.interp(a+phase/frequency,raw[:,0],raw[:,col])
    prior=np.interp(a+(phase-1)/frequency,raw[:,0],raw[:,col])
    difference=float(np.max(np.abs(last-prior)))
    if difference>.005: raise ValueError('cycle repetition gate failed')
    knots=np.r_[a,raw[(raw[:,0]>a)&(raw[:,0]<b),0],b]
    p=(knots-a)*frequency;p[0]=0;p[-1]=1
    voltage=np.interp(knots,raw[:,0],raw[:,col])
    return coefficients(p,voltage,math.floor(.45*48000/frequency)),difference


def main():
    inp=vco.read(INPUT_META)
    if INPUT_META.exists() and inp['input_sha256']!=vco.sha(INPUT): raise ValueError('input integrity')
    output=ROOT/'artifacts/filter-vca-circuit'
    output.mkdir(parents=True,exist_ok=True)
    receipt_path=ROOT/'evidence/filter_vca_circuit_listening.json'
    if receipt_path.exists(): raise ValueError('preserve earlier listening receipt')
    meta=dict(schema='rf-d/filter-vca-listening/v1',input=inp,scenes={},
        sample_rate_hz=48000,volts_per_full_scale=8,dc_removed=True,fade_s=.01,
        full_duration_spice_render=False,full_coupled_voice=False,physical_fidelity=False)
    parts=[]
    try:
        for label,cutoff in [('cerrado',.2),('medio',.5),('abierto',.8)]:
            base=f.Scenario()
            s=replace(base,frequency_hz=inp['frequency_hz'],board=replace(base.board,
                cutoff_fraction=cutoff,oscillator=replace(base.oscillator,max_step_s=1e-6)))
            exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
            raw,receipt=voice.run(s,label,INPUT.parent,exe,netlist_factory=netlist,vectors=f.VECTORS)
            measured=f.measure(raw,s)
            c,difference=output_cycle(raw,s.frequency_hz)
            audio=synthesize(c,s.frequency_hz,duration=.75)
            path=output/f'rf-d-filtro-vca-{label}.wav'
            save(path,audio,48000)
            meta['scenes'][label]=dict(receipt=receipt,measurements=measured,
                prior_cycle_difference_v=difference,removed_dc_v=float(c[0].real),
                audio_path=path.relative_to(ROOT).as_posix(),audio_sha256=vco.sha(path))
            parts.extend([audio,np.zeros(7200)])
            print(label,'complete',measured['output_ac_rms_v'],flush=True)
        montage=output/'rf-d-filtro-vca-cerrado-medio-abierto.wav'
        save(montage,np.concatenate(parts[:-1]),48000)
        meta['montage']=dict(path=montage.relative_to(ROOT).as_posix(),sha256=vco.sha(montage))
        meta['passed']=True
    except Exception as e:
        meta.update(passed=False,error=type(e).__name__+': '+str(e))
        raise
    finally:
        receipt_path.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
