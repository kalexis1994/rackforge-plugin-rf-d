"""Replay the equivalent-row experiment and preserve rejected gates by scope."""
import hashlib,json
from pathlib import Path
import numpy as np
import voice_741_row_build as build
import voice_741_row_compare as metrics
import voice_kcl_alias_instrument as prior
import voice_kcl_instrument as middle
import voice_inductor_instrument as earlier
import vco1_circuit_reference as vco
import voice_newton_probe as frozen

ROOT=vco.ROOT
WORK=build.WORK


def source_chain(old):
    source=[];old_patch=old['observation_rejection']['patch']['patches'];final_patch=old['patch']['patches']
    for p in earlier.TREE.rglob('*'):
        if not p.is_file():continue
        name=p.relative_to(earlier.TREE).as_posix();a=vco.sha(p)
        b=old_patch[name]['after_sha256'] if name in old_patch else a
        c=final_patch[name]['after_sha256'] if name in final_patch else b
        if vco.sha(middle.TREE/name)!=b or vco.sha(prior.TREE/name)!=c:raise ValueError('previous source tree changed')
        source.append((name,a,b,c))
    digest=hashlib.sha256(json.dumps(sorted(source),separators=(',',':')).encode()).hexdigest()
    if digest!=old['source_tree']['sha256']:raise ValueError('previous source ledger changed')
    return source


def main():
    output=ROOT/'evidence/voice_741_row_validation01.json'
    if output.exists():raise ValueError('preserve previous validation')
    old=vco.read(ROOT/'evidence/voice_kcl_observation02.json');patch=vco.read(WORK/'patch.json')
    if not old['passed'] or patch['previous_audit_sha256']!=vco.sha(ROOT/'evidence/voice_kcl_observation02.json'):raise ValueError('previous audit')
    chain=source_chain(old);sources=[]
    for name,_,_,digest in chain:
        ident=patch['patches'].get(name);expected=ident['after_sha256'] if ident else digest
        if ident and ident['before_sha256']!=digest:raise ValueError('candidate source before')
        if vco.sha(build.TREE/name)!=expected:raise ValueError('undeclared candidate source change')
        sources.append((name,digest,expected))
    if {p.relative_to(build.TREE).as_posix() for p in build.TREE.rglob('*') if p.is_file()}!={x[0] for x in sources}:raise ValueError('candidate source inventory')
    if patch['patcher_sha256']!=vco.sha(Path(build.__file__)):raise ValueError('patcher changed')
    for name,ident in patch['relocated_generated_files'].items():
        if vco.sha(WORK/name)!=ident['after_sha256']:raise ValueError('generated build files changed')
    marker='            *(ckt->CKTrhs+here->INDbrEq) += veq;'
    newmarker='            if (!here->IND741Active) *(ckt->CKTrhs+here->INDbrEq) += veq;'
    oldprefix=(prior.TREE/(build.DIR+'indload.c')).read_text().split(marker)[0]
    newprefix=(build.TREE/(build.DIR+'indload.c')).read_text().split(newmarker)[0]
    if oldprefix!=newprefix:raise ValueError('original flux and NIintegrate policy changed')
    bank=vco.read(ROOT/'evidence/voice_741_row_runs01.json')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after']:raise ValueError('wrapper changed during run')
    for name,digest in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('wrapper source changed')
    records=bank['records'];disabled={};control=None;rows={}
    for label,r in records.items():
        folder=WORK/'runs'
        for suffix,key in (('.cir','deck_sha256'),('.log','log_sha256')):
            if vco.sha(folder/(label+suffix))!=r[key]:raise ValueError('candidate artifact changed')
        if vco.sha(ROOT/r['exe_path'])!=r['exe_sha256'] or r['exe_sha256']!=r['exe_sha256_after']:raise ValueError('candidate executable changed')
        for key in ('source_sha256','helper_sha256','runtime_sha256'):
            if r[key]!=r[key+'_after']:raise ValueError('run inputs changed')
            for name,digest in r[key].items():
                if vco.sha(ROOT/name)!=digest:raise ValueError('run input identity')
        log=(folder/(label+'.log')).read_text(encoding='utf-8')
        enabled=label.startswith('row-on-')
        if ('RF741REDUCE,setup,l.xic3.l2,' in log)!=enabled:raise ValueError('activation scope')
        if 'RFTRACE,' in log or 'RFLTRACE,' in log or 'RFKTRACE,' in log:raise ValueError('temporal logging disabled')
        original_deck,original_export,_=frozen.original(r['scenario'])
        expected=original_deck.read_text(encoding='utf-8').replace('wrdata '+original_export.as_posix()+' ',
                    'wrdata '+(folder/(label+'.txt')).as_posix()+' ',1)
        if (folder/(label+'.cir')).read_text(encoding='utf-8')!=expected:raise ValueError('physical deck changed')
        if 'raw_export_sha256' in r:
            if vco.sha(folder/(label+'.txt'))!=r['raw_export_sha256']:raise ValueError('export changed')
            raw=np.loadtxt(folder/(label+'.txt'),skiprows=1,ndmin=2);frozen.exact(raw,raw);rows[label]=len(raw)
            if label.startswith('row-off-'):
                reference=np.loadtxt(prior.WORK/'runs'/('kcl-alias-off-'+r['scenario']+'.txt'),skiprows=1,ndmin=2)
                disabled[r['scenario']]=frozen.exact(raw,reference)
            elif label=='row-on-constant' and r['trajectory_complete']:
                reference=np.loadtxt(prior.WORK/'runs/kcl-alias-off-constant.txt',skiprows=1,ndmin=2)
                control=metrics.compare(raw,reference)
    if disabled!=bank['disabled_comparisons'] or control!=bank['active_control']:raise ValueError('recorded gates differ')
    disabled_pass=len(disabled)==2 and all(v['passed'] for v in disabled.values())
    if not disabled_pass and any(k.startswith('row-on-') for k in records):raise ValueError('active variant measured after failed disabled gate')
    if (control is None or not control['passed']) and 'row-on-returned' in records:raise ValueError('variable BUS measured after rejected control')
    variable=records.get('row-on-returned');admitted=bool(control and control['passed'] and variable and variable['trajectory_complete'])
    helpers=(Path(__file__),Path(metrics.__file__),ROOT/'tools/voice_741_row_math.py')
    report=dict(schema='rf-d/741-equivalent-row-validation/v1',passed=True,records=records,
                previous_audit_sha256=patch['previous_audit_sha256'],patch=patch,
                source_tree=dict(regular_files=len(sources),sha256=hashlib.sha256(json.dumps(sorted(sources),separators=(',',':')).encode()).hexdigest()),
                original_state_update_prefix_sha256=hashlib.sha256(oldprefix.encode()).hexdigest(),
                build_log_sha256=vco.sha(WORK/'reduction-make.log'),disabled_comparisons=disabled,
                active_control=control,decision=bank['decision'],candidate_admitted_locally=admitted,
                measured_solves=len(records),new_solves_during_validation=0,
                analysis_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
                coupling_admitted=False,explains_official_failure=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('741 row audit:',report['decision'],'locally admitted:',admitted,flush=True)


if __name__=='__main__':main()
