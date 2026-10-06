"""Frozen numerical refinement and controls for the loaded loudness circuit."""
from dataclasses import asdict,replace
import gzip
import json
import math
from pathlib import Path
import numpy as np
import loudness_board4_circuit as circuit
import vco1_circuit_reference as vco

ROOT=vco.ROOT
GATES=dict(trace_v=.005,rms_relative=.01,rms_absolute_v=10e-6,charge_c=.1e-9,
           observation_grid_s=20e-6)
PAIRS=(('nominal8','nominal4'),('nominal4','nominal2'),('nominal2','nominal-trap2'))


def temporal(s,step,method='gear'):
    return replace(s,audio=replace(s.audio,board=replace(s.audio.board,
        oscillator=replace(s.oscillator,max_step_s=step,method=method))))


def scenes():
    s=circuit.Scenario();fine=temporal(s,2e-6)
    bank=dict(nominal8=s,nominal4=temporal(s,4e-6),nominal2=fine,
              **{'nominal-trap2':temporal(s,2e-6,'trap')})
    for label,kw in [('attack1000',dict(attack_ohm=1000)),('decay10000',dict(decay_ohm=10000)),
                     ('sustain1000',dict(sustain_lower_ohm=1000)),('final-decay-off',dict(final_decay=False)),
                     ('trigger4700',dict(trigger_base_ohm=4700)),('reset1000',dict(reset_pullup_ohm=1000))]:
        bank[label]=replace(fine,controls=replace(fine.controls,**kw))
    return bank


def contrast(a,b,sa,sb):
    if sa.oscillator.duration_s!=sb.oscillator.duration_s:raise ValueError('matching clocks required')
    t=np.arange(0,sa.oscillator.duration_s+GATES['observation_grid_s']/2,GATES['observation_grid_s'])
    differences={}
    for node in ('v(e2_timing_c2)','v(f4_loudness_contour)','v(f4_main_output)'):
        xa=np.interp(t,a[:,0],a[:,sa.vectors.index(node)+1])
        xb=np.interp(t,b[:,0],b[:,sb.vectors.index(node)+1])
        differences[node]=float(np.max(np.abs(xa-xb)))
        if not np.isfinite(xa).all() or not np.isfinite(xb).all() or differences[node]>GATES['trace_v']:
            raise ValueError('loaded envelope temporal trace contrast rejected')
    ma,mb=circuit.measure(a,sa),circuit.measure(b,sb);rms={}
    for label in ma['windows']:
        x,y=[m['windows'][label]['output_ac_rms_v'] for m in (ma,mb)]
        limit=GATES['rms_absolute_v']+GATES['rms_relative']*y
        rms[label]=dict(difference_v=abs(x-y),limit_v=limit)
        if not math.isfinite(x+y) or abs(x-y)>limit:raise ValueError('loaded envelope RMS contrast rejected')
    return dict(max_trace_difference_v=differences,output_window_rms=rms)


def factory(s,export):
    text,meta=circuit.netlist(s,export)
    meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
    return text,meta


def main():
    import voice_circuit_reference as voice
    work=ROOT/'references-local/voice-circuit/loudness-board4-bank01'
    output=ROOT/'evidence/loudness_board4_bank01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve previous bank')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    report=dict(schema='rf-d/loudness-board4-bank/v1',bank=work.name,gates=GATES,
        cases={},comparisons={},passed=False,physical_fidelity=False,real_time=False,
        vco_electrically_coupled=False)
    observed={}
    for label,s in scenes().items():
        try:
            raw,r=voice.run(s,label,work,exe,netlist_factory=factory,vectors=s.vectors,timeout=120)
            m=circuit.measure(raw,s)
            if r['source_sha256']!=r['source_sha256_after']:raise ValueError('input mutated')
            if m['timing_balance_max_c']>GATES['charge_c'] or m['output_balance_max_c']>GATES['charge_c']:
                raise ValueError('cumulative charge balance rejected')
            report['cases'][label]=dict(receipt=r,measurements=m)
            if label.startswith('nominal'):observed[label]=raw
            print(label,'complete',round(r['wall_s'],2),m['contour_max_v'],flush=True)
        except Exception as e:
            r=vco.read(work/(label+'.json'));case=dict(receipt=r,error=str(e))
            if 'raw' in locals():case['last_clock_s']=float(raw[-1,0])
            report['cases'][label]=case;print(label,'rejected',str(e),flush=True)
        output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
        if 'raw' in locals():del raw
    try:
        if set(report['cases'])!=set(scenes()) or any(c.get('error') for c in report['cases'].values()):
            raise ValueError('complete accepted scene bank required')
        bank=scenes()
        for a,b in PAIRS:report['comparisons'][a+'--'+b]=contrast(observed[a],observed[b],bank[a],bank[b])
        report['passed']=True
    except Exception as e:report['validation_error']=str(e)
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print('bank passed',report['passed'],report.get('validation_error'),flush=True)


if __name__=='__main__':main()
