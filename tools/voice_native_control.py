"""One new dual-export solve, whole-array bit identity and preserved preflight."""
import json,shutil
from pathlib import Path
import numpy as np
import voice_binary_runner as runner
import voice_native_raw as native
import voice_six_runner as six
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def main():
    output=ROOT/'evidence/voice_native_control01.json';pre=ROOT/'evidence/voice_native_control_preflight01.json'
    if output.exists() or pre.exists() or runner.CONTROL.exists():raise ValueError('preserve native control')
    old,p=runner.source('nominal500')
    previous=vco.read(ROOT/'evidence/voice_six_long_preflight01.json')
    if previous['passed']:raise ValueError('protocol applies after archived ASCII resource rejection')
    estimated=old['raw_export_bytes']+old['rows']*(len(old['vectors'])+1)*8+131072
    free=shutil.disk_usage(ROOT).free;margin=2*1024**3
    resource=dict(schema='rf-d/native-control-preflight/v1',passed=free>=estimated+margin,estimated_export_bytes=estimated,
        available_free_bytes=free,required_free_bytes=estimated+margin,margin_bytes=margin,wall_limit_s=900,
        previous_ascii_preflight_sha256=vco.sha(ROOT/'evidence/voice_six_long_preflight01.json'),
        short_receipt_sha256=vco.sha(p),helper_sha256=vco.sha(Path(__file__)),new_spice_solves=0,estimates_are_not_bounds=True)
    runner.write(pre,resource)
    if not resource['passed']:raise ValueError('native control exports plus margin unavailable')
    helpers=[Path(__file__),Path(runner.__file__),Path(native.__file__)]
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    r=runner.run();report=dict(schema='rf-d/native-control/v1',run=r,preflight_sha256=vco.sha(pre),wrapper_sha256=before,
        reference_ascii_sha256=old['raw_export_sha256'],same_ascii_trajectory=None,binary_bit_identity=None,control_admitted=False,
        live_voltage_vectors=18,live_current_vectors=0,current_alias_scope='synthetic parser fixtures only',
        new_spice_solves=int(r['process_started']),new_audio=False,physical_fidelity=False,real_time=False)
    try:
        if r['trajectory_complete']:
            a=np.loadtxt(p.with_suffix('.txt'),skiprows=1,ndmin=2)
            b=np.loadtxt(runner.CONTROL/'nominal500.txt',skiprows=1,ndmin=2)
            c,layout=native.read(runner.CONTROL/'nominal500.raw',r['vectors'])
            report['same_ascii_trajectory']=native.bits(a,b);report['binary_bit_identity']=native.bits(b,c)
            report['control_admitted']=report['same_ascii_trajectory']['passed'] and report['binary_bit_identity']['passed']
    except Exception as e:report['analysis_error']=str(e)
    finally:
        report['wrapper_sha256_after']={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
        if report['wrapper_sha256_after']!=before:report['control_admitted']=False;report['analysis_error']='measured control helper changed'
        runner.write(output,report)
    print('native control admitted:',report['control_admitted'],flush=True)

if __name__=='__main__':main()
