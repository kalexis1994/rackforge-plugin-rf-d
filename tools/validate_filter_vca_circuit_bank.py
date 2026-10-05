"""Replay complete private exports and bind omitted generator to frozen Git."""
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

import filter_vca_circuit_reference as f
import filter_vca_circuit_probes as probes
import vco1_circuit_reference as vco

ARCHIVE=f.ROOT/'evidence/filter_vca_circuit_bank01.json.gz'


def audit():
    started=time.perf_counter()
    payload=gzip.decompress(ARCHIVE.read_bytes())
    bank=json.loads(payload)
    contrasts=probes.validate(bank)
    if not bank['passed'] or contrasts!=bank['comparisons']:
        raise ValueError('archived validation mismatch')
    replay=[]
    supplemental={}
    for label,s in probes.scenes().items():
        case=bank['cases'][label];r=case['receipt']
        if r['git_status']: raise ValueError('numerical bank was not frozen cleanly')
        work=f.ROOT/'references-local/filter-vca-circuit'/bank['bank']
        for ext,key in [('cir','deck_sha256'),('log','log_sha256'),('txt','raw_export_sha256')]:
            if vco.sha(work/(label+'.'+ext))!=r[key]: raise ValueError('private artifact digest changed')
        raw=np.loadtxt(work/(label+'.txt'),skiprows=1)
        if len(raw)!=r['rows'] or raw.shape[1]!=len(f.VECTORS)+1 or not np.isfinite(raw).all():
            raise ValueError('invalid complete trace')
        dt=np.diff(raw[:,0])
        if raw[0,0]!=0 or np.any(dt<=0) or abs(raw[-1,0]-s.oscillator.duration_s)>1e-14:
            raise ValueError('export clock incomplete')
        if dt.max()>s.oscillator.max_step_s*(1+1e-7): raise ValueError('clock limit')
        if f.measure(raw,s)!=case['measurements']: raise ValueError('replayed measurement changed')
        # Verify each measured input file from its immutable commit. Initial
        # bank did not list vco generator directly; clean Git identifies it.
        files=r['source_sha256']|{'tools/vco1_circuit_reference.py':None}
        for name,digest in files.items():
            blob=subprocess.check_output(['git','show',r['git_commit']+':'+name],cwd=f.ROOT)
            sha=hashlib.sha256(blob).hexdigest()
            if digest is not None and sha!=digest: raise ValueError('frozen Git source digest mismatch')
            if name=='tools/vco1_circuit_reference.py': supplemental[r['git_commit']]=sha
        replay.append(label)
    return dict(schema='rf-d/filter-vca-circuit-validation/v1',passed=True,
        archive_sha256=vco.sha(ARCHIVE),canonical_payload_sha256=hashlib.sha256(payload).hexdigest(),
        private_full_trace_replay=replay,supplemental_frozen_generator_sha256=supplemental,
        comparisons=contrasts,new_solves=0,wall_s=time.perf_counter()-started,
        source_sha256={p.relative_to(f.ROOT).as_posix():vco.sha(p) for p in
                      [Path(__file__),Path(f.__file__),Path(probes.__file__),ARCHIVE]})


if __name__=='__main__':
    output=f.ROOT/'evidence/filter_vca_circuit_validation.json'
    if output.exists(): raise ValueError('preserve earlier audit')
    report=audit()
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,indent=2))
