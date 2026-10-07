"""Replay the independent C27 oracle; preserve native tests and inherited scope."""
import hashlib,json,re,subprocess
from pathlib import Path
import mixer_c27_vectors as oracle
from validate_mixer_on_native import native_source_identity

ROOT=oracle.ROOT
OUTPUT=ROOT/'evidence/voice_mixer_c27_tests01.json'
BASE='3e7ce511d3939b73789fdd788c77b5b679d6b7db'

def main():
    if OUTPUT.exists():raise ValueError('preserve C27 release QA')
    vp=ROOT/'evidence/voice_mixer_c27_vectors01.json';v=json.loads(vp.read_text(encoding='utf8'))
    if v['case_count']!=837 or v['precision_digits']!=80 or v['gates']!=oracle.GATES or v['source_sha256']!=v['source_sha256_after']:
        raise ValueError('C27 fixed prospective oracle')
    for n,h in v['source_sha256'].items():
        if oracle.sha(ROOT/n)!=h:raise ValueError('C27 oracle input changed '+n)
    if json.loads((ROOT/'evidence/filter_input_board4.json').read_text(encoding='utf8'))['parts']['C27']['farad']!=10e-6:
        raise ValueError('documentary C27 nominal')
    text,count=oracle.fixtures()
    if count!=837 or text.encode()!=oracle.CSV.read_bytes() or oracle.sha(oracle.CSV)!=v['vector_sha256']:
        raise ValueError('C27 full nodal replay')
    ap=ROOT/'evidence/voice_mixer_c27_native_attempt01.json';a=json.loads(ap.read_text(encoding='utf8'))
    if not a['passed'] or not a['resource_passed'] or a['source_sha256']!=a['source_sha256_after']:
        raise ValueError('native C27 attempt')
    if a['estimated_build_bytes']!=64*1024**2 or a['margin_bytes']!=2*1024**3 or a['available_free_bytes']<a['estimated_build_bytes']+a['margin_bytes']:
        raise ValueError('native C27 resource estimate')
    for n,h in a['source_sha256'].items():
        if oracle.sha(ROOT/n)!=h:raise ValueError('native C27 source changed '+n)
    if oracle.sha(Path(a['toolchain']['path']))!=a['toolchain']['sha256'] or a['toolchain_sha256_after']!=a['toolchain']['sha256']:
        raise ValueError('rustc changed')
    if [c['kind'] for c in a['commands']]!=['compile','compile','test','compile','test'] or any(c['exit_code']!=0 for c in a['commands']):
        raise ValueError('library and isolated test binaries')
    tests='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
    if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',tests)!=['4','1']:
        raise ValueError('five executed C27 tests')
    if 'C27_ALLOCATION,evaluations=10000,allocations=0' not in tests:raise ValueError('C27 heap gate')
    match=re.search(r'C27_ORACLE,cases=837,max_voltage_v=([^,\s]+),max_current_a=([^,\s]+),max_admittance_s=([^,\s]+)',tests)
    if not match:raise ValueError('C27 maxima capture')
    maxima=dict(zip(('voltage_v','current_a','admittance_s'),map(float,match.groups())))
    if any(not 0<=x<=oracle.GATES[n] for n,x in maxima.items()):raise ValueError('C27 numerical conformance')
    private={}
    if len(a['outputs'])!=3:raise ValueError('three preserved native binaries')
    for item in a['outputs']:
        p=ROOT/item['path']
        if not p.resolve().is_relative_to((ROOT/'references-local/mixer-c27-native01').resolve()) or oracle.sha(p)!=item['sha256'] or p.stat().st_size!=item['bytes']:
            raise ValueError('C27 binary identity')
        private[item['path']]=item['sha256']
    oldp=ROOT/'evidence/voice_mixer_on_native_tests02.json';old=json.loads(oldp.read_text(encoding='utf8'))
    if not old['passed']:raise ValueError('inherited mixer release rejected')
    changed=[]
    for n,h in old['source_sha256'].items():
        if oracle.sha(ROOT/n)==h:continue
        blob=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
        native_source_identity(n,h,blob)
        new=(ROOT/n).read_bytes()
        if n=='crates/rf-d-circuit/src/lib.rs':
            if new.count(b'pub mod mixer_c27;\n')!=1 or new.replace(b'pub mod mixer_c27;\n',b'',1)!=blob:raise ValueError('only C27 module export')
        elif n=='.gitattributes':
            extra=(b'/crates/rf-d-circuit/src/mixer_c27.rs text eol=lf\n'
                   b'/crates/rf-d-circuit/tests/mixer_c27.rs text eol=lf\n'
                   b'/crates/rf-d-circuit/tests/mixer_c27_no_alloc.rs text eol=lf\n'
                   b'/evidence/voice_mixer_c27_vectors01.txt -text\n')
            if new!=blob+extra:raise ValueError('only new C27 byte policies')
        elif n in ('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'):
            head,body=blob.split(b'\n',1)
            if not new.startswith(head+b'\n\n') or not new.endswith(body.lstrip(b'\n')):raise ValueError('only current summary prefix')
        else:raise ValueError('undeclared inherited source changed '+n)
        changed.append(n)
    if sorted(changed)!=sorted(('.gitattributes','crates/rf-d-circuit/src/lib.rs','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')):
        raise ValueError('declared five metadata/export changes')
    for n,h in old['private_input_sha256'].items():
        if oracle.sha(ROOT/n)!=h:raise ValueError('historical private input changed')
        private[n]=h
    if oracle.sha(ROOT/old['previous_audio']['path'])!=old['previous_audio']['sha256']:
        raise ValueError('historical audio changed')
    if oracle.sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=old['official_executable_sha256']:
        raise ValueError('official reference changed')
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(old['source_sha256'])|{oldp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=OUTPUT})
    sources={n:oracle.sha(ROOT/n) for n in names}
    for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    after={n:oracle.sha(ROOT/n) for n in names}
    if after!=sources:raise ValueError('publication inputs changed')
    report=dict(schema='rf-d/mixer-c27-release/v1',passed=True,base_commit=BASE,
        source_sha256=sources,source_sha256_after=after,private_input_sha256=private,
        previous_qa_sha256=oracle.sha(oldp),native_attempt_sha256=oracle.sha(ap),vector_receipt_sha256=oracle.sha(vp),
        numerical_maxima=maxima,case_count=837,native_test_count=5,covered_test_count=178,
        inherited_test_count=173,inherited_tests_reexecuted=False,zero_heap_evaluations=10000,
        changed_inherited_inputs=sorted(changed),new_spice_solves_by_this_block=0,new_audio=False,
        preserved_native_bytes=sum(x['bytes'] for x in a['outputs']),build_bytes_estimate_is_not_bound=True,
        previous_audio=old['previous_audio'],official_executable_sha256=old['official_executable_sha256'],
        full_ladder_integrated=False,physical_fidelity=False,real_time=False)
    OUTPUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('C27 QA: 178 covered, 5 executed, 173 inherited; sources',len(sources),flush=True)

if __name__=='__main__':main()
