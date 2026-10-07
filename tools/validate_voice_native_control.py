"""Replay native exports, commands, provenance and exact bit gates; no solve."""
import json
from dataclasses import asdict
from pathlib import Path
import numpy as np
import voice_binary_runner as runner
import voice_native_raw as native
import voice_native_control as control
import voice_six_runner as six
import voice_six_build as build
import voice_full_note as note
import validate_voice_six_build as compiled
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def run_identity(name,long_mode=False):
    work=runner.LONG if long_mode else runner.CONTROL;p=work/(name+'.json');r=vco.read(p)
    old,receipt=runner.source(name);s=note.scenes()[name] if long_mode else note.short.scenes()[name]
    exe=build.WORK/'bin/candidate.exe'
    if r['scene']!=name or r['long_mode']!=long_mode or six.canonical(r['scenario'])!=six.canonical(asdict(s)) or r['vectors']!=list(s.vectors):raise ValueError('frozen scene scope')
    if r['short_receipt_path']!=receipt.relative_to(ROOT).as_posix() or r['short_receipt_sha256']!=vco.sha(receipt) or r['original_deck_sha256']!=vco.sha(receipt.with_suffix('.cir')):raise ValueError('short source lineage')
    for key,n in (('short_bank_sha256','evidence/voice_six_short_runs01.json'),('short_audit_sha256','evidence/voice_six_short_validation01.json'),('build_sha256','evidence/voice_six_build01.json'),('protocol_sha256',runner.PROTOCOL)):
        if r[key]!=vco.sha(ROOT/n):raise ValueError('bound input identity')
    deck,changes=runner.patch(receipt.with_suffix('.cir').read_bytes(),name,receipt.with_suffix('.txt').as_posix(),(work/(name+'.txt')).as_posix(),(work/(name+'.raw')).as_posix(),long_mode)
    if (work/(name+'.cir')).read_bytes()!=deck or vco.sha(work/(name+'.cir'))!=r['deck_sha256'] or six.canonical(changes)!=six.canonical(r['patch']):raise ValueError('exact temporal/export patch')
    expected=[str(exe),'-n','-b',str(work/(name+'.cir'))]
    if r['command']!=expected or r['executable_path']!=exe.relative_to(ROOT).as_posix() or r['executable_sha256']!=vco.sha(exe) or r['executable_sha256_after']!=vco.sha(exe):raise ValueError('pinned executable/command')
    if r['helper_sha256']!=runner.helper_hashes() or r['runtime_sha256']!=runner.runtime() or r['current_source_sha256']!=old['current_source_sha256']:raise ValueError('complete helper/runtime/physical scope')
    for k in ('helper_sha256','runtime_sha256','current_source_sha256','compiled_source_sha256'):
        if r[k]!=r[k+'_after']:raise ValueError('run input stability')
    if r['compiled_source_sha256']!={n:vco.sha(build.TREE/n) for n in (build.NAME,*runner.WRITERS)}:raise ValueError('compiled source scope')
    if r['controlled_environment']!={f:('1' if f=='RF_D_LINEAR_REFINE' else None) for f in six.FLAGS} or r['published_corrections']!=6 or r['wall_limit_s']!=(7200 if long_mode else 900):raise ValueError('flags and budgets')
    logp=work/(name+'.log')
    if vco.sha(logp)!=r['log_sha256']:raise ValueError('log identity')
    status=six.log_status(logp.read_text(encoding='utf-8',errors='replace'),True)
    if any(r[k]!=v for k,v in status.items()):raise ValueError('six activation/failure scope')
    a=None;info={};error=None
    for ext in ('txt','raw'):
        if ext+'_sha256' in r:
            artifact=work/(name+'.'+ext)
            if vco.sha(artifact)!=r[ext+'_sha256'] or artifact.stat().st_size!=r[ext+'_bytes']:raise ValueError('export byte identity')
    try:
        a,layout=native.read(work/(name+'.raw'),s.vectors)
        if six.canonical(layout)!=six.canonical(r['native_layout']):raise ValueError('native layout identity')
        info=six.clock_info(a,s.vectors,s.oscillator.duration_s,s.oscillator.max_step_s)
    except Exception as e:error=str(e)
    if error!=r.get('export_error') or any(r[k]!=v for k,v in info.items()):raise ValueError('native clock/export replay')
    complete=bool(info.get('endpoint_complete') and info.get('max_step_passed') and status['activation_gate_passed'] and not r.get('timeout') and not r.get('launch_error') and r.get('exit_code')==0)
    if r['trajectory_complete']!=complete:raise ValueError('trajectory gate')
    if long_mode:
        proof=ROOT/'evidence/voice_native_control_validation01.json'
        if r['control_audit_sha256']!=vco.sha(proof) or not vco.read(proof)['control_admitted']:raise ValueError('long dependency control gate')
        if (work/(name+'.txt')).exists():raise ValueError('long raw-only export required')
    return r,a

