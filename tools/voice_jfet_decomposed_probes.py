"""Terminal equivalence, unchanged positive control, then preserved failing VCO."""
from dataclasses import asdict,replace
import copy,gzip,json,math
from pathlib import Path
import numpy as np
import voice_jfet_decomposed as model
import voice_jfet_charge_ports as bench
import voice_port_probes as ports
import voice_port_relaxation as p
import voice_circuit_reference as voice
import loudness_voice_circuit as coupled
import vco1_circuit_reference as vco

ROOT=vco.ROOT
GATES=dict(terminal=bench.PORT_GATES,trace_v=.005,frequency_cents=1,
           reset_time_s=10e-9,observation_grid_s=5e-6)


def benchmark(s,export):
    text,_=bench.benchmark_netlist(s,export)
    # Recover a full primitive for the candidate; the earlier benchmark split
    # its charge only. Keep the independent REFERENCE device untouched.
    lines=[line for line in text.splitlines() if not line.startswith('Ccharge_')]
    card=vco.read(vco.DEVICES)['jfet'];full=' '.join(f'{k}={v:.17g}' for k,v in card.items())
    lines=[f'.model LAB_E402 NJF({full})' if l.startswith('.model LAB_E402 ') else l for l in lines]
    deck,manifest=model.decompose('\n'.join(lines)+'\n')
    return deck,dict(scenario=asdict(s),decomposed_jfets=manifest,source_sha256={path.relative_to(ROOT).as_posix():vco.sha(path)
        for path in (vco.DEVICES,Path(model.__file__),Path(bench.__file__),Path(__file__))})


def historical_factory(label):
    bank=json.loads(gzip.decompress((ROOT/'evidence/voice_port_behavioral01.json.gz').read_bytes()))
    r=next(k['vco_receipt'] for k in bank['cases']['fixed-contour-control']['iterations'] if k['vco_receipt']['label']==label)
    path=ROOT/'references-local/voice-circuit'/bank['bank']/(label+'.cir')
    if vco.sha(path)!=r['deck_sha256']:raise ValueError('frozen reproduction deck identity')
    def generate(s,export):
        if asdict(s)!=r['scenario']:raise ValueError('reproduction scenario identity')
        text=path.read_text(encoding='utf-8')
        old_export=ROOT/'references-local/voice-circuit'/bank['bank']/(label+'.txt')
        marker='wrdata '+old_export.as_posix()+' '
        if text.count(marker)!=1:raise ValueError('frozen export identity')
        text=text.replace(marker,'wrdata '+export.as_posix()+' ',1)
        text,manifest=model.decompose(text)
        for name,digest in r['source_sha256'].items():
            if vco.sha(ROOT/name)!=digest:raise ValueError('historical generation input changed: '+name)
        meta=dict(scenario=asdict(s),source_sha256=copy.deepcopy(r['source_sha256']),decomposed_jfets=manifest,
            reproduced_deck_sha256=r['deck_sha256'],reproduced_commit=r['git_commit'],
            reproduced_label=label,diagnostic_only=True)
        for path in (Path(model.__file__),Path(__file__)):
            meta['source_sha256'][path.relative_to(ROOT).as_posix()]=vco.sha(path)
        return text,meta
    return generate,r


def contrast(raw,reference):
    t=np.arange(0,.04+GATES['observation_grid_s']/2,GATES['observation_grid_s']);diff={}
    for i,n in enumerate(p.VCO_VECTORS,1):
        if n=='i(vmixer)':continue
        diff[n]=float(np.max(np.abs(np.interp(t,raw[:,0],raw[:,i])-np.interp(t,reference[:,0],reference[:,i]))))
    edge=lambda r:vco.crossings(r[:,0],r[:,1],-2,True)
    a,b=edge(raw),edge(reference)
    if len(a)!=len(b) or len(a)<5:raise ValueError('reset count mismatch')
    lag=float(np.max(np.abs(a-b)))
    cents=abs(1200*math.log2(ports.frequency(raw[:,0],raw[:,1])/ports.frequency(reference[:,0],reference[:,1])))
    return dict(max_trace_difference_v=diff,frequency_cents=cents,max_reset_time_difference_s=lag,
        passed=max(diff.values())<=GATES['trace_v'] and cents<=GATES['frequency_cents'] and lag<=GATES['reset_time_s'])


def main():
    work=ROOT/'references-local/voice-circuit/jfet-decomposed01';output=ROOT/'evidence/voice_jfet_decomposed01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve previous experiment')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    report=dict(schema='rf-d/jfet-decomposed-screen/v1',bank=work.name,gates=GATES,cases={},passed=False,
                coupling_admitted=False,physical_fidelity=False,real_time=False)
    def save():output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    s=coupled.Scenario();small=replace(s,board=replace(s.board,oscillator=replace(s.oscillator,duration_s=20e-6,max_step_s=5e-9)))
    jobs=[('terminal-benchmark',small,benchmark,bench.BENCH_VECTORS),
          ('constant-control',s,historical_factory('fixed-contour-control-01-vco')[0],p.VCO_VECTORS),
          ('returned-bus',s,historical_factory('fixed-contour-control-03-vco')[0],p.VCO_VECTORS)]
    for label,scenario,fn,vectors in jobs:
        try:
            raw,r=voice.run(scenario,label,work,exe,netlist_factory=fn,vectors=vectors,timeout=120)
            case=dict(receipt=r,passed=True);report['cases'][label]=case
            if r['source_sha256']!=r['source_sha256_after']:raise ValueError('source changed')
            if label=='terminal-benchmark':case['measurements']=bench.validate_benchmark(raw)
            elif label=='constant-control':
                path=ROOT/'references-local/voice-circuit/port-behavioral01/fixed-contour-control-01-vco.txt'
                old=json.loads(gzip.decompress((ROOT/'evidence/voice_port_behavioral01.json.gz').read_bytes()))['cases']['fixed-contour-control']['iterations'][0]['vco_receipt']
                if vco.sha(path)!=old['raw_export_sha256']:raise ValueError('positive control raw identity')
                case['contrast']=contrast(raw,np.loadtxt(path,skiprows=1,ndmin=2))
                if not case['contrast']['passed']:raise ValueError('positive control contrast rejected')
            else:case['frequency_hz']=ports.frequency(raw[:,0],raw[:,1])
            save();print(label,'passed',round(r['wall_s'],2),flush=True)
        except Exception as e:
            r=vco.read(work/(label+'.json'));case=report['cases'].setdefault(label,dict(receipt=r))
            case.update(passed=False,error=str(e));report['validation_error']=label+' rejected; remaining jobs not measured'
            if (work/(label+'.txt')).exists():case['last_clock_s']=float(np.loadtxt(work/(label+'.txt'),skiprows=1,ndmin=2)[-1,0])
            save();print(label,'rejected',str(e),flush=True);return
    report['passed']=True;save()


if __name__=='__main__':main()
