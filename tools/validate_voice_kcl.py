"""Audit immutable KCL observation, source copies and selected row residuals."""
import hashlib,json
from pathlib import Path
import numpy as np
import voice_kcl_instrument as instrument
import voice_kcl_instrument_retry as retry
import voice_kcl_trace as trace
import voice_newton_probe as runner
import voice_inductor_instrument as prior
import voice_newton_instrument as origin
import validate_voice_newton as previous
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=instrument.WORK


def inventory():
    path=ROOT/'references-local/datasheets/ti_lm741_lm741.lib'
    if vco.sha(path)!='f58370983c8bd22bf6a59ddd05a1dd492f1a0ea60f673ffd460a356da5e693dc':raise ValueError('frozen TI model')
    conductive={'16':[],'17':[]};controls={'16':[],'17':[]};active=False
    for line in path.read_text().splitlines():
        tokens=line.upper().split()
        if not tokens or tokens[0].startswith('*'):continue
        if tokens[0]=='.SUBCKT':active=tokens[1]=='LM741';continue
        if tokens[0].startswith('.ENDS'):active=False;continue
        if not active or tokens[0].startswith(('.', '+')):continue
        kind=tokens[0][0]
        if kind not in 'RLCVIDQGEFH':raise ValueError('unsupported inventory card')
        terminals=tokens[1:4] if kind=='Q' else tokens[1:3]
        for node in conductive:
            if node in terminals:conductive[node].append(tokens[0])
            if kind in 'GE' and node in tokens[3:-2]:controls[node].append(tokens[0])
    if conductive!={'16':['G4','R13'],'17':['L2','R13']} or controls!={'16':['EOS'],'17':[]}:raise ValueError('complete node inventory')
    mif='src/xspice/mif/mifload.c';port='src/xspice/icm/spice2poly/icm_spice2poly/ifspec.ifs'
    return dict(model_sha256=vco.sha(path),conductive_cards=conductive,ideal_voltage_control_cards=controls,
                input_port_source_sha256={n:vco.sha(prior.TREE/n) for n in (mif,port)},
                full_network_kcl_observed=False)


def main():
    output=ROOT/'evidence/voice_kcl_observation01.json'
    if output.exists():raise ValueError('preserve prior audit')
    old=vco.read(ROOT/'evidence/voice_inductor_observation01.json');patch=vco.read(WORK/'patch.json')
    if patch['previous_audit_sha256']!=vco.sha(ROOT/'evidence/voice_inductor_observation01.json'):raise ValueError('previous audit changed')
    original=vco.read(ROOT/'evidence/voice_newton_observation01.json')
    if previous.tree_identity()!=original['tree_identity']:raise ValueError('original source tree changed')
    triples=[]
    for p in origin.TREE.rglob('*'):
        if not p.is_file():continue
        name=p.relative_to(origin.TREE).as_posix();a=vco.sha(p)
        expected=old['patch']['patches'][name]['after_sha256'] if name in old['patch']['patches'] else a
        if vco.sha(prior.TREE/name)!=expected:raise ValueError('prior L2 source changed')
        triples.append((name,a,expected))
    if hashlib.sha256(json.dumps(sorted(triples),separators=(',',':')).encode()).hexdigest()!=old['source_tree']['sha256']:raise ValueError('previous tree ledger identity')
    if patch['patcher_sha256']!=vco.sha(Path(retry.__file__)):raise ValueError('instrumenter changed')
    if vco.sha(WORK/'bin/prior.exe')!=old['records']['inductor-off-returned']['exe_sha256']:raise ValueError('frozen previous executable')
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
    if {p.relative_to(instrument.TREE).as_posix() for p in instrument.TREE.rglob('*') if p.is_file()}!={x[0] for x in sources}:raise ValueError('unexpected source files')
    if patch['preparation_rejection_sha256']!=vco.sha(ROOT/'evidence/voice_kcl_preparation_rejection01.json'):raise ValueError('rejection changed')
    rejection=vco.read(ROOT/'evidence/voice_kcl_preparation_rejection01.json')
    if vco.sha(ROOT/rejection['source_path'])!=rejection['source_sha256'] or vco.sha(ROOT/rejection['frozen_source_path'])!=rejection['source_sha256']:raise ValueError('failed source identity')
    bank=vco.read(ROOT/'evidence/voice_kcl_runs01.json')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after']:raise ValueError('wrapper changed during measurement')
    for name,digest in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('wrapper identity')
    summaries={};comparisons={};records={}
    for kind in ('constant','returned'):
        reference_path=prior.WORK/'runs'/('inductor-off-'+kind+'.txt')
        oldreceipt=old['records']['inductor-off-'+kind]
        if vco.sha(reference_path)!=oldreceipt['raw_export_sha256']:raise ValueError('prior baseline observation changed')
        reference=np.loadtxt(reference_path,skiprows=1,ndmin=2)
        comparisons[kind]={}
        for enabled in (False,True):
            state='on' if enabled else 'off';label='kcl-'+state+'-'+kind;r=bank['records'][label];folder=WORK/'runs'
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
            elif any(prefix in log for prefix in ('RFKTRACE,','RFLTRACE,','RFTRACE,')):raise ValueError('disabled observer emitted observations')
    helpers=(Path(__file__),Path(trace.__file__))
    helper_hashes={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/kcl-observation-audit/v1',passed=True,records=records,
                previous_audit_sha256=patch['previous_audit_sha256'],patch=patch,
                source_tree=dict(regular_files=len(sources),sha256=hashlib.sha256(json.dumps(sorted(sources),separators=(',',':')).encode()).hexdigest(),
                                 only_extended_files=sorted(patch['patches'])),
                build_log_sha256=vco.sha(WORK/'observer-make.log'),exact_observation_comparisons=comparisons,
                observations=summaries,analysis_source_sha256=helper_hashes,
                new_solves_during_validation=0,measured_solves=4,
                selected_linear_kcl_observed_nodes=[16,17], numerical_reformulation_measured=False,
                model_inventory=inventory(),preparation_rejection=vco.read(ROOT/'evidence/voice_kcl_preparation_rejection01.json'),
                full_nonlinear_kcl_residual_observed=False,explains_official_failure=False,
                coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('KCL observation admitted locally; no numerical reformulation measured')


if __name__=='__main__':main()
