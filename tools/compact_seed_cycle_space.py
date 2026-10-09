"""Compress four exact protected records transparently, without deleting bytes."""
import json,os,shutil,subprocess,time,traceback
from pathlib import Path
from compact_joint_cache import allocation
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
FILES=['references-local/vco1-sdirk-probe4-01/walk.failed-original.bin','references-local/vco1-sdirk-probe4-01/walk.bin','references-local/vco1-reset-grid02/reset.failed-original.bin','references-local/vco1-reset-grid02/reset.bin']

def inventory():
    rows={}
    for n in FILES:
        p=ROOT/n;target=p.resolve();require(target.is_relative_to((ROOT/'references-local').resolve()) and p.is_file() and not p.is_symlink(),'exact local record')
        require(all(not os.path.islink(t) and not os.path.isjunction(t) for t in [p.parent,p.parent.parent]),'no redirected parent')
        rows[n]=dict(sha256=sha(p),bytes=p.stat().st_size,allocated_bytes=allocation(p))
    return rows

def main():
    out='evidence/voice_joint_seed_cycles_compression01.json';require(not (ROOT/out).exists(),'new compression receipt');qa_name='evidence/voice_joint_charge_seed_tests01.json';qa=json.loads((ROOT/qa_name).read_text());before=inventory();require(qa['passed'] and all(qa['private_input_sha256'][n]==r['sha256'] for n,r in before.items()),'exact protected records')
    exe=Path(os.environ['SystemRoot'])/'System32/compact.exe';r=dict(schema='rf-d/seed-cycle-space-compression/v1',passed=False,source_sha256={n:sha(ROOT/n) for n in [qa_name,'tools/compact_seed_cycle_space.py','tools/compact_joint_cache.py']},utility_sha256=sha(exe),files_before=before,commands=[],free_before_bytes=shutil.disk_usage(ROOT).free,deleted_files=0,moved_files=0,logical_bytes_changed=False);start=time.perf_counter()
    try:
        for n in FILES:
            cmd=[str(exe),'/C','/A','/I','/Q',str((ROOT/n).resolve())];p=subprocess.run(cmd,capture_output=True,timeout=60);r['commands'].append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout.decode('oem',errors='replace'),stderr=p.stderr.decode('oem',errors='replace')));require(p.returncode==0,'compression')
        after=inventory();r['files_after']=after;require(all(before[n]['sha256']==after[n]['sha256'] and before[n]['bytes']==after[n]['bytes'] for n in before),'all bytes preserved');r['allocation_reclaimed_bytes']=sum(before[n]['allocated_bytes']-after[n]['allocated_bytes'] for n in before);r['passed']=True
    except Exception:r['failure']=traceback.format_exc();r['files_after_failure']=inventory();r['failure_identity_recheck']=all(before[n]['sha256']==r['files_after_failure'][n]['sha256'] for n in before)
    r['source_sha256_after']={n:sha(ROOT/n) for n in r['source_sha256']};require(r['source_sha256']==r['source_sha256_after'],'unchanged compression source');r['wall_s']=time.perf_counter()-start;r['free_after_bytes']=shutil.disk_usage(ROOT).free;write(out,r);print('SEED_SPACE',r['passed'],r.get('allocation_reclaimed_bytes'),r['free_after_bytes'],flush=True)
if __name__=='__main__':main()
