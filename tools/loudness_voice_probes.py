"""Frozen first coupling screen and finite contrasts; no hardware claim."""
from dataclasses import replace
import gzip,json,math
from pathlib import Path
import numpy as np
import loudness_voice_circuit as c
import vco1_circuit_reference as vco

ROOT=vco.ROOT
GATES=dict(trace_v=.005,frequency_cents=1,rms_relative=.01,rms_absolute_v=10e-6,
           charge_c=.1e-9,observation_grid_s=5e-6)
PAIRS=(('nominal500','nominal250'),('nominal250','nominal125'),('nominal125','nominal-trap125'))


def temporal(s,step,method='gear'):
    return replace(s,board=replace(s.board,oscillator=replace(s.oscillator,max_step_s=step,method=method)))


def scenes():
    base=c.Scenario()
    return dict(nominal500=base,nominal250=temporal(base,.25e-6),nominal125=temporal(base,.125e-6),
        **{'nominal-trap125':temporal(base,.125e-6,'trap')})


def contrast(a,b,sa,sb):
    t=np.arange(0,sa.oscillator.duration_s+GATES['observation_grid_s']/2,GATES['observation_grid_s'])
    differences={}
    for n in ('v(e2_timing_c2)','v(f4_loudness_contour)','v(mix_bus_board4_pin4)',
              'v(f4_recover_collector)','v(f4_main_output)'):
        x=np.interp(t,a[:,0],a[:,sa.vectors.index(n)+1]);y=np.interp(t,b[:,0],b[:,sb.vectors.index(n)+1])
        differences[n]=float(np.max(np.abs(x-y)))
        if not np.isfinite(x+y).all() or differences[n]>GATES['trace_v']:raise ValueError('trace contrast rejected')
    ma,mb=c.measurement(a,sa),c.measurement(b,sb)
    cents=abs(1200*math.log2(ma['frequency_hz']/mb['frequency_hz']))
    if cents>GATES['frequency_cents']:raise ValueError('frequency contrast rejected')
    rms={}
    for label in ma['windows']:
        x,y=[m['windows'][label]['output_ac_rms_v'] for m in (ma,mb)]
        limit=GATES['rms_absolute_v']+GATES['rms_relative']*y
        rms[label]=dict(difference_v=abs(x-y),limit_v=limit)
        if not math.isfinite(x+y) or abs(x-y)>limit:raise ValueError('RMS contrast rejected')
    return dict(max_trace_difference_v=differences,frequency_cents=cents,output_window_rms=rms)


def factory(s,export):
    text,meta=c.netlist(s,export)
    meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
    return text,meta


def main():
    work=ROOT/'references-local/voice-circuit/loudness-voice-screen01'
    output=ROOT/'evidence/loudness_voice_screen01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve prior screen')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    report=dict(schema='rf-d/loudness-voice-screen/v1',bank=work.name,gates=GATES,cases={},comparisons={},passed=False)
    kept={}
    for label,s in scenes().items():
        try:
            raw,r=c.run(s,label,work,exe,factory=factory)
            m=c.measurement(raw,s)
            if r['source_sha256']!=r['source_sha256_after']:raise ValueError('source changed')
            if max(m['timing_balance_max_c'],m['output_balance_max_c'])>GATES['charge_c']:raise ValueError('charge balance')
            report['cases'][label]=dict(receipt=r,measurements=m);kept[label]=raw
            print(label,'complete',round(r['wall_s'],2),flush=True)
        except Exception as e:
            r=vco.read(work/(label+'.json'));case=dict(receipt=r,error=str(e))
            if (work/(label+'.txt')).exists():
                raw=np.loadtxt(work/(label+'.txt'),skiprows=1,ndmin=2);case['last_clock_s']=float(raw[-1,0])
            report['cases'][label]=case;print(label,'rejected',case.get('last_clock_s'),flush=True)
        output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    try:
        if any(case.get('error') for case in report['cases'].values()):raise ValueError('coupling screen rejected')
        ss=scenes()
        for a,b in PAIRS:report['comparisons'][a+'--'+b]=contrast(kept[a],kept[b],ss[a],ss[b])
        report['passed']=True
    except Exception as e:report['validation_error']=str(e)
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print('screen passed',report['passed'],report.get('validation_error'),flush=True)


if __name__=='__main__':main()
