"""Replay completed loaded-contour traces and frozen source identities."""
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time
import numpy as np
import loudness_board4_circuit as c
import loudness_board4_probes as p
import vco1_circuit_reference as vco

ROOT=vco.ROOT
ARCHIVE=ROOT/'evidence/loudness_board4_bank02.json.gz'


def main():
    output=ROOT/'evidence/loudness_board4_validation.json'
    if output.exists():raise ValueError('preserve prior audit')
    started=time.perf_counter();payload=gzip.decompress(ARCHIVE.read_bytes());bank=json.loads(payload)
    if not bank['passed'] or bank['gates']!=p.GATES or set(bank['cases'])!=set(p.scenes()):
        raise ValueError('unchanged accepted complete bank required')
    work=ROOT/'references-local/voice-circuit'/bank['bank'];kept={};replayed=[]
    for label,s in p.scenes().items():
        case=bank['cases'][label];r=case['receipt']
        if case.get('error') or not r['trajectory_complete'] or r['scenario']!=asdict(s):
            raise ValueError('scene identity/completeness')
        if r['source_sha256']!=r['source_sha256_after']:raise ValueError('source mutated during solve')
        for ext,key in [('cir','deck_sha256'),('log','log_sha256'),('txt','raw_export_sha256')]:
            if vco.sha(work/(label+'.'+ext))!=r[key]:raise ValueError('private artifact hash')
        for name,digest in r['source_sha256'].items():
            blob=subprocess.check_output(['git','show',r['git_commit']+':'+name],cwd=ROOT)
            if hashlib.sha256(blob).hexdigest()!=digest:raise ValueError('frozen Git input hash')
        raw=np.loadtxt(work/(label+'.txt'),skiprows=1,ndmin=2)
        dt=np.diff(raw[:,0])
        if raw.shape!=(r['rows'],len(s.vectors)+1) or not np.isfinite(raw).all():raise ValueError('trace vectors/finiteness')
        if raw[0,0]!=0 or abs(raw[-1,0]-s.oscillator.duration_s)>1e-14 or np.any(dt<=0) or dt.max()>s.oscillator.max_step_s*(1+1e-7):
            raise ValueError('trace clock')
        m=c.measure(raw,s)
        if m!=case['measurements'] or max(m['timing_balance_max_c'],m['output_balance_max_c'])>p.GATES['charge_c']:
            raise ValueError('measurement replay or charge balance')
        if label.startswith('nominal'):kept[label]=raw
        replayed.append(label);print(label,'replayed',flush=True)
    pairs={a+'--'+b:p.contrast(kept[a],kept[b],p.scenes()[a],p.scenes()[b]) for a,b in p.PAIRS}
    if pairs!=bank['comparisons']:raise ValueError('comparison replay')
    failed=ROOT/'evidence/loudness_board4_bank01.json.gz';old=json.loads(gzip.decompress(failed.read_bytes()))
    if old['passed'] or len(old['cases'])!=10 or any(not x.get('error') for x in old['cases'].values()):
        raise ValueError('adapter failure history missing')
    report=dict(schema='rf-d/loudness-board4-validation/v1',passed=True,
        archive_sha256=vco.sha(ARCHIVE),payload_sha256=hashlib.sha256(payload).hexdigest(),
        replayed=replayed,comparisons=pairs,new_solves=0,physical_fidelity=False,real_time=False,
        previous_adapter_rejection_sha256=vco.sha(failed),
        vco_electrically_coupled=False,wall_s=time.perf_counter()-started,
        auditor_sha256=vco.sha(Path(__file__)))
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('accepted replay',len(replayed),flush=True)


if __name__=='__main__':main()
