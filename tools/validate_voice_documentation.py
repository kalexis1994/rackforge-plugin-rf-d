"""Consolidate current documentation while retaining exact historical QA inputs."""
import json,re,subprocess
from pathlib import Path
from mixer_on_native_vectors import ROOT,sha
from validate_mixer_on_native import native_source_identity

OUTPUT=ROOT/'evidence/voice_documentation_tests01.json'
def main():
    if OUTPUT.exists():raise ValueError('preserve documentation publication')
    qp=ROOT/'evidence/voice_mixer_chain_port_tests01.json';q=json.loads(qp.read_text(encoding='utf8'))
    sp=ROOT/'evidence/voice_documentation_snapshot01.json';snapshot=json.loads(sp.read_text(encoding='utf8'))
    if not q['passed'] or snapshot['previous_qa_sha256']!=sha(qp) or snapshot['algorithms_changed'] or snapshot['numerical_gates_changed']:
        raise ValueError('previous release and snapshot lineage')
    originals={}
    for entry in snapshot['entries']:
        n=entry['original_path'];backup=ROOT/entry['snapshot_path']
        if sha(backup)!=q['source_sha256'][n] or sha(backup)!=entry['original_sha256'] or entry['snapshot_sha256']!=entry['original_sha256'] or not entry['exact_bytes'] or not entry['relative_link_base_preserved'] or backup.parent!=(ROOT/n).parent:
            raise ValueError('exact historical snapshot '+n)
        originals[n]=entry['snapshot_path']
    if set(originals)!={'README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'}:raise ValueError('three portadas only')
    for n,h in q['source_sha256'].items():
        if n not in originals and sha(ROOT/n)!=h:raise ValueError('non-documentary protected input changed '+n)
    local=[]
    for n in originals:
        path=ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf8')):
            if link.startswith(('https:','http:','#')):continue
            target=(path.parent/link.split('#')[0].strip('<>')).resolve()
            if not target.exists() and target!=OUTPUT.resolve():raise ValueError('missing current documentation target '+link)
            local.append(target.relative_to(ROOT).as_posix())
    for n,h in q['private_input_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('historical private input changed')
    if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=q['official_executable_sha256']:raise ValueError('historical audio/executable')
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(q['source_sha256'])|{qp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=OUTPUT})
    sources={n:sha(ROOT/n) for n in names}
    for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    after={n:sha(ROOT/n) for n in names}
    if after!=sources:raise ValueError('documentation publication changed')
    OUTPUT.write_text(json.dumps(dict(schema='rf-d/documentation-release/v1',passed=True,
        source_sha256=sources,source_sha256_after=after,previous_qa_sha256=sha(qp),snapshot_sha256=sha(sp),
        changed_documentary_inputs=originals,checked_local_targets=sorted(set(local)),
        covered_test_count=185,native_test_count=0,inherited_test_count=185,inherited_tests_reexecuted=False,
        algorithms_changed=False,numerical_gates_changed=False,private_input_sha256=q['private_input_sha256'],
        previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],
        new_spice_solves_by_documentation=0,new_compiler_runs=0,new_audio=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
    print('documentation QA: 185 inherited; protected inputs',len(sources),'local targets',len(set(local)),flush=True)

if __name__=='__main__':main()
