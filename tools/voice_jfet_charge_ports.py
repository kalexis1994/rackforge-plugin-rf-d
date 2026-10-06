"""Equivalent level-1 laboratory JFET charge ports, fixed at TNOM=25 C.

Channel, junction conduction and gmin remain in the original NJF primitive.
Only CGS/CGD memory moves to explicit Q(V) capacitor ports. Diagnostic only.
"""
from dataclasses import replace
import gzip
import json
import math
from pathlib import Path
import numpy as np
import voice_circuit_reference as voice
import voice_circuit_probes as probes
import vco1_circuit_reference as vco

ROOT=vco.ROOT
PORT_GATES=dict(current_absolute_a=1e-9,current_relative=1e-6,integrated_difference_c=1e-14)


def charge(v,c0,pb=1,fc=.5):
    if not all(math.isfinite(x) for x in (v,c0,pb,fc)) or c0<=0 or pb<=0 or not 0<fc<1:
        raise ValueError('finite charge domain required')
    vc=fc*pb
    if v<vc:return 2*pb*c0*(1-math.sqrt(1-v/pb))
    d=v-vc
    return 2*pb*c0*(1-math.sqrt(1-fc))+c0/math.sqrt(1-fc)*d+c0/(4*pb*(1-fc)**1.5)*d*d


def charge_expression(gate,other,c0,pb,fc):
    # max protects the inactive square-root branch; never changes selected law.
    x=f'v({gate},{other})';vc=fc*pb
    q0=2*pb*c0*(1-math.sqrt(1-fc));slope=c0/math.sqrt(1-fc)
    quadratic=c0/(4*pb*(1-fc)**1.5)
    return (f'{x}<{vc:.17g} ? {2*pb*c0:.17g}*(1-sqrt(max(1-{x}/{pb:.17g},{1-fc:.17g}))) : '
            f'{q0:.17g}+{slope:.17g}*({x}-{vc:.17g})+{quadratic:.17g}*({x}-{vc:.17g})^2')


def split(text):
    device=vco.read(vco.DEVICES);card=device['jfet']
    if device['temperature_c']!=25 or card['TNOM']!=25 or card['LEVEL']!=1 or card['RD'] or card['RS']:
        raise ValueError('only registered zero-series-resistance 25C card supported')
    lines=[];ports=[];models=0
    for line in text.splitlines():
        if line.startswith('.model LAB_E402 NJF('):
            zero=dict(card,CGS=0,CGD=0)
            line='.model LAB_E402 NJF('+' '.join(f'{k}={v:.17g}' for k,v in zero.items())+')';models+=1
        lines.append(line)
        if line.startswith('J') and line.split()[-1]=='LAB_E402':
            ref,drain,gate,source,_=line.split()
            for suffix,other,c0 in [('gs',source,card['CGS']),('gd',drain,card['CGD'])]:
                expr=charge_expression(gate,other,c0,card['PB'],card['FC'])
                lines.append(f"Ccharge_{ref}_{suffix} {gate} {other} Q='{expr}'")
                ports.append(dict(ref=ref,gate=gate,other=other,capacitance_zero_f=c0,
                                  charge_law='level1-depletion-m=.5-forward-quadratic'))
    if models!=1 or not ports:raise ValueError('registered model and ports required')
    return '\n'.join(lines)+'\n',ports


def factory(s,export):
    text,meta=voice.netlist(s,export,linear_solver='klu');text,ports=split(text)
    if len(ports)!=4:raise ValueError('both E402 halves and four charge ports required')
    meta.update(jfet_charge_ports=ports,charge_memory_representation='explicit-Q',
                diagnostic_only=True,all_physical_charge_laws_retained=True)
    meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
    return text,meta


BENCH_VECTORS=['v(g_a)','v(d_a)','v(s_a)','i(vg_a)','i(vd_a)','i(vs_a)',
               'i(vg_b)','i(vd_b)','i(vs_b)']


