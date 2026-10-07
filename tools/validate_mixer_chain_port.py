"""Loaded-port oracle replay, production conformance and inherited identities."""
import json,re,subprocess
from pathlib import Path
from mixer_on_native_vectors import ROOT,sha
from validate_mixer_on_native import native_source_identity
import mixer_chain_port_vectors as oracle

BASE='3271a3fc5043e8c7e3361d8a1fc850d10d28ea22'
OUTPUT=ROOT/'evidence/voice_mixer_chain_port_tests01.json'

def main():
    if OUTPUT.exists():raise ValueError('preserve loaded-port QA')
    oldp=ROOT/'evidence/voice_mixer_chain_tests01.json';old=json.loads(oldp.read_text(encoding='utf8'))
    vp=oracle.OUTPUT;v=json.loads(vp.read_text(encoding='utf8'))
    ap=ROOT/'evidence/voice_mixer_chain_port_native01.json';a=json.loads(ap.read_text(encoding='utf8'))
    if not all(x['passed'] for x in (old,v,a)) or v['source_sha256']!=v['source_sha256_after'] or a['source_sha256']!=a['source_sha256_after']:
        raise ValueError('loaded-port admitted inputs')
    cases,text=oracle.fixtures()
    if cases!=v['cases'] or text.encode()!=oracle.TEXT.read_bytes() or sha(oracle.TEXT)!=v['text_sha256'] or v['fd_source_delta_v']!=.001 or v['case_count']!=4:raise ValueError('full nodal source FD replay')
    changed=[]
    for n,h in old['source_sha256'].items():
        if sha(ROOT/n)==h:continue
        blob=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT);native_source_identity(n,h,blob);new=(ROOT/n).read_bytes()
        if n=='crates/rf-d-circuit/src/lib.rs':
            if new!=blob+b'\npub mod mixer_chain_port;\n':raise ValueError('one loaded-port export')
        elif n=='.gitattributes':
            extra=(b'/crates/rf-d-circuit/src/mixer_chain_port.rs text eol=lf\n'
                   b'/crates/rf-d-circuit/tests/mixer_chain_port.rs text eol=lf\n'
                   b'/crates/rf-d-circuit/tests/mixer_chain_port_no_alloc.rs text eol=lf\n'
                   b'/evidence/voice_mixer_chain_port_vectors01.txt -text\n')
            if new!=blob+extra:raise ValueError('loaded-port byte policies only')
        elif n in ('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'):
            head,body=blob.split(b'\n',1)
            if not new.startswith(head+b'\n\n') or not new.endswith(body.lstrip(b'\n')):raise ValueError('loaded-port summary prefix only')
        else:raise ValueError('undeclared inherited source change '+n)
        changed.append(n)
    for n,h in v['source_sha256'].items():
        if n not in changed and sha(ROOT/n)!=h:raise ValueError('source FD oracle changed '+n)
    for n,h in a['source_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('executed native source changed '+n)
    if not a['resource_passed'] or a['estimated_build_bytes']!=64*1024**2 or a['margin_bytes']!=2*1024**3 or a['available_free_bytes']<a['estimated_build_bytes']+a['margin_bytes']:raise ValueError('compiler resource estimate')
    if sha(Path(a['compiler']['path']))!=a['compiler']['sha256'] or a['compiler_sha256_after']!=a['compiler']['sha256']:raise ValueError('compiler identity')
    if [c['kind'] for c in a['commands']]!=['compile','compile','test','compile','test'] or any(c['exit_code'] for c in a['commands']):raise ValueError('production commands')
    tests='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
    if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',tests)!=['2','1'] or 'LOADED_PORT_ALLOCATION,solves=16,allocations=0' not in tests:raise ValueError('three production tests / heap')
    m=re.search(r'LOADED_PORT,cases=4,max_admittance_delta_s=([^,\s]+),max_node_gradient_delta=([^,\s]+)',tests)
    if not m or not 0<=float(m[1])<1e-8 or not 0<=float(m[2])<1e-6:raise ValueError('loaded-port captured maxima')
    private=dict(old['private_input_sha256'])
    for item in a['outputs']:
        p=ROOT/item['path']
        if not p.resolve().is_relative_to((ROOT/'references-local/mixer-chain-port-native01').resolve()) or sha(p)!=item['sha256'] or p.stat().st_size!=item['bytes']:raise ValueError('preserved port binary')
        private[item['path']]=item['sha256']
    for n,h in private.items():
        if sha(ROOT/n)!=h:raise ValueError('private identity '+n)
    if sha(ROOT/old['previous_audio']['path'])!=old['previous_audio']['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=old['official_executable_sha256']:raise ValueError('historical audio / executable')
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(old['source_sha256'])|{oldp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=OUTPUT})
    sources={n:sha(ROOT/n) for n in names}
    for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    after={n:sha(ROOT/n) for n in names}
    if after!=sources:raise ValueError('loaded-port publication source change')
    OUTPUT.write_text(json.dumps(dict(schema='rf-d/mixer-chain-loaded-port-release/v1',passed=True,base_commit=BASE,
        source_sha256=sources,source_sha256_after=after,private_input_sha256=private,
        previous_qa_sha256=sha(oldp),native_attempt_sha256=sha(ap),oracle_sha256=sha(vp),cases=4,
        numerical_maxima=dict(admittance_s=float(m[1]),node_gradient=float(m[2])),covered_test_count=185,
        native_test_count=3,inherited_test_count=182,inherited_tests_reexecuted=False,zero_heap_port_solves=16,
        changed_inherited_inputs=sorted(changed),previous_audio=old['previous_audio'],official_executable_sha256=old['official_executable_sha256'],
        new_spice_solves_by_this_block=0,new_audio=False,physical_fidelity=False,real_time=False,imposed_generators=True),indent=2)+'\n',encoding='utf8',newline='\n')
    print('loaded port QA: 185 covered, 3 executed; sources',len(sources),flush=True)

if __name__=='__main__':main()
