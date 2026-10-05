"""Numerical interventions after the electrical-decoupling experiment."""
from dataclasses import replace
import gzip
import json
from pathlib import Path

import numpy as np
import voice_reset_isolation as isolate
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT
CASES={'coupled-be':('coupled',(),False,1),
       'decoupled-be':('board-decoupled',(),False,1),
       'coupled-newtrunc':('coupled',(),True,2)}
for ref in ('C9','C24','C15','C4'):
    CASES['decoupled-without-'+ref.lower()]=('board-decoupled',(ref,),False,2)


def factory(label):
    variant,removed,newtrunc,order=CASES[label]
    def build(s,export):
        text,meta=isolate.factory(variant)(s,export)
        if removed:
            text='\n'.join(l for l in text.splitlines() if not any(l.startswith('CF4_'+r+' ') for r in removed))+'\n'
        if newtrunc:
            text=text.replace('.options ','.options newtrunc ltereltol=1e-7 lteabstol=1e-8 ltetrtol=1 ',1)
        meta.update(numerical_intervention=label,removed_capacitors=list(removed),newtrunc=newtrunc)
        meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
        return text,meta
    return build


def main():
    work=ROOT/'references-local/voice-reset/numerical01'
    output=ROOT/'evidence/voice_reset_numerical01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve prior bank')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    report=dict(schema='rf-d/voice-reset-numerical/v1',cases={})
    for label,(_,_,_,order) in CASES.items():
        s=replace(voice.Scenario(),oscillator=replace(voice.Scenario().oscillator,
            duration_s=.01,order=order,method='trap' if order==1 else 'gear'))
        try:
            raw,r=voice.run(s,label,work,exe,netlist_factory=factory(label),vectors=vco.VECTORS)
            report['cases'][label]=dict(receipt=r,measurements=vco.measure(raw,.002))
            print(label,'complete',flush=True)
        except Exception as e:
            r=json.loads((work/(label+'.json')).read_text(encoding='utf-8'))
            case=dict(receipt=r,error=str(e))
            if (work/(label+'.txt')).exists():
                raw=np.loadtxt(work/(label+'.txt'),skiprows=1)
                case['partial_end_s']=float(raw[-1,0])
            report['cases'][label]=case
            print(label,'rejected',case.get('partial_end_s'),flush=True)
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))


if __name__=='__main__':main()