def benchmark_netlist(s,export):
    card=vco.read(vco.DEVICES)['jfet'];full=' '.join(f'{k}={v:.17g}' for k,v in card.items())
    pieces=['RF-D level1 JFET equivalent charge port comparison',f'.model LAB_E402 NJF({full})',
            f'.model REFERENCE NJF({full})']
    for name in ('a','b'):
        pieces += [f'Vg_{name} g_{name} 0 PWL(0 -1 2u -.1 4u .65 6u -1 10u -3 14u .65 20u -1)',
                   f'Vd_{name} d_{name} 0 SIN(.2 1.5 100k)',f'Vs_{name} s_{name} 0 0']
    pieces += ['Ja d_a g_a s_a REFERENCE','Jb d_b g_b s_b LAB_E402']
    text,ports=split('\n'.join(pieces)+'\n')
    text += f'''.options klu bypass=0 itl4=100 temp=25 tnom=25 method=gear maxord=2 reltol=1e-7 abstol=1e-13 vntol=1e-8 gmin=1e-12
.save {' '.join(BENCH_VECTORS)}
.control
set numdgt=17
set wr_singlescale
set wr_vecnames
tran {s.oscillator.max_step_s:.17g} {s.oscillator.duration_s:.17g} 0 {s.oscillator.max_step_s:.17g}
wrdata {export.as_posix()} {' '.join(BENCH_VECTORS)}
quit
.endc
.end
'''
    return text,dict(source_sha256={vco.DEVICES.relative_to(ROOT).as_posix():vco.sha(vco.DEVICES),
                    Path(__file__).relative_to(ROOT).as_posix():vco.sha(Path(__file__))},
                    jfet_charge_ports=ports)


def validate_benchmark(raw):
    t=raw[:,0];details={}
    for label,a,b in [('gate',4,7),('drain',5,8),('source',6,9)]:
        diff=np.abs(raw[:,a]-raw[:,b]);limit=PORT_GATES['current_absolute_a']+PORT_GATES['current_relative']*np.abs(raw[:,a])
        integral=np.cumsum(np.diff(t)*((raw[:-1,a]-raw[:-1,b])+(raw[1:,a]-raw[1:,b]))/2)
        peak=float(np.max(np.abs(integral)))
        details[label]=dict(max_current_difference_a=float(diff.max()),max_current_ratio=float((diff/limit).max()),
                            max_integrated_difference_c=peak)
        if np.any(diff>limit) or peak>PORT_GATES['integrated_difference_c']:
            raise ValueError('equivalent terminal port comparison rejected: '+label)
    return details


def main():
    work=ROOT/'references-local/voice-circuit/jfet-ports01'
    output=ROOT/'evidence/voice_jfet_charge_ports01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve prior experiment')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    report=dict(schema='rf-d/voice-jfet-charge-ports/v1',bank=work.name,
                port_gates=PORT_GATES,voice_gates=probes.GATES,cases={},full_bank_passed=False)
    s=voice.Scenario();s=replace(s,oscillator=replace(s.oscillator,duration_s=20e-6,max_step_s=5e-9))
    try:
        raw,r=voice.run(s,'terminal-benchmark',work,exe,netlist_factory=benchmark_netlist,vectors=BENCH_VECTORS)
        report['benchmark']=dict(receipt=r,measurements=validate_benchmark(raw),passed=True)
        print('terminal benchmark passed',flush=True)
    except Exception as e:
        report['benchmark']=dict(receipt=vco.read(work/'terminal-benchmark.json'),passed=False,error=str(e))
        print('terminal benchmark rejected',str(e),flush=True)
    if report['benchmark']['passed']:
        for label in ('external-mute','contour-mute','cutoff-low','nominal125'):
            try:
                raw,r=voice.run(probes.scenes()[label],label,work,exe,netlist_factory=factory)
                report['cases'][label]=dict(receipt=r,measurements=voice.measure(raw))
                print(label,'complete',round(r['wall_s'],2),flush=True)
            except Exception as e:
                r=vco.read(work/(label+'.json'));case=dict(receipt=r,error=str(e))
                if (work/(label+'.txt')).exists():
                    raw=np.loadtxt(work/(label+'.txt'),skiprows=1,ndmin=2);case['last_clock_s']=float(raw[-1,0])
                report['cases'][label]=case
                print(label,'rejected',case.get('last_clock_s'),flush=True)
            output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))


if __name__=='__main__':main()
