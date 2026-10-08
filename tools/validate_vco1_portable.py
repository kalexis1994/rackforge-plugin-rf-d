"""Validate exact laboratory-to-crate lineage and bounded API test receipts."""
import base64,hashlib,json,re,subprocess
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from validate_mixer_on_native import native_source_identity
OUT='evidence/voice_vco1_portable_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,msg):
    if not ok:raise ValueError(msg)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def function(source,name):
    start=source.index(b'fn '+name.encode()+b'<');opening=source.index(b'{',start);depth=1;i=opening+1
    while depth:
        depth+=(source[i]==123)-(source[i]==125);i+=1
    return source[start:i]
def audit():
    old=read('evidence/voice_vco1_radau_cycles_tests01.json');before=read('evidence/voice_vco1_portable_before01.json')
    require(old['passed'] and sha(ROOT/'evidence/voice_vco1_radau_cycles_tests01.json')==before['previous_qa_sha256'],'previous QA')
    require(before['source_sha256']==old['source_sha256'] and before['private_input_sha256']==old['private_input_sha256'],'frozen inputs')
    snapshots={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():
        require(hashlib.sha256(snapshots[n] if n in snapshots else (ROOT/n).read_bytes()).hexdigest()==h,'inherited source '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'inherited private '+n)
    original=snapshots['crates/rf-d-circuit/src/lib.rs'];addition=b'\nmod vco1_radau_fine;\npub mod vco1_radau;\npub mod vco1_engine;\n'
    require((ROOT/'crates/rf-d-circuit/src/lib.rs').read_bytes()==original+addition,'library only additive exports')
    fine=(ROOT/'crates/rf-d-circuit/src/vco1_radau_fine.rs').read_bytes()
    require(fine==(ROOT/'references-local/vco1-radau-cycles04/fine.rs').read_bytes(),'fine exact admitted copy')
    require(fine==(ROOT/'crates/rf-d-circuit/src/vco1_increment.rs').read_bytes().replace(b'125e-9/4096.',b'125e-9/65536.'),'physical stamp identity with existing API')
    kernel=(ROOT/'tools/vco1_radau_residual_kernel.rs').read_bytes().replace(b'fine::{self,State,Solution}',b'vco1_radau_fine::{self as fine,State,Solution}')
    portable=(ROOT/'crates/rf-d-circuit/src/vco1_radau.rs').read_bytes()
    require(portable.startswith(kernel),'coupled residual kernel exact body')
    require(portable[len(kernel):].startswith(b'\n/// Outward Qa/Q10'),'only terminal observation appended')
    linear=(ROOT/'references-local/vco1-radau-cycles04/linear.rs').read_bytes()
    current=(ROOT/'crates/rf-d-circuit/src/output_conversion.rs').read_bytes()
    for name in ['max_abs','solve_linear_sparse','solve_linear_internal']:
        require(function(linear,name).replace(b'\r\n',b'\n')==function(current,name).replace(b'\r\n',b'\n'),'sparse solver exact except declared CRLF/LF '+name)
    validation=read('evidence/voice_vco1_portable_validation01.json')
    require(len(validation['commands'])==2 and all(c['exit_code']!=0 and 'sparse solver exact max_abs' in c['stderr'] for c in validation['commands']),'validator failure/replay preserved')
    vectors=read('evidence/voice_vco1_portable_vectors01.json');bank=read('evidence/voice_vco1_radau_cycles04.json');diagnostic=read('evidence/voice_vco1_radau_newton01.json')
    require(vectors['bank_sha256']==sha(ROOT/'evidence/voice_vco1_radau_cycles04.json') and vectors['diagnostic_sha256']==sha(ROOT/'evidence/voice_vco1_radau_newton01.json'),'fixture lineage')
    require(canonical(vectors['actual_intervals'])==canonical(bank['profiles'][1]['actual_intervals']),'all four selected intervals unchanged')
    require(canonical(vectors['diagnostic']['independent'])==canonical(diagnostic['independent']),'independent diagnostic unchanged')
    for name in ['previous_high','previous_low','elapsed_ticks']:
        require(vectors['diagnostic'][name]==diagnostic[name],'diagnostic history '+name)
    for i in [1,2]:
        failure=read(f'evidence/voice_vco1_portable_native{i:02d}.json');repair=read(f'evidence/voice_vco1_portable_repair{i:02d}.json')
        require(not failure['passed'] and len(failure['commands'])==len(failure['replays'])==1,'failure and replay retained')
        require(failure['commands'][0]['exit_code']==failure['replays'][0]['exit_code']==101,'same rejection original/replay')
        require(repair['failure_sha256']==sha(ROOT/repair['failure_receipt']),'failure hash')
        for n,v in repair['before_base64'].items():
            require(base64.b64decode(v).decode()==failure['failed_source_text'][n],'repair source frozen')
    repair1=read('evidence/voice_vco1_portable_repair01.json')
    n='crates/rf-d-circuit/src/vco1_engine.rs';original_engine=base64.b64decode(repair1['before_base64'][n])
    corrected=original_engine.replace(b'Startup(vco1_newton::Error),',b'Startup(vco1_startup::Error),').replace(
        b'Error::Startup(vco1_newton::Error::IterationLimit)',b'Error::Startup(vco1_startup::Error::Newton(vco1_newton::Error::IterationLimit))')
    require((ROOT/n).read_bytes()==corrected,'wrapper repair only exact typed error edits')
    repair2=read('evidence/voice_vco1_portable_repair02.json')
    n='crates/rf-d-circuit/tests/vco1_engine.rs';original_test=base64.b64decode(repair2['before_base64'][n])
    corrected=original_test.replace(b'// A valid representation with extreme imposed load gives a deterministic nonlinear rejection.',
        b'// Diagnosed extreme range CV rejects in Newton; this tests rollback, not electrical admission.').replace(
        b'nonlinear.controls.external_neg4_load_a=1.;',b'nonlinear.controls.cv_v[5]=40.;')
    require((ROOT/n).read_bytes()==corrected,'test repair only diagnosed scene and comment')
    require('error[E0631]' in read('evidence/voice_vco1_portable_native01.json')['commands'][0]['stderr'],'typed startup failure')
    second=read('evidence/voice_vco1_portable_native02.json')
    require('3 passed; 1 failed' in second['commands'][0]['stdout'] and '3 passed; 1 failed' in second['replays'][0]['stdout'],'second test result/replay')
    d=read('evidence/voice_vco1_portable_diagnostic01.json');require(len(d['commands'])==3 and all(c['exit_code']==0 for c in d['commands']),'diagnostic executed')
    require(d['commands'][1]['stdout']==d['commands'][2]['stdout'] and d['commands'][1]['stderr']==d['commands'][2]['stderr'],'diagnostic exact replay')
    require('scene=0,error=PrecisionLimit(LocalError(' in d['commands'][1]['stdout'] and 'scene=2,error=PrecisionLimit(Nonlinear(LineSearch))' in d['commands'][1]['stdout'],'diagnosed distinct rejections')
    final=read('evidence/voice_vco1_portable_native03.json')
    require(final['passed'] and not final['replays'] and len(final['commands'])==1,'final attempt')
    require(final['source_sha256']==final['source_sha256_after'],'measured source stable')
    for n,h in final['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
    require(sha(Path(final['compiler']['path']))==final['compiler']['sha256']==final['compiler_sha256_after'],'compiler pinned')
    require(final['env']['RUSTFLAGS']=='-C opt-level=2 -C link-arg=-Wl,--stack,8388608' and final['env']['RUST_MIN_STACK']=='8388608','optimized fixed laboratory stack')
    text=final['commands'][0]['stdout']
    require(final['commands'][0]['exit_code']==0 and 'test result: ok. 4 passed; 0 failed' in text,'four actual tests')
    for marker in ['comparisons=26,actual_currents=12,new_independent_solves=0','startu'+'p_restore_accepted_allocations=0','temporal_and_nonlinear=true,allocations=0','u64_boundary=true,invalid_restore_cases=6']:
        require(marker in text,'native marker '+marker)
    scope=read('evidence/voice_vco1_portable_scope01.json')
    require(sha(ROOT/scope['provisional_qa_path'])==scope['provisional_qa_sha256'] and sha(ROOT/'docs/VCO1_PORTABLE_PROTOCOLO.md')==scope['original_protocol_sha256'],'conservative scope reconciliation retained')
    require(bank['inherited_250_profile'],'250 ns archived profile retained, not reexecuted portable')
    for folder in ['references-local/vco1-portable-diagnostic01','references-local/vco1-portable-scope01','tmp/vco1-portable-build01','tmp/vco1-portable-build02','tmp/vco1-portable-build03']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
    tracked=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    names=sorted(set(tracked)-{OUT});sources={n:sha(ROOT/n) for n in names}
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
    require(staged and OUT in staged,'stage complete release including QA')
    for n in staged:
        if n==OUT:continue
        native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/portable-engine-release/v1',passed=True,base_commit=before['base_commit'],
        previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,source_sha256_after=sources,
        private_input_sha256=private,inherited_test_count=235,native_test_count=4,covered_test_count=239,
        inherited_tests_reexecuted=False,independent_stage_comparisons=26,new_independent_solves=0,
        terminal_current_comparisons=12,archived_cycle_metrics_retained=True,portable_full_cycles_admitted=False,
        residual_kernel_identity_with_recovered_lab=True,new_full_campaigns=0,
        native_portable_api_admitted=True,atomic_checkpoint_admitted=True,integer_clock_u64_admitted=True,
        measured_heap_allocations=0,heap_scope='startup/restore/accepted/local-error rejection/nonlinear rejection',
        physical_kernel_changed=False,additive_production_modules=True,lab_stack_bytes=8388608,
        stack_bound_measured=False,real_time=False,physical_fidelity=False,active_mixer_admitted=False,
        calibrated_transient_admitted=False,c4_pf=10,new_spice_processes=0,new_audio=False,
        previous_audio=old['previous_audio'],native_listening=old['native_listening'],
        official_executable_sha256=old['official_executable_sha256'],long_note_admitted_locally=False)
def main():
    report=audit();(ROOT/OUT).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PORTABLE_QA',report['passed'],'sources',len(report['source_sha256']),'private',len(report['private_input_sha256']),'tests',report['covered_test_count'])
if __name__=='__main__':main()
