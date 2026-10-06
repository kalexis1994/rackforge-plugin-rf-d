"""Replay tool identities, exact probe gates and rejected solver observations."""
import gzip,hashlib,json,subprocess,tarfile
from pathlib import Path
import numpy as np
import voice_newton_instrument as instrument
import voice_newton_probe as probe
import voice_newton_trace as trace
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=instrument.WORK


def tree_identity():
    download=vco.read(WORK/'download.json');patch=vco.read(WORK/'patch.json')
    if vco.sha(WORK/'ngspice-46.tar.gz')!=download['sha256']:raise ValueError('distribution identity')
    sources=patch['sources'];pairs=[]
    with tarfile.open(WORK/'ngspice-46.tar.gz') as archive:
        for member in archive.getmembers():
            if not member.isfile():continue
            name=Path(member.name).relative_to('ngspice-46').as_posix()
            original=archive.extractfile(member).read();digest=hashlib.sha256(original).hexdigest()
            expected=sources[name]['after_sha256'] if name in sources else digest
            if name in sources and digest!=sources[name]['before_sha256']:raise ValueError('source before patch identity')
            if vco.sha(instrument.TREE/name)!=expected:raise ValueError('unexpected source tree change: '+name)
            pairs.append((name,digest,expected))
    return dict(regular_files=len(pairs),sha256=hashlib.sha256(json.dumps(sorted(pairs),separators=(',',':')).encode()).hexdigest(),
                only_modified_files=sorted(sources),patch=patch,download=download)


def main():
    output=ROOT/'evidence/voice_newton_observation01.json'
    if output.exists():raise ValueError('preserve prior validation')
    build=vco.read(WORK/'build.json')
    for name,digest in build['file_sha256'].items():
        if vco.sha(ROOT/name)!=digest:raise ValueError('build artifact identity: '+name)
    if build['patcher_sha256']!=vco.sha(Path(instrument.__file__)):raise ValueError('patcher changed')
    rejections=vco.read(ROOT/'evidence/voice_newton_build_rejections01.json')
    for r in rejections['receipts']:
        folder=WORK/'runs';label=r['label']
        for suffix,key in (('.cir','deck_sha256'),('.log','log_sha256')):
            if vco.sha(folder/(label+suffix))!=r[key]:raise ValueError('configuration rejection identity')
        if r['trajectory_complete'] or (folder/(label+'.txt')).exists():raise ValueError('rejected configuration produced a trace')
        if r['source_sha256']!=r['source_sha256_after'] or r['helper_sha256']!=r['helper_sha256_after']:
            raise ValueError('configuration rejection inputs changed during measurement')
        if vco.sha(ROOT/r['exe_path'])!=r['exe_sha256'] or r['exe_sha256']!=r['exe_sha256_after']:
            raise ValueError('rejected executable identity')
        if 'XSPICE is required' not in (folder/(label+'.log')).read_text(encoding='utf-8'):raise ValueError('configuration rejection cause changed')
        for name,commit in rejections['rejected_helper_commits'].items():
            blob=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
            if hashlib.sha256(blob).hexdigest()!=r['helper_sha256'][name]:raise ValueError('rejected helper frozen source')
    if vco.sha(ROOT/rejections['rejected_make_log']['path'])!=rejections['rejected_make_log']['sha256']:
        raise ValueError('premature make rejection identity')
    tree=tree_identity();receipts={};arrays={};comparisons={};summaries={}
    preflight=vco.read(ROOT/'evidence/voice_newton_preflight_rejection01.json')
    for key in ('deck','runner_snapshot'):
        if vco.sha(ROOT/preflight[key+'_path'])!=preflight[key+'_sha256']:raise ValueError('preflight rejection identity')
    stages=('baseline-xspice02','instrumented-off','instrumented-on')
    for stage in stages:
        for kind in ('constant','returned'):
            label=stage+'-'+kind;folder=WORK/'runs';r=vco.read(folder/(label+'.json'))
            for suffix,key in (('.cir','deck_sha256'),('.log','log_sha256'),('.txt','raw_export_sha256')):
                if vco.sha(folder/(label+suffix))!=r[key]:raise ValueError('probe artifact identity: '+label+suffix)
            if vco.sha(ROOT/r['exe_path'])!=r['exe_sha256'] or r['exe_sha256']!=r['exe_sha256_after']:
                raise ValueError('probe executable changed')
            if r['source_sha256']!=r['source_sha256_after'] or r['helper_sha256']!=r['helper_sha256_after'] or r['runtime_sha256']!=r['runtime_sha256_after']:
                raise ValueError('probe sources changed during measurement')
            for name,digest in (r['source_sha256']|r['helper_sha256']|r['runtime_sha256']).items():
                if vco.sha(ROOT/name)!=digest:raise ValueError('measured source changed: '+name)
            raw=np.loadtxt(folder/(label+'.txt'),skiprows=1,ndmin=2);arrays[label]=raw
            _,old,_=probe.original(kind);contrast=probe.exact(raw,np.loadtxt(old,skiprows=1,ndmin=2))
            if contrast!=r['exact_official_trace']:raise ValueError('official contrast changed')
            text=(folder/(label+'.log')).read_text(encoding='utf-8',errors='replace')
            if stage=='instrumented-on':summaries[kind]=trace.summarize(trace.parse(text))
            elif 'RFTRACE,' in text:raise ValueError('trace present when disabled')
            receipts[label]=r
    for kind in ('constant','returned'):
        a,b,c=(arrays[stage+'-'+kind] for stage in stages)
        comparisons[kind]=dict(baseline_vs_off=probe.exact(a,b),off_vs_on=probe.exact(b,c))
        for metric in comparisons[kind].values():
            if not metric['passed']:raise ValueError('observation changed trajectory: '+kind)
        for field in ('trajectory_complete','reset_failure_reported'):
            if len({receipts[stage+'-'+kind][field] for stage in stages})!=1:
                raise ValueError('observation changed solver outcome')
    official_exact=all(r['exact_official_trace']['passed'] for r in receipts.values())
    report=dict(schema='rf-d/newton-observation/v1',passed=True,new_solves_during_validation=0,
                measured_solves=6,build=build,tree_identity=tree,receipts=receipts,
                configuration_rejections=2,rejection_archive_sha256=vco.sha(ROOT/'evidence/voice_newton_build_rejections01.json'),
                preflight_rejection_sha256=vco.sha(ROOT/'evidence/voice_newton_preflight_rejection01.json'),
                exact_observation_comparisons=comparisons,exact_official_trajectory=official_exact,
                observations=summaries,explains_official_failure=official_exact,
                full_nonlinear_kcl_residual_observed=False,coupling_admitted=False,
                physical_fidelity=False,real_time=False,new_audio=False,
                auditor_sha256=vco.sha(Path(__file__)))
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('instrumentation observation passed; exact official trajectory:',official_exact,flush=True)


if __name__=='__main__':main()
