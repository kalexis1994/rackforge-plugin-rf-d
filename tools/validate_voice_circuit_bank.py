"""Scoped nominal validation; the full eleven-scene bank remains rejected."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np
import voice_circuit_reference as voice
import voice_circuit_probes as probes
import vco1_circuit_reference as vco

ROOT=vco.ROOT
ARCHIVE=ROOT/'evidence/voice_circuit_klu_bank01.json.gz'


def nominal_contrasts(bank):
    if bank['gates']!=probes.GATES:raise ValueError('original gates required')
    contrasts={}
    for a,b in [('nominal500','nominal250'),('nominal250','nominal125'),('nominal125','nominal-trap125')]:
        ca,cb=[bank['cases'][k] for k in (a,b)]
        if ca.get('error') or cb.get('error'):raise ValueError('nominal trajectory rejected')
        ma,mb=ca['measurements'],cb['measurements']
        cents=abs(1200*math.log2(ma['frequency_hz']/mb['frequency_hz']))
        extreme=max(abs(ma['windows'][n][metric]-mb['windows'][n][metric])
            for n in ('v(mix_bus_board4_pin4)','v(f4_recover_collector)','v(f4_main_output)')
            for metric in ('min','max'))
        rms=abs(ma['output_ac_rms_v']-mb['output_ac_rms_v'])
        limit=probes.GATES['rms_absolute_v']+probes.GATES['rms_relative']*mb['output_ac_rms_v']
        if cents>probes.GATES['frequency_cents'] or extreme>probes.GATES['extrema_v'] or rms>limit:
            raise ValueError('nominal contrast rejected')
        contrasts[a+'--'+b]=dict(frequency_cents=cents,max_extrema_difference_v=extreme,
            output_rms_difference_v=rms,rms_limit_v=limit)
    return contrasts


def main():
    output=ROOT/'evidence/voice_circuit_scoped_validation.json'
    if output.exists():raise ValueError('preserve prior audit')
    started=time.perf_counter()
    payload=gzip.decompress(ARCHIVE.read_bytes());bank=json.loads(payload)
    if bank['passed']:raise ValueError('historical full-bank rejection must remain visible')
    nominal=nominal_contrasts(bank)
    replayed=[];rejected=[]
    for label,case in bank['cases'].items():
        r=case['receipt'];work=ROOT/'references-local/voice-circuit'/bank['bank']
        if r['source_sha256']!=r['source_sha256_after']:raise ValueError('source mutated')
        for ext,key in [('cir','deck_sha256'),('log','log_sha256')]:
            if vco.sha(work/(label+'.'+ext))!=r[key]:raise ValueError('artifact digest')
        path=work/(label+'.txt')
        digest=r.get('raw_export_sha256',r.get('partial_export_sha256'))
        if vco.sha(path)!=digest:raise ValueError('export digest')
        raw=np.loadtxt(path,skiprows=1)
        if raw.shape[1]!=len(voice.VECTORS)+1 or not np.isfinite(raw).all() or np.any(np.diff(raw[:,0])<=0):
            raise ValueError('malformed clock or data')
        for name,digest in r['source_sha256'].items():
            if name.startswith('references-local/'):
                current=vco.sha(ROOT/name)
            else:
                blob=subprocess.check_output(['git','show',r['git_commit']+':'+name],cwd=ROOT)
                current=hashlib.sha256(blob).hexdigest()
            if current!=digest:raise ValueError('frozen input source changed')
        if case.get('error'):
            if r['trajectory_complete'] or raw[-1,0]>=r['scenario']['oscillator']['duration_s']:
                raise ValueError('rejected trajectory classification mismatch')
            rejected.append(dict(label=label,last_clock_s=float(raw[-1,0]),error=case['error']))
        else:
            if not r['trajectory_complete'] or len(raw)!=r['rows'] or abs(raw[-1,0]-.04)>1e-14:
                raise ValueError('trajectory not complete')
            if np.diff(raw[:,0]).max()>r['scenario']['oscillator']['max_step_s']*(1+1e-7):
                raise ValueError('maximum clock step')
            if voice.measure(raw)!=case['measurements']:raise ValueError('measurement replay')
            if case['measurements']['c2_balance_absolute_c']>probes.GATES['c2_charge_c']:
                raise ValueError('output charge balance')
            replayed.append(label)
    report=dict(schema='rf-d/voice-scoped-validation/v1',nominal_scope_passed=True,
        full_bank_passed=False,archive_sha256=vco.sha(ARCHIVE),
        canonical_payload_sha256=hashlib.sha256(payload).hexdigest(),nominal_contrasts=nominal,
        completed_trace_replay=replayed,rejected_trace_replay=rejected,new_solves=0,
        numerical_series_resistance_added=False,physical_fidelity=False,real_time=False,
        wall_s=time.perf_counter()-started,source_sha256={Path(__file__).relative_to(ROOT).as_posix():vco.sha(Path(__file__))})
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
