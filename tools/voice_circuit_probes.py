"""Coupled conditional voice finite validation with all capacitor branches."""
from dataclasses import asdict, replace
import gzip
import json
from pathlib import Path

import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT
GATES=dict(frequency_cents=1,extrema_v=.005,rms_relative=.01,rms_absolute_v=10e-6,c2_charge_c=.1e-9)


def scenes():
    base=voice.Scenario()
    fine=replace(base,oscillator=replace(base.oscillator,max_step_s=.125e-6))
    return {'nominal500':base,
        'nominal250':replace(base,oscillator=replace(base.oscillator,max_step_s=.25e-6)),
        'nominal125':fine,
        'nominal-trap125':replace(fine,oscillator=replace(fine.oscillator,method='trap')),
        'cutoff-low':replace(fine,cutoff_fraction=.2),
        'cutoff-high':replace(fine,cutoff_fraction=.8),
        'contour-mute':replace(fine,first_loudness_v=0),
        'external-mute':replace(fine,second_loudness_base_v=0),
        'triangle':replace(fine,oscillator=replace(fine.oscillator,upper_contact=1,lower_contact=8)),
        'pulse-narrow':replace(fine,oscillator=replace(fine.oscillator,upper_contact=4,lower_contact=12)),
        'load10000':replace(fine,main_load_ohm=10000)}


def netlist(s,export):
    text,meta=voice.netlist(s,export,linear_solver='klu')
    meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
    return text,meta


def validate(report):
    if report['gates']!=GATES or set(report['cases'])!=set(scenes()):
        raise ValueError('unchanged gates and complete bank required')
    for label,s in scenes().items():
        case=report['cases'][label]
        if case.get('error'):raise ValueError('scene rejected: '+label)
        r,m=case['receipt'],case['measurements']
        if r['scenario']!=asdict(s) or not r['trajectory_complete'] or r['linear_solver']!='klu':
            raise ValueError('scene/solver identity mismatch')
        if r['source_sha256']!=r['source_sha256_after']:raise ValueError('source changed during solve')
        if m['c2_balance_absolute_c']>GATES['c2_charge_c']:raise ValueError('output charge balance')
    contrasts={}
    for a,b in [('nominal500','nominal250'),('nominal250','nominal125'),('nominal125','nominal-trap125')]:
        ma,mb=[report['cases'][k]['measurements'] for k in (a,b)]
        cents=abs(1200*__import__('math').log2(ma['frequency_hz']/mb['frequency_hz']))
        extrema=max(abs(ma['windows'][node][metric]-mb['windows'][node][metric])
            for node in ('v(mix_bus_board4_pin4)','v(f4_recover_collector)','v(f4_main_output)')
            for metric in ('min','max'))
        rms=abs(ma['output_ac_rms_v']-mb['output_ac_rms_v'])
        limit=GATES['rms_absolute_v']+GATES['rms_relative']*mb['output_ac_rms_v']
        passed=cents<=GATES['frequency_cents'] and extrema<=GATES['extrema_v'] and rms<=limit
        contrasts[a+'--'+b]=dict(frequency_cents=cents,max_extrema_difference_v=extrema,
                              output_rms_difference_v=rms,rms_limit_v=limit,passed=passed)
        if not passed:raise ValueError('finite contrast rejected: '+a+'--'+b)
    return contrasts


def main():
    work=ROOT/'references-local/voice-circuit/klu-bank01'
    output=ROOT/'evidence/voice_circuit_klu_bank01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve prior bank')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    report=dict(schema='rf-d/voice-circuit-bank/v1',bank=work.name,gates=GATES,cases={},passed=False)
    for label,s in scenes().items():
        try:
            raw,r=voice.run(s,label,work,exe,netlist_factory=netlist)
            if 'KLU' not in (work/(label+'.log')).read_text(encoding='utf-8'):
                raise ValueError('linear backend execution unconfirmed')
            report['cases'][label]=dict(receipt=r,measurements=voice.measure(raw))
            print(label,'complete',round(r['wall_s'],2),'s',flush=True)
        except Exception as e:
            r=json.loads((work/(label+'.json')).read_text(encoding='utf-8'))
            report['cases'][label]=dict(receipt=r,error=str(e))
            print(label,'rejected',str(e),flush=True)
    try:
        report['contrasts']=validate(report);report['passed']=True
    except Exception as e:report['validation_error']=str(e)
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print('passed',report['passed'],report.get('validation_error'),flush=True)


if __name__=='__main__':main()
