"""Audit source/runtime chain, real-factor replay and sequential full gates."""
import hashlib,json
from pathlib import Path
import numpy as np
import voice_refine_build as prepared
import voice_refine_replay_build as build
import voice_refine_trace as refine
import voice_refine_arithmetic_retry as arithmetic
import voice_matrix_build_retry as observed
import voice_matrix_trace as matrix
import voice_kcl_alias_instrument as original
import voice_741_row_compare as metrics
import voice_newton_probe as frozen
from validate_voice_741_row import source_chain
import vco1_circuit_reference as vco

ROOT=vco.ROOT;WORK=build.WORK

def sources():
    old=vco.read(ROOT/'evidence/voice_kcl_observation02.json');prior=vco.read(ROOT/'evidence/voice_matrix_observation01.json')
    base_chain=source_chain(old);p06=prior['patch']['patches'];ledger=[]
    for name,_,_,digest in base_chain:
        expected=p06[name]['after_sha256'] if name in p06 else digest
        if vco.sha(observed.TREE/name)!=expected:raise ValueError('observed source changed')
        ledger.append((name,digest,expected))
    if hashlib.sha256(json.dumps(sorted(ledger),separators=(',',':')).encode()).hexdigest()!=prior['source_tree']['sha256']:raise ValueError('original source ledger')
    reports=[]
    for module in (prepared,build):
        patch=vco.read(module.WORK/'patch.json');rows=[]
        if patch['previous_audit_sha256']!=vco.sha(ROOT/'evidence/voice_matrix_observation01.json') or patch['protocol_sha256']!=vco.sha(ROOT/'docs/NEWTON_REFINAMIENTO_LINEAL_PROTOCOLO.md'):raise ValueError('preparation scope')
        if patch['corrections']!=3 or patch['device_stamps_changed'] or patch['state_update_changed']:raise ValueError('declared variant')
        for name,digest in patch['helper_sha256'].items():
            if vco.sha(ROOT/name)!=digest:raise ValueError('prepared helper changed')
        path='src/maths/ni/niiter.c'
        expected_text=module.patched((observed.TREE/path).read_text(encoding='utf-8'))
        if (module.TREE/path).read_bytes()!=expected_text.encode():raise ValueError('numerical patch not reproduced')
        for name,_,digest in ledger:
            ident=patch['patches'].get(name);expected=ident['after_sha256'] if ident else digest
            if ident and ident['before_sha256']!=digest:raise ValueError('source before')
            if vco.sha(module.TREE/name)!=expected:raise ValueError('undeclared source mutation')
            rows.append((name,digest,expected))
        for name,digest in patch['added_files'].items():
            if vco.sha(module.TREE/name)!=digest or digest!=vco.sha(ROOT/'tools/voice_refine_dd.h'):raise ValueError('arithmetic header identity')
            rows.append((name,None,digest))
        if {p.relative_to(module.TREE).as_posix() for p in module.TREE.rglob('*') if p.is_file()}!={r[0] for r in rows}:raise ValueError('source inventory')
        for name,ident in patch['relocated_generated_files'].items():
            if vco.sha(module.WORK/name)!=ident['after_sha256']:raise ValueError('generated build files')
        compile=vco.read(module.WORK/'build.json')
        if compile['exit_code'] or compile['build_log_sha256']!=vco.sha(module.WORK/'build.log') or compile['patch_sha256']!=vco.sha(module.WORK/'patch.json') or compile['executable_sha256']!=vco.sha(module.WORK/'baseline02/src/ngspice.exe'):raise ValueError('build identity')
        if vco.sha(Path(compile['compiler_path']))!=compile['compiler_sha256']:raise ValueError('compiler identity')
        reports.append(dict(source_tree=dict(regular_files=len(rows),sha256=hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()),patch=patch,compilation=compile))
    return reports

