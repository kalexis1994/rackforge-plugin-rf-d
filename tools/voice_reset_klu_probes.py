"""Compare another linear backend without changing circuit or tolerances."""
from dataclasses import replace
import gzip
import json
from pathlib import Path
import voice_reset_isolation as isolate
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT


def factory(variant):
    def build(s,export):
        text,meta=isolate.factory(variant)(s,export)
        text=text.replace('.options ','.options klu ',1)
        meta.update(linear_solver='klu',all_discrete_capacitors_retained=True)
        meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
        return text,meta
    return build


def main():
    work=ROOT/'references-local/voice-reset/klu01'
    output=ROOT/'evidence/voice_reset_klu01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve prior bank')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    s=replace(voice.Scenario(),oscillator=replace(voice.Scenario().oscillator,duration_s=.01))
    report=dict(schema='rf-d/voice-reset-klu/v1',cases={})
    for variant in ('isolated','board-decoupled','coupled'):
        try:
            raw,r=voice.run(s,variant,work,exe,netlist_factory=factory(variant),vectors=vco.VECTORS)
            log=(work/(variant+'.log')).read_text(encoding='utf-8')
            if 'KLU' not in log:raise ValueError('KLU execution not confirmed')
            report['cases'][variant]=dict(receipt=r,measurements=vco.measure(raw,.002))
            print(variant,'complete',flush=True)
        except Exception as e:
            r=json.loads((work/(variant+'.json')).read_text(encoding='utf-8'))
            report['cases'][variant]=dict(receipt=r,error=str(e))
            print(variant,'rejected',str(e),flush=True)
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))


if __name__=='__main__':main()
