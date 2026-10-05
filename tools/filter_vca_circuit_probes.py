"""Frozen finite-scene convergence and control bank for independent board 4."""
from dataclasses import replace
import argparse
import gzip
import json
from pathlib import Path

import filter_vca_circuit_reference as f
import vco1_circuit_reference as vco

GATES=dict(extrema_v=.005,rms_relative=.01,rms_absolute_v=10e-6,c2_balance_c=.1e-9)


def scenes():
    base=f.Scenario()
    fine=replace(base,board=replace(base.board,oscillator=replace(base.oscillator,max_step_s=1e-6)))
    bank={'nominal2':base,'nominal1':fine,
          'nominal-trap1':replace(fine,board=replace(fine.board,oscillator=replace(fine.oscillator,method='trap')))}
    for label,kw in [('cutoff-low',dict(cutoff_fraction=.2)),('cutoff-high',dict(cutoff_fraction=.8)),
        ('contour-mute',dict(first_loudness_v=0)),('contour1',dict(first_loudness_v=1)),
        ('contour4',dict(first_loudness_v=4)),('external-mute',dict(second_loudness_base_v=0)),
        ('emphasis5000',dict(emphasis_ohm=5000)),('emphasis0',dict(emphasis_ohm=0)),
        ('load10000',dict(main_load_ohm=10000)),('r61-alternate',dict(r61_ohm=200000))]:
        bank[label]=replace(fine,board=replace(fine.board,**kw))
    for hz in (110,440,1760,7040): bank['small-'+str(hz)]=replace(fine,frequency_hz=hz,amplitude_v=.001)
    for label,amplitude in [('drive1',1),('drive10',10)]: bank[label]=replace(fine,amplitude_v=amplitude)
    return bank


def validate(report):
    expected=scenes()
    if set(report['cases'])!=set(expected): raise ValueError('complete frozen scene bank required')
    if report['gates']!=GATES: raise ValueError('declared gates changed')
    from dataclasses import asdict
    for label,s in expected.items():
        case=report['cases'][label]
        if case.get('error'): raise ValueError('scene failed: '+label)
        r=case['receipt']
        if r['scenario']!=asdict(s) or not r['trajectory_complete']:
            raise ValueError('scene configuration or completeness mismatch: '+label)
        if r['source_sha256']!=r['source_sha256_after']:
            raise ValueError('source mutated during solve')
        if case['measurements']['c2_balance_absolute_c']>GATES['c2_balance_c']:
            raise ValueError('C2 integrated charge balance failed: '+label)
    comparisons={}
    for a,b in [('nominal2','nominal1'),('nominal1','nominal-trap1')]:
        ma,mb=[report['cases'][name]['measurements'] for name in (a,b)]
        worst=max(abs(ma['windows'][node][metric]-mb['windows'][node][metric])
                  for node in ('v(mix_bus_board4_pin4)','v(f4_recover_collector)','v(f4_main_output)')
                  for metric in ('min','max'))
        rms=abs(ma['output_ac_rms_v']-mb['output_ac_rms_v'])
        limit=GATES['rms_absolute_v']+GATES['rms_relative']*mb['output_ac_rms_v']
        passed=worst<=GATES['extrema_v'] and rms<=limit
        comparisons[a+'--'+b]=dict(max_extrema_difference_v=worst,output_rms_difference_v=rms,rms_limit_v=limit,passed=passed)
        if not passed: raise ValueError('finite convergence contrast failed')
    return comparisons


def main():
    p=argparse.ArgumentParser();p.add_argument('--bank',required=True);args=p.parse_args()
    if not args.bank or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in args.bank):
        raise ValueError('safe bank name required')
    work=f.ROOT/'references-local/filter-vca-circuit'/args.bank
    output=f.ROOT/'evidence'/('filter_vca_circuit_'+args.bank+'.json.gz')
    if work.exists() or output.exists(): raise ValueError('preserve earlier bank')
    report=dict(schema='rf-d/filter-vca-circuit-bank/v1',bank=args.bank,gates=GATES,cases={},passed=False)
    exe=f.ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    for label,s in scenes().items():
        try:
            raw,receipt=f.run(s,label,work,exe)
            report['cases'][label]=dict(receipt=receipt,measurements=f.measure(raw,s))
            print(label,'complete',round(receipt['wall_s'],3),'s',flush=True)
        except Exception as e:
            receipt=json.loads((work/(label+'.json')).read_text()) if (work/(label+'.json')).exists() else {}
            report['cases'][label]=dict(receipt=receipt,error=type(e).__name__+': '+str(e))
            print(label,'rejected',str(e),flush=True)
    try:
        report['comparisons']=validate(report);report['passed']=True
    except Exception as e: report['validation_error']=str(e)
    payload=(json.dumps(report,indent=2)+'\n').encode()
    output.write_bytes(gzip.compress(payload,compresslevel=9,mtime=0))
    print(json.dumps(dict(passed=report['passed'],error=report.get('validation_error'),output=str(output)),indent=2))
    if not report['passed']: raise SystemExit(1)


if __name__=='__main__': main()