def main():
    output=ROOT/'evidence/voice_native_control_validation01.json'
    if output.exists():raise ValueError('preserve native control audit')
    path=ROOT/'evidence/voice_native_control01.json';bank=vco.read(path)
    fresh=compiled.validate();stored=vco.read(ROOT/'evidence/voice_six_build_validation01.json')
    if six.canonical(fresh)!=six.canonical({k:v for k,v in stored.items() if k!='schema'}):raise ValueError('compiled tree changed')
    for n,h in bank['wrapper_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('measured control helper changed')
    if bank['wrapper_sha256']!=bank['wrapper_sha256_after']:raise ValueError('control wrapper stability')
    pre=ROOT/'evidence/voice_native_control_preflight01.json';resource=vco.read(pre)
    old,receipt=runner.source('nominal500')
    estimate=old['raw_export_bytes']+old['rows']*(len(old['vectors'])+1)*8+131072
    if bank['preflight_sha256']!=vco.sha(pre) or resource['estimated_export_bytes']!=estimate or resource['margin_bytes']!=2*1024**3 or resource['required_free_bytes']!=estimate+2*1024**3 or not resource['passed'] or resource['available_free_bytes']<resource['required_free_bytes'] or resource['wall_limit_s']!=900 or resource['short_receipt_sha256']!=vco.sha(receipt) or resource['helper_sha256']!=vco.sha(Path(control.__file__)):raise ValueError('native control resource replay')
    previous=ROOT/'evidence/voice_six_long_preflight01.json'
    if resource['previous_ascii_preflight_sha256']!=vco.sha(previous) or vco.read(previous)['passed']:raise ValueError('archived ASCII resource rejection')
    r,a=run_identity('nominal500')
    if six.canonical(r)!=six.canonical(bank['run']):raise ValueError('public/private control receipt identity')
    same=None;bits=None
    if r['trajectory_complete']:
        reference=np.loadtxt(receipt.with_suffix('.txt'),skiprows=1,ndmin=2)
        exported=np.loadtxt(runner.CONTROL/'nominal500.txt',skiprows=1,ndmin=2)
        same=native.bits(reference,exported);bits=native.bits(exported,a)
    admitted=bool(same and same['passed'] and bits and bits['passed'])
    if same!=bank['same_ascii_trajectory'] or bits!=bank['binary_bit_identity'] or admitted!=bank['control_admitted'] or bank['new_spice_solves']!=int(r['process_started']):raise ValueError('bit admission replay')
    if bank['live_voltage_vectors']!=18 or bank['live_current_vectors']!=0 or bank['current_alias_scope']!='synthetic parser fixtures only':raise ValueError('live vector scope')
    if bank['reference_ascii_sha256']!=old['raw_export_sha256']:raise ValueError('whole ASCII reference')
    helpers=[Path(__file__),Path(control.__file__),Path(runner.__file__),Path(native.__file__),Path(compiled.__file__)]
    report=dict(schema='rf-d/native-control-validation/v1',passed=True,control_admitted=admitted,control_sha256=vco.sha(path),
        preflight_sha256=vco.sha(pre),compiled_audit_sha256=vco.sha(ROOT/'evidence/voice_six_build_validation01.json'),
        same_ascii_trajectory=same,binary_bit_identity=bits,rows=r.get('rows'),columns=19,
        ascii_bytes=r.get('txt_bytes'),native_bytes=r.get('raw_bytes'),native_layout=r.get('native_layout'),
        live_voltage_vectors=18,live_current_vectors=0,new_spice_solves=0,new_compiler_runs=0,
        analysis_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},physical_fidelity=False,real_time=False,new_audio=False)
    runner.write(output,report);print('native control audit admitted:',admitted,flush=True)

if __name__=='__main__':main()
