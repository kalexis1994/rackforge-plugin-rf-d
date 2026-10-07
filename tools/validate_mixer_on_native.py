"""Audit targeted native port conformance and release input identities."""
import json,re,subprocess
from pathlib import Path
import mixer_on_native_vectors as oracle
from validate_loudness_board4_bank import source_identity

ROOT=oracle.ROOT
OUTPUT=ROOT/'evidence/voice_mixer_on_native_validation01.json'
CHECKOUT_PAIRS={
    'crates/rf-d-circuit/src/output_conversion.rs':('8573df31148f234f7b475a39232de9d5e1e1beffd8bbac11c882e40661fd8414','5e31ddc65a5843fea7c511e865c89a9658a0e1effe72983c2d8b6079fb7ffde5'),
    'crates/rf-d-circuit/src/output_conversion_c4.rs':('629865a4df9f1e2a2ee2e5b8f83b36c780db6facdb964b399a7819102be630af','1958d33bfb6b3b7f010902d89ad31a8a6c3d5f97c9aa4c441d0090557138bbad'),
    'crates/rf-d-circuit/src/recovery_vca_output.rs':('fb544899240d0ef5775e78e7f6868a6146c723195b646a6967aeef5982596a60','da9dd0c8f466587a7abd16b4a6af0de9521756fe28c3f7cd6e7e194c2e72a4d1'),
    'crates/rf-d-circuit/src/vca2_output.rs':('9107d32bbaab38542683f1df99d33893c9a9ae77c5452d17be60f8970836086d','e47591b0310e72da3978c65d1c7392acc3998c244b2e507128f9195d4454297f')}

def native_source_identity(name,digest,blob):
    import hashlib
    pair=CHECKOUT_PAIRS.get(name)
    if pair and (hashlib.sha256(blob).hexdigest(),digest)==pair and hashlib.sha256(blob.replace(b'\n',b'\r\n')).hexdigest()==digest:
        return 'explicit-existing-Rust-CRLF-pair'
    return source_identity(name,digest,blob)

def main():
    if OUTPUT.exists():raise ValueError('preserve mixer native validation')
    vectors=ROOT/'evidence/voice_mixer_on_vectors01.json';f=json.loads(vectors.read_text(encoding='utf-8'))
    if f['source_sha256']!=f['source_sha256_after'] or f['gates']!=oracle.GATES or f['case_count']!=279 or f['precision_digits']!=80:
        raise ValueError('fixed independent oracle inputs')
    for n,h in f['source_sha256'].items():
        if oracle.sha(ROOT/n)!=h:raise ValueError('oracle source changed')
    cases,maxima,worst=oracle.fixtures()
    if cases!=f['cases'] or maxima!=f['legacy_maxima'] or worst!=f['legacy_worst_cases'] or not f['legacy_bus_comparison_passed']:
        raise ValueError('full resistor-oracle replay')
    attemptp=ROOT/'evidence/voice_mixer_on_native_attempt01.json';r=json.loads(attemptp.read_text(encoding='utf-8'))
    if not r['passed'] or r['exit_code']!=0 or not r['process_started'] or not r['resource_passed'] or r['source_sha256']!=r['source_sha256_after']:
        raise ValueError('native attempt gate')
    if r['required_free_bytes']!=r['estimated_build_bytes']+2*1024**3 or r['available_free_bytes']<r['required_free_bytes'] or r['wall_limit_s']!=900 or r['wall_s']>900:
        raise ValueError('native attempt resources')
    for n,h in r['source_sha256'].items():
        if oracle.sha(ROOT/n)!=h:raise ValueError('executed native source changed')
    for n,t in r['toolchain'].items():
        if oracle.sha(Path(t['path']))!=t['sha256'] or r['toolchain_sha256_after'][n]!=t['sha256']:raise ValueError('toolchain identity')
    results=re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',r['stdout'])
    if results!=['7','1'] or 'MIXER_ALLOCATION,evaluations=10000,allocations=0' not in r['stdout']:
        raise ValueError('eight captured conformance/heap tests')
    m=re.search(r'MIXER_ORACLE,cases=279,max_voltage_v=([^,\s]+),max_current_a=([^,\s]+),max_admittance_s=([^,\s]+)',r['stdout'])
    if not m:raise ValueError('native maxima capture')
    native=dict(zip(('voltage_v','current_a','admittance_s'),map(float,m.groups())))
    if any(native[k]<0 or native[k]>oracle.GATES[k] for k in native):raise ValueError('native conformance maxima')
    archivep=ROOT/'evidence/voice_mixer_on_build_archive01.json';archive=json.loads(archivep.read_text(encoding='utf-8'))
    if not archive['cache_retired'] or archive['historical_campaigns_touched'] or archive['test_receipt_sha256']!=oracle.sha(attemptp) or archive['helper_sha256']!=oracle.sha(ROOT/'tools/archive_mixer_native_build.ps1'):
        raise ValueError('preserved build archive')
    if Path(archive['resolved_build_target']).exists() or len(archive['preserved_binaries'])!=2:raise ValueError('new build cache retirement')
    private={}
    for b in archive['preserved_binaries']:
        p=Path(b['preserved_path'])
        if not p.resolve().is_relative_to((ROOT/'references-local/mixer-on-native01').resolve()) or oracle.sha(p)!=b['sha256'] or p.stat().st_size!=b['bytes']:raise ValueError('preserved native binary')
        private[p.relative_to(ROOT).as_posix()]=b['sha256']
    base='9042af90d55b84113eb69e2cb4e9f6982b8b8e9e'
    lib=ROOT/'crates/rf-d-circuit/src/lib.rs';old=subprocess.check_output(['git','show',base+':crates/rf-d-circuit/src/lib.rs'],cwd=ROOT)
    if lib.read_bytes().count(b'pub mod mixer_on;\n')!=1 or lib.read_bytes().replace(b'pub mod mixer_on;\n',b'',1)!=old:raise ValueError('one module export only')
    unchanged=[];modes={}
    for p in (ROOT/'crates/rf-d-circuit/src').glob('*.rs'):
        if p.name in ('lib.rs','mixer_on.rs'):continue
        n=p.relative_to(ROOT).as_posix();blob=subprocess.check_output(['git','show',base+':'+n],cwd=ROOT)
        modes[n]=native_source_identity(n,oracle.sha(p),blob)
        unchanged.append(n)
    before={Path(__file__).relative_to(ROOT).as_posix():oracle.sha(Path(__file__))}
    OUTPUT.write_text(json.dumps(dict(schema='rf-d/mixer-on-native-audit/v1',passed=True,
        vector_sha256=oracle.sha(vectors),native_attempt_sha256=oracle.sha(attemptp),build_archive_sha256=oracle.sha(archivep),
        analysis_source_sha256=before,native_test_count=8,case_count=279,native_maxima=native,
        zero_heap_evaluations=10000,legacy_bus_comparison_passed=True,legacy_two_port_diagnostic_max_s=maxima['legacy_two_port_admittance_s'],
        unchanged_native_sources=sorted(unchanged),native_source_identity_modes=modes,
        explicit_checkout_pairs=CHECKOUT_PAIRS,base_commit=base,private_binary_sha256=private,
        admitted_static_on_ports=True,new_spice_solves=0,new_compiler_runs_during_audit=0,
        full_voice_integrated=False,physical_fidelity=False,real_time=False,new_audio=False),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('native mixer audit: passed; independent cases 279; native tests 8',flush=True)

if __name__=='__main__':main()
