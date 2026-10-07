"""Production chain gates, bound laboratory root equivalence and inherited scope."""
import hashlib,json,re,subprocess
from pathlib import Path
import mixer_chain_vectors as oracle
from mixer_on_native_vectors import ROOT,sha
from validate_mixer_on_native import native_source_identity

BASE='34825be259b454f724dbbf903025f53b2ec71d94'
OUTPUT=ROOT/'evidence/voice_mixer_chain_tests01.json'
LIB='crates/rf-d-circuit/src/lib.rs'

def main():
    if OUTPUT.exists():raise ValueError('preserve chain release QA')
    vp=ROOT/'evidence/voice_mixer_chain_vectors01.json';v=json.loads(vp.read_text(encoding='utf8'))
    boundp=ROOT/'evidence/voice_mixer_chain_vectors_validation01.json';bound=json.loads(boundp.read_text(encoding='utf8'))
    ap=ROOT/'evidence/voice_mixer_chain_native_attempt01.json';a=json.loads(ap.read_text(encoding='utf8'))
    pp=ROOT/'evidence/voice_mixer_chain_production01.json';p=json.loads(pp.read_text(encoding='utf8'))
    oldp=ROOT/'evidence/voice_mixer_c27_tests01.json';old=json.loads(oldp.read_text(encoding='utf8'))
    if not all(r['passed'] for r in (v,bound,a,p,old)):raise ValueError('required chain gates')
    cases,text=oracle.fixtures()
    if cases!=v['cases'] or text.encode()!=oracle.TEXT.read_bytes() or v['gates']!=oracle.GATES or v['rows']!=64:
        raise ValueError('full BUS/cursor trajectory replay')
    oldlib=subprocess.check_output(['git','show',BASE+':'+LIB],cwd=ROOT)
    if (ROOT/LIB).read_bytes()!=oldlib+b'\npub mod mixer_chain66;\n':raise ValueError('one public module export only')
    if a['source_sha256'][LIB]!=hashlib.sha256(oldlib).hexdigest():raise ValueError('laboratory root base')
    def rooted(match):
        name=match.group(1);return '#[path="'+(ROOT/f'crates/rf-d-circuit/src/{name}.rs').as_posix()+'"]\npub mod '+name+';'
    derived=re.sub(r'^pub mod (\w+);$',rooted,(ROOT/LIB).read_text(encoding='utf8'),flags=re.M).encode()
    private={}
    for attempt in (a,p):
        if not attempt['resource_passed'] or attempt['source_sha256']!=attempt['source_sha256_after'] or any(c['exit_code'] for c in attempt['commands']):raise ValueError('captured native chain commands')
        if attempt['estimated_build_bytes']!=64*1024**2 or attempt['margin_bytes']!=2*1024**3 or attempt['available_free_bytes']<attempt['estimated_build_bytes']+attempt['margin_bytes']:raise ValueError('compiler resource gate')
        for n,h in attempt['source_sha256'].items():
            if attempt is a and n==LIB:continue
            if sha(ROOT/n)!=h:raise ValueError('measured chain input changed '+n)
        compiler=attempt['compiler']
        if sha(Path(compiler['path']))!=compiler['sha256'] or attempt['compiler_sha256_after']!=compiler['sha256']:raise ValueError('chain compiler changed')
        for item in attempt['outputs']:
            path=ROOT/item['path']
            if not path.resolve().is_relative_to((ROOT/'references-local').resolve()) or sha(path)!=item['sha256'] or path.stat().st_size!=item['bytes']:raise ValueError('preserved chain artifact')
            private[item['path']]=item['sha256']
    root=ROOT/'references-local/mixer-chain-native01/lib.rs'
    if root.read_bytes()!=derived or sha(root)!=a['laboratory_root_sha256']:raise ValueError('production/laboratory root exact module-path transform')
    tests='\n'.join(c['stdout'] for c in p['commands'] if c['kind']=='test')
    if [c['kind'] for c in p['commands']]!=['compile','compile','test','compile','test'] or re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',tests)!=['3','1']:raise ValueError('four production tests')
    if 'CHAIN_ALLOCATION,steps=32,allocations=0' not in tests:raise ValueError('full chain heap gate')
    match=re.search(r'CHAIN_ORACLE,cases=4,steps=64,max_node_v=([^,\s]+),max_current_a=([^,\s]+)',tests)
    if not match:raise ValueError('captured chain maxima')
    maxima=dict(zip(('node_v','current_a'),map(float,match.groups())))
    if any(not 0<=x<oracle.GATES[n] for n,x in maxima.items()):raise ValueError('chain trajectory gates')
    changed=[]
    for n,h in old['source_sha256'].items():
        if sha(ROOT/n)==h:continue
        blob=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT);native_source_identity(n,h,blob);new=(ROOT/n).read_bytes()
        if n==LIB:
            if new!=blob+b'\npub mod mixer_chain66;\n':raise ValueError('inherited export only')
        elif n=='.gitattributes':
            extra=(b'/crates/rf-d-circuit/src/mixer_chain66.rs text eol=lf\n'
                   b'/crates/rf-d-circuit/tests/mixer_chain66.rs text eol=lf\n'
                   b'/crates/rf-d-circuit/tests/mixer_chain_no_alloc.rs text eol=lf\n'
                   b'/crates/rf-d-circuit/tests/support/mixer_chain_lab.rs text eol=lf\n'
                   b'/evidence/voice_mixer_chain_vectors01.txt -text\n')
            if new!=blob+extra:raise ValueError('only new chain byte policies')
        elif n in ('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'):
            head,body=blob.split(b'\n',1)
            if not new.startswith(head+b'\n\n') or not new.endswith(body.lstrip(b'\n')):raise ValueError('only chain summary prefix')
        else:raise ValueError('undeclared inherited change '+n)
        changed.append(n)
    for n,h in bound['source_sha256'].items():
        if n not in changed and sha(ROOT/n)!=h:raise ValueError('bound oracle input changed '+n)
    for n,h in old['private_input_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('historical private input changed')
        private[n]=h
    if sha(ROOT/old['previous_audio']['path'])!=old['previous_audio']['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=old['official_executable_sha256']:raise ValueError('historical audio/executable')
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(old['source_sha256'])|{oldp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=OUTPUT})
    sources={n:sha(ROOT/n) for n in names}
    for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    after={n:sha(ROOT/n) for n in names}
    if after!=sources:raise ValueError('chain publication inputs changed')
    OUTPUT.write_text(json.dumps(dict(schema='rf-d/mixer-chain-release/v1',passed=True,base_commit=BASE,
        source_sha256=sources,source_sha256_after=after,private_input_sha256=private,
        previous_qa_sha256=sha(oldp),oracle_sha256=sha(vp),oracle_bound_replay_sha256=sha(boundp),
        laboratory_attempt_sha256=sha(ap),production_attempt_sha256=sha(pp),numerical_maxima=maxima,
        cases=4,temporal_steps=64,covered_test_count=182,inherited_test_count=178,native_test_count=4,
        laboratory_tests_repeated_in_production=3,laboratory_repeats_counted_as_new_coverage=False,
        inherited_tests_reexecuted=False,zero_heap_steps=32,changed_inherited_inputs=sorted(changed),
        laboratory_root_transform_exact=True,previous_audio=old['previous_audio'],official_executable_sha256=old['official_executable_sha256'],
        new_spice_solves_by_this_block=0,new_audio=False,imposed_generators=True,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
    print('chain QA: 182 covered, 4 production tests, 178 inherited; sources',len(sources),flush=True)

if __name__=='__main__':main()
