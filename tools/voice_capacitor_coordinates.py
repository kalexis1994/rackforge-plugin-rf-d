"""Exact ideal-capacitor port realization in centered voltage coordinates.

u = Va - Vb - offset; Iab = C du/dt = C d(Va-Vb)/dt.
The constant offset is a coordinate choice, not ESR or a sound parameter.
The internal capacitor is driven by a VCVS and reflected by a CCCS.
"""
from dataclasses import asdict, replace
import gzip
import json
from pathlib import Path

import numpy as np
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT
OFFSETS={'C9':10.,'C24':2.,'C15':6.,'C4':-1.,'C27':-1.,'C10':6.,'C2':3.}


def port(ref,a,b,cap,offset):
    if not np.isfinite([cap,offset]).all() or cap<=0:raise ValueError('finite coordinate and positive capacitance required')
    return [f'Ecoord_{ref} COORD_PRE_{ref} 0 {a} {b} 1',
            f'Vcoord_{ref} COORD_PRE_{ref} COORD_{ref} {offset:.17g}',
            f'CF4_{ref} COORD_{ref} 0 {cap:.17g}',
            f'Fcoord_{ref} {a} {b} Vcoord_{ref} 1']


def netlist(s,export,*,linear_solver='klu'):
    text,meta=voice.netlist(s,export,linear_solver=linear_solver)
    caps={p['ref']:p for p in vco.read(voice.GRAPH)['capacitors']}
    changes=[]
    for ref,offset in OFFSETS.items():
        prefix='CF4_'+ref+' '
        original=[l for l in text.splitlines() if l.startswith(prefix)]
        if len(original)!=1:raise ValueError('unique physical capacitor required')
        _,a,b,c=original[0].split()
        if float(c)!=caps[ref]['farad']:raise ValueError('physical capacitance changed')
        text=text.replace(original[0],'\n'.join(port(ref,a,b,float(c),offset)),1)
        changes.append(dict(ref=ref,physical_terminals=[a,b],farad=float(c),offset_v=offset))
    meta.update(capacitor_coordinates=changes,coordinate_scope='exact ideal two-terminal port, constant charge reference offset, consistent DC initialization')
    meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
    return text,meta


def capacitor_benchmark(s,export):
    # Both independent terminal realizations share ideal voltage boundaries.
    lines=['Centered capacitor two-terminal equivalence benchmark',
           'Va A 0 SIN(2 .1 440)','Vb B 0 1','Cdirect A B 220u']
    lines+=port('BENCH','A','B',220e-6,1.)
    vectors=['v(a,b)','@cdirect[i]','@cf4_bench[i]']
    lines += ['.options method=trap maxord=1 reltol=1e-7 abstol=1e-13 vntol=1e-8',
        '.save '+' '.join(vectors),'.control','set numdgt=17','set wr_singlescale','set wr_vecnames',
        f'tran {s.oscillator.max_step_s:.17g} {s.oscillator.duration_s:.17g} 0 {s.oscillator.max_step_s:.17g}',
        f"wrdata {export.as_posix()} {' '.join(vectors)}",'quit','.endc','.end','']
    return '\n'.join(lines),dict(schema='rf-d/capacitor-coordinate-benchmark/v1',scenario=asdict(s),
        source_sha256={Path(__file__).relative_to(ROOT).as_posix():vco.sha(Path(__file__))})


def main():
    work=ROOT/'references-local/voice-reset/coordinates01'
    output=ROOT/'evidence/voice_capacitor_coordinates01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve prior bank')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    report=dict(schema='rf-d/voice-capacitor-coordinates/v1',cases={})
    base=replace(voice.Scenario(),oscillator=replace(voice.Scenario().oscillator,duration_s=.01))
    raw,r=voice.run(base,'linear-port',work,exe,netlist_factory=capacitor_benchmark,
                   vectors=['v(a,b)','@cdirect[i]','@cf4_bench[i]'])
    delta=np.diff(raw[:,0]);expected=220e-6*np.diff(raw[:,1])/delta
    matched=float(np.max(np.abs(raw[1:,2]-raw[1:,3])))
    be_error=float(np.max(np.abs(raw[1:,3]-expected)))
    report['linear_port']=dict(receipt=r,peak_port_difference_a=matched,
        peak_backward_euler_current_error_a=be_error,passed=matched<=1e-8 and be_error<=1e-8)
    print('linear port',matched,be_error,report['linear_port']['passed'],flush=True)
    if report['linear_port']['passed']:
        for label,kw in [('nominal',{}),('cutoff-low',dict(cutoff_fraction=.2)),
                          ('contour-mute',dict(first_loudness_v=0)),('external-mute',dict(second_loudness_base_v=0))]:
            s=replace(base,**kw)
            try:
                raw,r=voice.run(s,label,work,exe,netlist_factory=netlist)
                report['cases'][label]=dict(receipt=r,measurements=voice.measure(raw,.002))
                print(label,'complete',flush=True)
            except Exception as e:
                r=json.loads((work/(label+'.json')).read_text(encoding='utf-8'))
                report['cases'][label]=dict(receipt=r,error=str(e))
                print(label,'rejected',str(e),flush=True)
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))


if __name__=='__main__':main()
