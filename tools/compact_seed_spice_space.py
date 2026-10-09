"""Reinforce the reserve by transparently compressing exact protected exports."""
import json,os,shutil,subprocess,time,traceback
from pathlib import Path
from compact_joint_cache import allocation
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    out='evidence/voice_joint_seed_cycles_compression03.json';require(not (ROOT/out).exists(),'new maintenance receipt');qa_name='evidence/voice_joint_charge_seed_tests01.json';qa=json.loads((ROOT/qa_name).read_text());require(qa['passed'],'admitted exports');names=sorted(n for n in qa['private_input_sha256'] if n.startswith('references-local/vco1-stamp-reference08/') and n.endswith('/transient.txt'));require(len(names)>0,'explicit old export scope')
    def inventory():
        result={}
        for n in names:
            p=ROOT/n;target=p.resolve();require(target.is_relative_to((ROOT/'references-local/vco1-stamp-reference08').resolve()) and p.is_file() and not p.is_symlink() and all(not os.path.islink(t) and not os.path.isjunction(t) for t in [p.parent,p.parent.parent]),'exact nonredirected export')
            result[n]=dict(sha256=sha(p),bytes=p.stat().st_size,allocated_bytes=allocation(p))
        return result
    before=inventory();require(all(r['sha256']==qa['private_input_sha256'][n] for n,r in before.items()),'protected identities');exe=Path(os.environ['SystemRoot'])/'System32/compact.exe';r=dict(schema='rf-d/seed-cycle-spice-compression/v1',passed=False,source_sha256={n:sha(ROOT/n) for n in [qa_name,'tools/compact_seed_spice_space.py','tools/compact_joint_cache.py']},utility_sha256=sha(exe),files_before=before,commands=[],free_before_bytes=shutil.disk_usage(ROOT).free,deleted_files=0,moved_files=0,logical_bytes_changed=False);start=time.perf_counter()
    try:
        for n in names:
            cmd=[str(exe),'/C','/A','/I','/Q',str((ROOT/n).resolve())];q=subprocess.run(cmd,capture_output=True,timeout=60);r['commands'].append(dict(command=cmd,exit_code=q.returncode,stdout=q.stdout.decode('oem',errors='replace'),stderr=q.stderr.decode('oem',errors='replace')));require(q.returncode==0,'compression')
        after=inventory();r['files_after']=after;require(before.keys()==after.keys() and all(before[n]['sha256']==after[n]['sha256'] and before[n]['bytes']==after[n]['bytes'] for n in names),'all logical bytes preserved');r['allocation_reclaimed_bytes']=sum(before[n]['allocated_bytes']-after[n]['allocated_bytes'] for n in names);r['passed']=True
    except Exception:r['failure']=traceback.format_exc();r['files_after_failure']=inventory();r['failure_identity_recheck']=all(before[n]['sha256']==r['files_after_failure'][n]['sha256'] for n in names)
    r['source_sha256_after']={n:sha(ROOT/n) for n in r['source_sha256']};require(r['source_sha256']==r['source_sha256_after'],'unchanged maintenance sources');r['wall_s']=time.perf_counter()-start;r['free_after_bytes']=shutil.disk_usage(ROOT).free;write(out,r);print('SEED_SPICE_SPACE',r['passed'],len(names),r.get('allocation_reclaimed_bytes'),r['free_after_bytes'],flush=True)
if __name__=='__main__':main()
