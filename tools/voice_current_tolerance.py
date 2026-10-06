"""Predeclared absolute-current tolerance candidates, unchanged circuit/gates.

Selection is numerical only. Historical strict bank remains rejected.
Stop a screening candidate at its first rejected scene; preserve all attempts.
"""
from dataclasses import replace
import gzip
import json
from pathlib import Path
import numpy as np
import voice_circuit_reference as voice
import voice_circuit_probes as probes
import vco1_circuit_reference as vco

ROOT=vco.ROOT
CANDIDATES=(1e-12,1e-11,1e-10)
ORDER=('external-mute','contour-mute','cutoff-low','nominal125')


def factory(abstol):
    if abstol not in CANDIDATES:raise ValueError('predeclared current tolerance required')
    def build(s,export):
        text,meta=voice.netlist(s,export,linear_solver='klu')
        if text.count('abstol=1e-13')!=1:raise ValueError('baseline current tolerance mismatch')
        text=text.replace('abstol=1e-13',f'abstol={abstol:.17g}')
        meta.update(absolute_current_tolerance_a=abstol,numerical_candidate=True,
                    physical_components_changed=False)
        meta['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=vco.sha(Path(__file__))
        return text,meta
    return build


def attempt(s,label,work,abstol):
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    try:
        raw,r=voice.run(s,label,work,exe,netlist_factory=factory(abstol))
        if 'Using KLU as Direct Linear Solver' not in (work/(label+'.log')).read_text(encoding='utf-8'):
            raise ValueError('backend unconfirmed')
        m=voice.measure(raw)
        if m['c2_balance_absolute_c']>probes.GATES['c2_charge_c']:
            raise ValueError('output charge balance rejected')
        case=dict(receipt=r,measurements=m)
        print(label,'complete',round(r['wall_s'],2),flush=True)
    except Exception as e:
        r=vco.read(work/(label+'.json'))
        case=dict(receipt=r,error=type(e).__name__+': '+str(e))
        if (work/(label+'.txt')).exists():
            raw=np.loadtxt(work/(label+'.txt'),skiprows=1,ndmin=2)
            case.update(last_clock_s=float(raw[-1,0]),rows=len(raw))
        print(label,'rejected',case.get('last_clock_s'),flush=True)
    return case


def save(path,report):
    path.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))


def main():
    work=ROOT/'references-local/voice-circuit/current-screen01'
    output=ROOT/'evidence/voice_current_tolerance_screen01.json.gz'
    if work.exists() or output.exists():raise ValueError('preserve previous screening')
    report=dict(schema='rf-d/voice-current-tolerance-screen/v1',bank=work.name,
        candidates_a=list(CANDIDATES),scene_order=list(ORDER),gates=probes.GATES,
        cases={},selected_a=None,full_bank_passed=False)
    for abstol in CANDIDATES:
        cases={};report['cases'][format(abstol,'.0e')]=cases
        for label in ORDER:
            cases[label]=attempt(probes.scenes()[label],label+'-'+format(abstol,'.0e'),work,abstol)
            save(output,report)
            if cases[label].get('error'):break
        if len(cases)==len(ORDER) and all(not c.get('error') for c in cases.values()):
            report['selected_a']=abstol;break
    save(output,report)
    print('selected',report['selected_a'],flush=True)


if __name__=='__main__':main()
