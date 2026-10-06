"""Audit observation bytes and exact trajectories, then solve captured A offline."""
import hashlib,json
from pathlib import Path
import numpy as np
import voice_matrix_build_retry as build
import voice_matrix_trace as trace
import voice_kcl_alias_instrument as prior
import voice_newton_probe as frozen
from validate_voice_741_row import source_chain
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=build.WORK

def main():
    output=ROOT/'evidence/voice_matrix_observation01.json'
    if output.exists():raise ValueError('preserve observation')
    old=vco.read(ROOT/'evidence/voice_kcl_observation02.json');patch=vco.read(WORK/'patch.json')
    if not old['passed'] or patch['previous_audit_sha256']!=vco.sha(ROOT/'evidence/voice_kcl_observation02.json'):raise ValueError('prior original audit')
    if patch['patcher_sha256']!=vco.sha(Path(build.__file__)) or patch['protocol_sha256']!=vco.sha(ROOT/'docs/NEWTON_MATRIZ_COMPLETA_PROTOCOLO.md'):raise ValueError('frozen preparation')
    rejection=vco.read(ROOT/'evidence/voice_matrix_preflight_rejection01.json')
    if vco.sha(ROOT/rejection['failed_helper'])!=rejection['failed_helper_sha256'] or rejection['private_tree_created'] or rejection['solves']:raise ValueError('preflight failure preservation')
    compilation=vco.read(WORK/'build.json')
    if compilation['exit_code'] or compilation['build_log_sha256']!=vco.sha(WORK/'build.log') or compilation['patch_sha256']!=vco.sha(WORK/'patch.json'):
        raise ValueError('compile receipt identity')
    if compilation['executable_sha256']!=vco.sha(WORK/'bin/observer.exe') or compilation['prior_executable_sha256']!=vco.sha(prior.WORK/'bin/observer.exe') or vco.sha(WORK/'bin/prior.exe')!=compilation['prior_executable_sha256']:
        raise ValueError('original and observer binaries')
    if vco.sha(Path(compilation['compiler_path']))!=compilation['compiler_sha256']:raise ValueError('compiler identity')
    chain=source_chain(old);sources=[]
    expected_patches=build.patched(*[(prior.TREE/p).read_text(encoding='utf-8') for p in ('src/maths/ni/niiter.c','src/maths/KLU/klusmp.c')])
    for name,s in zip(('src/maths/ni/niiter.c','src/maths/KLU/klusmp.c'),expected_patches):
        if (build.TREE/name).read_bytes()!=s.encode():raise ValueError('observer patch not reproduced')
    for name,_,_,digest in chain:
        ident=patch['patches'].get(name);expected=ident['after_sha256'] if ident else digest
        if ident and ident['before_sha256']!=digest:raise ValueError('observer source before')
        if vco.sha(build.TREE/name)!=expected:raise ValueError('undeclared source change')
        sources.append((name,digest,expected))
    if {p.relative_to(build.TREE).as_posix() for p in build.TREE.rglob('*') if p.is_file()}!={x[0] for x in sources}:raise ValueError('source inventory')
    for name,ident in patch['relocated_generated_files'].items():
        if vco.sha(WORK/name)!=ident['after_sha256']:raise ValueError('generated build file changed')
    bank=vco.read(ROOT/'evidence/voice_matrix_runs01.json')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after']:raise ValueError('wrapper changed during run')
    for name,digest in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('measured helper changed')
    comparisons={};snapshots={};rows={};coverage={};baseline_receipts=vco.read(ROOT/'evidence/voice_kcl_runs03.json')['records']
    for label,r in bank['records'].items():
        folder=WORK/'runs';kind=r['scenario']
        for suffix,key in (('.cir','deck_sha256'),('.log','log_sha256'),('.txt','raw_export_sha256')):
            if vco.sha(folder/(label+suffix))!=r[key]:raise ValueError('observer artifact changed')
        if vco.sha(ROOT/r['exe_path'])!=r['exe_sha256'] or r['exe_sha256']!=r['exe_sha256_after']:raise ValueError('executable changed')
        for key in ('source_sha256','helper_sha256','runtime_sha256'):
            if r[key]!=r[key+'_after']:raise ValueError('run inputs changed')
            for name,digest in r[key].items():
                if vco.sha(ROOT/name)!=digest:raise ValueError('run input identity')
        original_deck,original_export,_=frozen.original(kind)
        expected=original_deck.read_text(encoding='utf-8').replace('wrdata '+original_export.as_posix()+' ',
                    'wrdata '+(folder/(label+'.txt')).as_posix()+' ',1)
        if (folder/(label+'.cir')).read_text(encoding='utf-8')!=expected:raise ValueError('physical deck changed')
        baseline=prior.WORK/'runs'/('kcl-alias-off-'+kind+'.txt')
        receipt=baseline_receipts['kcl-alias-off-'+kind]
        if vco.sha(baseline)!=receipt['raw_export_sha256']:raise ValueError('baseline changed')
        a=np.loadtxt(folder/(label+'.txt'),skiprows=1,ndmin=2);b=np.loadtxt(baseline,skiprows=1,ndmin=2)
        comparisons[label]=frozen.exact(a,b);rows[label]=len(a)
        log=(folder/(label+'.log')).read_text(encoding='utf-8')
        actual_complete=not any(s in log.lower() for s in ('aborted','timestep too small','error:')) and abs(float(a[-1,0])-.04)<1e-14 and r.get('exit_code')==0 and not r.get('timeout')
        if actual_complete!=r['trajectory_complete']:raise ValueError('coverage receipt mismatch')
        coverage[label]=actual_complete
        if any(s in log for s in ('RFTRACE,','RFLTRACE,','RFKTRACE,','RF741REDUCE,')):raise ValueError('old observers/row variant disabled')
        parsed=trace.parse(log)
        if label.startswith('matrix-off-') and parsed:raise ValueError('disabled observer logged matrix')
        snapshots[label]=parsed
    if comparisons!=bank['comparisons'] or len(comparisons)!=4 or not all(c['passed'] for c in comparisons.values()):raise ValueError('four exact trajectories required')
    if not all(coverage[k] for k in coverage if k.endswith('constant')):raise ValueError('positive control complete')
    selected=snapshots['matrix-on-returned'];pairs={}
    for s in selected:pairs.setdefault((s['time_s'],s['h_s']),set()).add(s['iteration'])
    missing=[dict(time_s=t,h_s=h,missing_iterations=sorted({100,101}-iters)) for (t,h),iters in pairs.items() if iters!={100,101}]
    if not selected:missing.append(dict(reason='no selected iterations captured'))
    analyses=[trace.analyze(s) for s in selected]
    helpers=(Path(__file__),Path(trace.__file__),ROOT/'tools/validate_voice_741_row.py')
    report=dict(schema='rf-d/newton-matrix-observation/v1',passed=not missing,patch=patch,
        source_tree=dict(regular_files=len(sources),sha256=hashlib.sha256(json.dumps(sorted(sources),separators=(',',':')).encode()).hexdigest()),
        preflight_rejection_sha256=vco.sha(ROOT/'evidence/voice_matrix_preflight_rejection01.json'),
        runs_sha256=vco.sha(ROOT/'evidence/voice_matrix_runs01.json'),records=bank['records'],
        build_log_sha256=vco.sha(WORK/'build.log'),compilation=compilation,comparisons=comparisons,rows=rows,coverage_complete=coverage,
        captured_counts={k:len(v) for k,v in snapshots.items()},missing_selected=missing,analyses=analyses,
        selection='all iterations 100/101 with h<=1e-17s in 2.2773-2.2775ms; none substituted',
        exact_inputs='%.17g C round-trip to binary64, then Decimal.from_float, not decimal text interpreted as exact',
        residual_unit_policy='SP_VOLTAGE unknown V / KCL row A; SP_CURRENT unknown A / constraint row V; effective unmodified original MNA rows',
        precision_agreement_gate='80/120 absolute difference <=1e-55*max(1,abs(x120)) per unknown; diagnostic check only',
        residual_gate='abs(A*x120-b)<=1e-95*max(1,sum(abs(Aij*xj))+abs(b)) per row; no solver gate changed',
        analysis_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
        measured_solves=4,new_solves_during_validation=0,linear_system_observed=True,
        full_nonlinear_kcl_residual_observed=False,independent_nonlinear_root=False,
        coupling_admitted=False,explains_official_failure=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('matrix audit:',report['passed'],'snapshots:',len(selected),'missing:',missing,flush=True)
    for r in analyses:print(r['iteration'],r['h_s'],r['n'],r['nz'],r['maxima'],flush=True)

if __name__=='__main__':main()