def main():
    output=ROOT/'evidence/voice_refine_validation01.json'
    if output.exists():raise ValueError('preserve validation')
    source_reports=sources();arith_path=ROOT/'evidence/voice_refine_arithmetic02.json';arith=vco.read(arith_path)
    if not arith['passed'] or arith['source_sha256']!=arith['source_sha256_after'] or arith['new_spice_solves']:raise ValueError('compiled arithmetic admission')
    for name,digest in arith['source_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('compiled arithmetic helper')
    folder=prepared.WORK/'arithmetic02'
    for name,key in (('bench.exe','exe_sha256'),('input.txt','input_sha256'),('output.txt','output_sha256'),('build.log','build_log_sha256')):
        if vco.sha(folder/name)!=arith[key]:raise ValueError('arithmetic artifacts changed')
    results=arithmetic.check(arithmetic.cases(),(folder/'output.txt').read_text(encoding='utf-8'))
    if results!=arith['results']:raise ValueError('arithmetic replay')
    rejected=vco.read(ROOT/'evidence/voice_refine_arithmetic_rejection01.json')
    if vco.sha(ROOT/rejected['failed_helper'])!=rejected['failed_helper_sha256'] or vco.sha(prepared.WORK/'arithmetic/build.log')!=rejected['build_log_sha256']:raise ValueError('failed compilation preservation')
    bank=vco.read(ROOT/'evidence/voice_refine_runs01.json')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after'] or bank['arithmetic_sha256']!=vco.sha(arith_path):raise ValueError('measured wrapper')
    for name,digest in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('measured helper changed')
    disabled={};control=None;replay=[];coverage={};rows={}
    baselines=vco.read(ROOT/'evidence/voice_kcl_runs03.json')['records']
    for label,r in bank['records'].items():
        folder=WORK/'runs';kind=r['scenario']
        for suffix,key in (('.cir','deck_sha256'),('.log','log_sha256')):
            if vco.sha(folder/(label+suffix))!=r[key]:raise ValueError('experiment artifact identity')
        if vco.sha(ROOT/r['exe_path'])!=r['exe_sha256'] or r['exe_sha256']!=r['exe_sha256_after'] or r['exe_sha256']!=source_reports[1]['compilation']['executable_sha256']:raise ValueError('candidate identity')
        for key in ('source_sha256','helper_sha256','runtime_sha256'):
            if r[key]!=r[key+'_after']:raise ValueError('run inputs changed')
            for name,digest in r[key].items():
                if vco.sha(ROOT/name)!=digest:raise ValueError('run input identity')
        deck,export,_=frozen.original(kind)
        expected=deck.read_text(encoding='utf-8').replace('wrdata '+export.as_posix()+' ','wrdata '+(folder/(label+'.txt')).as_posix()+' ',1)
        if (folder/(label+'.cir')).read_text(encoding='utf-8')!=expected:raise ValueError('physical deck changed')
        log=(folder/(label+'.log')).read_text(encoding='utf-8');active=label.startswith('refine-on-');is_replay=label=='refine-replay-returned'
        if ('RFREFINE,active,' in log)!=active or ('RFREFINE,replay,' in log)!=is_replay:raise ValueError('activation scope')
        if 'RFREFINE,error,' in log:raise ValueError('explicit arithmetic/solver failure')
        if any(s in log for s in ('RFTRACE,','RFLTRACE,','RFKTRACE,','RF741REDUCE,')):raise ValueError('old flags disabled')
        complete=False
        if 'raw_export_sha256' in r:
            if vco.sha(folder/(label+'.txt'))!=r['raw_export_sha256']:raise ValueError('export identity')
            a=np.loadtxt(folder/(label+'.txt'),skiprows=1,ndmin=2);frozen.exact(a,a);rows[label]=len(a)
            complete=not any(s in log.lower() for s in ('aborted','timestep too small','error:')) and abs(float(a[-1,0])-.04)<1e-14 and r.get('exit_code')==0 and not r.get('timeout')
            reference=original.WORK/'runs'/('kcl-alias-off-'+kind+'.txt')
            if vco.sha(reference)!=baselines['kcl-alias-off-'+kind]['raw_export_sha256']:raise ValueError('baseline bytes')
            b=np.loadtxt(reference,skiprows=1,ndmin=2)
            if label.startswith('refine-off-'):disabled[kind]=frozen.exact(a,b)
            if is_replay:
                disabled['replay']=frozen.exact(a,b)
                snapshots=matrix.parse(log);details=refine.parse(log)
                prior_log=(observed.WORK/'runs/matrix-on-returned.log').read_text(encoding='utf-8')
                if snapshots!=matrix.parse(prior_log) or len(details)!=2:raise ValueError('real factors and identical system')
                prior=vco.read(ROOT/'evidence/voice_matrix_observation01.json')
                replay=[refine.compare(s,d,a) for s,d,a in zip(snapshots,details,prior['analyses'])]
            if label=='refine-on-constant' and complete:control=metrics.compare(a,b)
        if complete!=r['trajectory_complete']:raise ValueError('coverage receipt')
        coverage[label]=complete
    if disabled!=bank['disabled_comparisons'] or control!=bank['active_control'] or replay!=bank['replay']:raise ValueError('recorded gates differ')
    if (len(disabled)!=3 or not all(v['passed'] for v in disabled.values()) or not all(v['passed'] for v in replay)) and any(k.startswith('refine-on-') for k in bank['records']):raise ValueError('active run before prechecks')
    if (control is None or not control['passed']) and 'refine-on-returned' in bank['records']:raise ValueError('variable BUS before control gate')
    admitted=bool(control and control['passed'] and coverage.get('refine-on-returned'))
    helpers=[Path(__file__),Path(refine.__file__),Path(arithmetic.__file__),Path(metrics.__file__)]
    report=dict(schema='rf-d/linear-refine-validation/v1',passed=True,source_reports=source_reports,arithmetic=arith,
        arithmetic_rejection_sha256=vco.sha(ROOT/'evidence/voice_refine_arithmetic_rejection01.json'),
        runs_sha256=vco.sha(ROOT/'evidence/voice_refine_runs01.json'),records=bank['records'],rows=rows,coverage_complete=coverage,
        disabled_comparisons=disabled,replay=replay,active_control=control,decision=bank['decision'],
        candidate_admitted_locally=admitted,measured_solves=len(bank['records']),new_solves_during_validation=0,
        analysis_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
        coupling_admitted=False,explains_official_failure=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('refinement audit:',report['decision'],'locally admitted:',admitted,flush=True)

if __name__=='__main__':main()
