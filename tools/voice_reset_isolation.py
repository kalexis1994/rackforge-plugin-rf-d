"""Factorial reset diagnosis: electrical loading vs common solver clock.

Fixtures are interventions, not proposed changes to the vintage circuit.
All failed trajectories and the exact generating source remain preserved.
"""
from dataclasses import replace, asdict
import gzip
import json
from pathlib import Path

import numpy as np
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT
VARIANTS=('isolated','resistive','capacitive','board-decoupled','board-decoupled-no-bulk-caps','coupled')


def factory(variant):
    if variant not in VARIANTS: raise ValueError('declared intervention required')
    def build(s,export):
        if variant.startswith('board-') or variant=='coupled':
            text,meta=voice.netlist(s,export)
            if variant.startswith('board-'):
                old='CF4_C27 MIX_BUS_BOARD4_PIN4 F4_BASE_Q29'
                if text.count(old)!=1:raise ValueError('input coupling branch mismatch')
                text=text.replace(old,'CF4_C27 BOARD4_DIAGNOSTIC_BUS F4_BASE_Q29')
                additions='Vmixer MIX_BUS_BOARD4_PIN4 0 0\nVboard_fixture BOARD4_DIAGNOSTIC_BUS 0 0\n'
                text=text.replace('.options ',additions+'.options ',1)
            if variant.endswith('no-bulk-caps'):
                text='\n'.join(l for l in text.splitlines() if not l.startswith('CF4_'))+'\n'
        else:
            text,meta=vco.netlist(s.oscillator,export)
            if variant!='isolated':
                text='\n'.join(l for l in text.splitlines() if not l.startswith('Vmixer '))+'\n'
                if variant=='resistive':
                    additions='Rdiagnostic MIX_BUS_BOARD4_PIN4 0 470\n'
                else:
                    additions='Cdiagnostic MIX_BUS_BOARD4_PIN4 DIAGNOSTIC_LOAD 10u\nRdiagnostic DIAGNOSTIC_LOAD DIAGNOSTIC_BIAS 470\nVdiagnostic DIAGNOSTIC_BIAS 0 2\n'
                text=text.replace('.options ',additions+'.options ',1)
            text=text.replace('.options ','.options bypass=0 itl4=100 ',1)
        # Observe the same VCO vectors in every factorial branch.
        lines=[]
        for line in text.splitlines():
            if line.startswith('.save '):line='.save '+' '.join(vco.VECTORS)
            elif line.startswith('wrdata '):line=f"wrdata {export.as_posix()} {' '.join(vco.VECTORS)}"
            lines.append(line)
        meta.update(intervention=variant,diagnostic_only=True,scenario=asdict(s))
        meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
        return '\n'.join(lines)+'\n',meta
    return build


def main():
    work=ROOT/'references-local/voice-reset/isolation01'
    output=ROOT/'evidence/voice_reset_isolation01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve previous bank')
    s=replace(voice.Scenario(),oscillator=replace(voice.Scenario().oscillator,duration_s=.01))
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    report=dict(schema='rf-d/voice-reset-isolation/v1',cases={})
    for label in VARIANTS:
        try:
            raw,r=voice.run(s,label,work,exe,netlist_factory=factory(label),vectors=vco.VECTORS)
            report['cases'][label]=dict(receipt=r,measurements=vco.measure(raw,settle_s=.002))
            print(label,'complete',flush=True)
        except Exception as e:
            r=json.loads((work/(label+'.json')).read_text(encoding='utf-8'))
            case=dict(receipt=r,error=str(e))
            if (work/(label+'.txt')).exists():
                raw=np.loadtxt(work/(label+'.txt'),skiprows=1)
                case['partial_end_s']=float(raw[-1,0])
                case['partial_rows']=len(raw)
            report['cases'][label]=case
            print(label,'rejected',case.get('partial_end_s'),flush=True)
    output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))


if __name__=='__main__':main()
