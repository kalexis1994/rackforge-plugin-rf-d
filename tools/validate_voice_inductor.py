"""Replay exact observation gates, immutable sources and high precision L2 row."""
import hashlib,json
from pathlib import Path
import numpy as np
import voice_inductor_instrument as instrument
import voice_inductor_trace as trace
import voice_newton_probe as runner
import voice_newton_instrument as prior
import validate_voice_newton as previous
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=instrument.WORK


def main():
    output=ROOT/'evidence/voice_inductor_observation01.json'
    if output.exists():raise ValueError('preserve prior audit')
    old=vco.read(ROOT/'evidence/voice_newton_observation01.json');patch=vco.read(WORK/'patch.json')
    if patch['previous_audit_sha256']!=vco.sha(ROOT/'evidence/voice_newton_observation01.json'):raise ValueError('previous audit changed')
    if previous.tree_identity()!=old['tree_identity']:raise ValueError('prior source tree changed')
    if patch['patcher_sha256']!=vco.sha(Path(instrument.__file__)):raise ValueError('instrumenter changed')
    if vco.sha(WORK/'bin/prior.exe')!=old['receipts']['instrumented-off-returned']['exe_sha256']:raise ValueError('frozen previous executable')
    sources=[]
    for path in prior.TREE.rglob('*'):
        if not path.is_file():continue
        name=path.relative_to(prior.TREE).as_posix();digest=vco.sha(path)
        expected=patch['patches'][name]['after_sha256'] if name in patch['patches'] else digest
        if name in patch['patches'] and patch['patches'][name]['before_sha256']!=digest:raise ValueError('extension source before identity')
        if vco.sha(instrument.TREE/name)!=expected:raise ValueError('unexpected extension source change: '+name)
        sources.append((name,digest,expected))
    for name,ident in patch['relocated_generated_files'].items():
        if vco.sha(WORK/name)!=ident['after_sha256']:raise ValueError('relocated generated build file changed: '+name)
    bank=vco.read(ROOT/'evidence/voice_inductor_runs01.json')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after']:raise ValueError('wrapper changed during measurement')
    for name,digest in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('wrapper identity')
    summaries={};comparisons={};records={}
    for kind in ('constant','returned'):
        reference_path=prior.WORK/'runs'/('instrumented-off-'+kind+'.txt')
        oldreceipt=old['receipts']['instrumented-off-'+kind]
        if vco.sha(reference_path)!=oldreceipt['raw_export_sha256']:raise ValueError('prior baseline observation changed')
        reference=np.loadtxt(reference_path,skiprows=1,ndmin=2)
        comparisons[kind]={}
        for enabled in (False,True):
            state='on' if enabled else 'off';label='inductor-'+state+'-'+kind;r=bank['records'][label];folder=WORK/'runs'
            for suffix,key in (('.cir','deck_sha256'),('.log','log_sha256'),('.txt','raw_export_sha256')):
                if vco.sha(folder/(label+suffix))!=r[key]:raise ValueError('record artifact: '+label+suffix)
            if vco.sha(ROOT/r['exe_path'])!=r['exe_sha256'] or r['exe_sha256']!=r['exe_sha256_after']:raise ValueError('observer executable changed')
            for key in ('source_sha256','helper_sha256','runtime_sha256'):
                after_key='source_sha256_after' if key=='source_sha256' else key+'_after'
                if r[key]!=r[after_key]:raise ValueError('measured inputs changed')
                for name,digest in r[key].items():
                    if vco.sha(ROOT/name)!=digest:raise ValueError('measured source identity: '+name)
            raw=np.loadtxt(folder/(label+'.txt'),skiprows=1,ndmin=2)
            metric=runner.exact(raw,reference)
            if not metric['passed']:raise ValueError('L2 observation changed trajectory')
            if r['trajectory_complete']!=oldreceipt['trajectory_complete'] or r['reset_failure_reported']!=oldreceipt['reset_failure_reported']:
                raise ValueError('L2 observation changed solver outcome')
            comparisons[kind][state]=metric;records[label]=r
            log=(folder/(label+'.log')).read_text(encoding='utf-8')
            if enabled:summaries[kind]=trace.summarize(trace.pairs(log))
            elif 'RFLTRACE,' in log or 'RFTRACE,' in log:raise ValueError('disabled observer emitted observations')
    helpers=(Path(__file__),Path(trace.__file__))
    helper_hashes={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/inductor-observation-audit/v1',passed=True,records=records,
                previous_audit_sha256=patch['previous_audit_sha256'],patch=patch,
                source_tree=dict(regular_files=len(sources),sha256=hashlib.sha256(json.dumps(sorted(sources),separators=(',',':')).encode()).hexdigest(),
                                 only_extended_files=sorted(patch['patches'])),
                build_log_sha256=vco.sha(WORK/'observer-make.log'),exact_observation_comparisons=comparisons,
                observations=summaries,analysis_source_sha256=helper_hashes,
                new_solves_during_validation=0,measured_solves=4,
                conditional_history_reformulation_measured=False,
                conditional_history_reformulation_allowed=summaries['returned']['varying_history_stamps']>0,
                full_nonlinear_kcl_residual_observed=False,explains_official_failure=False,
                coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('L2 observation admitted locally; conditional RHS reformulation allowed:',report['conditional_history_reformulation_allowed'])


if __name__=='__main__':main()
