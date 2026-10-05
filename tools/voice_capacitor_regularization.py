"""Finite series-resistance approximants to the retained zero-ESR circuit.

Epsilon is a numerical approximation parameter, not identified vintage ESR.
Its admission needs refinement toward zero and matched zero-ESR scenes.
"""
from dataclasses import replace
import gzip
import json
from pathlib import Path

import numpy as np
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT


def netlist(s,export,*,epsilon_ohm=.001):
    if not np.isfinite(epsilon_ohm) or epsilon_ohm<0:raise ValueError('finite nonnegative approximation resistance')
    text,meta=voice.netlist(s,export,linear_solver='klu')
    changes=[]
    for p in vco.read(voice.GRAPH)['capacitors']:
        if p['farad']<10e-6 or epsilon_ohm==0:continue
        ref=p['ref'];prefix='CF4_'+ref+' '
        old=[l for l in text.splitlines() if l.startswith(prefix)]
        if len(old)!=1:raise ValueError('unique original capacitor required')
        name,a,b,c=old[0].split()
        new=f'REPS_{ref} {a} EPS_{ref} {epsilon_ohm:.17g}\n{name} EPS_{ref} {b} {c}'
        text=text.replace(old[0],new,1)
        changes.append(dict(ref=ref,original_terminals=[a,b],farad=float(c),series_ohm=epsilon_ohm))
    meta.update(numerical_series_ohm=epsilon_ohm,regularized_capacitors=changes,
                identified_vintage_esr=False,zero_esr_limit=epsilon_ohm==0)
    meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
    return text,meta


def measure(raw,epsilon_ohm,settle_s=.02):
    m=voice.measure(raw,settle_s)
    a,b=m['reset_crossings_s'][-3],m['reset_crossings_s'][-1]
    cols={n:i+1 for i,n in enumerate(voice.VECTORS)}
    def values(n):return np.interp([a,b],raw[:,0],raw[:,cols['v(f4_'+n+')']])
    q17,right,main,hp=map(values,('q17_collector','c2_right','main_output','headphone_input'))
    current=(right-main)/1000+(right-hp)/1000
    capacitor_voltage=q17-right-epsilon_ohm*current
    change=float(10e-6*np.diff(capacitor_voltage)[0])
    m.update(c2_charge_change_c=change,c2_balance_absolute_c=abs(change-m['c2_delivered_c']),
             c2_series_drop_v=(epsilon_ohm*current).tolist())
    return m


def main():
    work=ROOT/'references-local/voice-reset/regularization01'
    output=ROOT/'evidence/voice_capacitor_regularization01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve prior bank')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    base=replace(voice.Scenario(),oscillator=replace(voice.Scenario().oscillator,duration_s=.01))
    report=dict(schema='rf-d/voice-capacitor-regularization/v1',epsilon_ohm=.001,cases={})
    for label,kw in [('nominal',{}),('cutoff-low',dict(cutoff_fraction=.2)),
                     ('contour-mute',dict(first_loudness_v=0)),('external-mute',dict(second_loudness_base_v=0))]:
        s=replace(base,**kw)
        try:
            raw,r=voice.run(s,label,work,exe,netlist_factory=netlist)
            report['cases'][label]=dict(receipt=r,measurements=measure(raw,.001,.002))
            print(label,'complete',round(r['wall_s'],2),'s',flush=True)
        except Exception as e:
            r=json.loads((work/(label+'.json')).read_text(encoding='utf-8'))
            report['cases'][label]=dict(receipt=r,error=str(e))
            print(label,'rejected',str(e),flush=True)
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))


if __name__=='__main__':main()
