"""Compress a retained large lab export, preserving its logical bytes."""
import json,os,shutil,subprocess,time,traceback
from pathlib import Path
from compact_joint_cache import allocation
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    out='evidence/voice_joint_charge_response_compression02.json';require(not (ROOT/out).exists(),'exclusive maintenance')
    name='references-local/voice-circuit/full-note01/nominal125.txt';p=ROOT/name;target=p.resolve();require(target.is_relative_to((ROOT/'references-local/voice-circuit').resolve()) and p.is_file() and not p.is_symlink() and all(not os.path.islink(t) and not os.path.isjunction(t) for t in [p.parent,p.parent.parent,p.parent.parent.parent]),'exact nonredirected export')
    qa_name='evidence/voice_joint_seed_cycles_tests01.json';qa=json.loads((ROOT/qa_name).read_text());require(qa['passed'],'previous release');before=dict(sha256=sha(p),bytes=p.stat().st_size,allocated_bytes=allocation(p));protected=name in qa['private_input_sha256']
    if protected:require(before['sha256']==qa['private_input_sha256'][name],'previous protected identity')
    exe=Path(os.environ['SystemRoot'])/'System32/compact.exe';r=dict(schema='rf-d/charge-response-retained-export-compression/v1',passed=False,source_sha256={n:sha(ROOT/n) for n in [qa_name,'tools/compact_charge_response_capture.py','tools/compact_joint_cache.py']},utility_sha256=sha(exe),files_before={name:before},file_in_previous_private_manifest=protected,compression_does_not_admit_export_electrical_results=True,commands=[],free_before_bytes=shutil.disk_usage(ROOT).free,deleted_files=0,moved_files=0,logical_bytes_changed=False);start=time.perf_counter()
    try:
        cmd=[str(exe),'/C','/A','/I','/Q',str(target)];q=subprocess.run(cmd,capture_output=True,timeout=60);r['commands'].append(dict(command=cmd,exit_code=q.returncode,stdout=q.stdout.decode('oem',errors='replace'),stderr=q.stderr.decode('oem',errors='replace')));require(q.returncode==0,'compression')
        after=dict(sha256=sha(p),bytes=p.stat().st_size,allocated_bytes=allocation(p));r['files_after']={name:after};require(before['sha256']==after['sha256'] and before['bytes']==after['bytes'],'logical bytes preserved');r['allocation_reclaimed_bytes']=before['allocated_bytes']-after['allocated_bytes'];r['passed']=True
    except Exception:r['failure']=traceback.format_exc();r['failure_identity_recheck']=sha(p)==before['sha256']
    r['source_sha256_after']={n:sha(ROOT/n) for n in r['source_sha256']};require(r['source_sha256']==r['source_sha256_after'],'unchanged maintenance source');r['wall_s']=time.perf_counter()-start;r['free_after_bytes']=shutil.disk_usage(ROOT).free;write(out,r);print('CHARGE_RESPONSE_CAPTURE_SPACE',r['passed'],r.get('allocation_reclaimed_bytes'),r['free_after_bytes'],flush=True)

if __name__=='__main__':main()
