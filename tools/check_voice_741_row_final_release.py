"""Reconcile two summary edits while inheriting byte-identical successful tests."""
import json,re,subprocess
from pathlib import Path
import numpy as np
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT
BASE='61d937d8de03103755fe72e4359396c4122a7b20'
CHANGED={'docs/MATRIZ_DE_FIDELIDAD.md','docs/741_FILA_REDUCIDA_RESULTADOS.md'}


def main():
    output=ROOT/'evidence/voice_741_row_tests02.json'
    if output.exists():raise ValueError('preserve final QA')
    path=ROOT/'evidence/voice_741_row_tests01.json';old=vco.read(path)
    if not old['passed'] or old['source_sha256']!=old['source_sha256_after']:raise ValueError('successful immutable QA required')
    for name,digest in old['source_sha256'].items():
        source_identity(name,digest,subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT))
        if name not in CHANGED and vco.sha(ROOT/name)!=digest:raise ValueError('tested input changed')
    inputs=set(old['source_sha256'])|{'evidence/voice_741_row_tests01.json',Path(__file__).relative_to(ROOT).as_posix()}
    before={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    receipt=vco.read(ROOT/'evidence/voice_741_row_runs01.json')['records']['row-on-constant']
    raw=ROOT/'references-local/voice-circuit/newton-build05/runs/row-on-constant.txt'
    if vco.sha(raw)!=receipt['raw_export_sha256']:raise ValueError('failed trajectory identity')
    a=np.loadtxt(raw,skiprows=1,ndmin=2);events=vco.crossings(a[:,0],a[:,1],-2.,True)
    if len(events)!=1 or not events[0]<a[-1,0]:raise ValueError('first reset underway before failure')
    targets=[]
    for name in ('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','docs/741_FILA_REDUCIDA_PROTOCOLO.md',
                 'docs/741_FILA_REDUCIDA_RESULTADOS.md','docs/NEWTON_MATRIZ_COMPLETA_PROTOCOLO.md'):
        p=ROOT/name
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#')):continue
            target=(p.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target!=output:raise ValueError('missing document target')
            targets.append(target)
    if vco.sha(ROOT/old['previous_audio']['path'])!=old['previous_audio']['sha256']:raise ValueError('prior audio changed')
    official=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
    if vco.sha(official)!=old['official_executable_sha256']:raise ValueError('official binary changed')
    after={n:vco.sha(ROOT/n) for n in sorted(inputs)}
    if before!=after:raise ValueError('final QA inputs changed')
    report=dict(schema='rf-d/741-row-final-release/v1',passed=True,tests_count=old['tests_count'],runs=old['runs'],
                inherited_qa_sha256=vco.sha(path),inherited_base_commit=BASE,new_tests_during_final_qa=0,
                source_sha256=before,source_sha256_after=after,changed_summaries=sorted(CHANGED),
                reset_wording_correction=dict(first_minus2v_crossing_s=float(events[0]),last_accepted_s=float(a[-1,0]),
                    raw_sha256=receipt['raw_export_sha256'],meaning='failure during the first reset, after the first -2 V crossing'),
                previous_audio=old['previous_audio'],official_executable_sha256=old['official_executable_sha256'],
                local_document_links=len(targets),new_solves_during_qa=0,candidate_admitted_locally=False,
                coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    if not all(p.exists() for p in targets):raise ValueError('final self-link missing')
    print('50 successful regressions inherited by unchanged code/test bytes; reset wording corrected')


if __name__=='__main__':main()
