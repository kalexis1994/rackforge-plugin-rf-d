"""Keep a compact cleanup ledger, never an archive of retired samples."""
import gzip,json,shutil
from prepare_dual_chain import ROOT,sha,write
def main():
    receipt='evidence/lab_cleanup01.json';r=json.loads((ROOT/receipt).read_text(encoding='utf8'))
    assert r['passed'] and r['retired_files']==r['planned_files'] and r['retired_bytes']==r['planned_bytes']
    original=(ROOT/r['full_plan_private']).resolve();assert original.parent==(ROOT/'tmp').resolve()
    assert sha(original)==r['plan_sha256']
    data=original.read_bytes();plan=json.loads(data)
    assert not any((ROOT/x['path']).exists() for x in plan['files'])
    destination=ROOT/'references-local/lab-retention';destination.mkdir(exist_ok=True)
    packed=destination/'cleanup01.plan.json.gz';assert not packed.exists()
    packed.write_bytes(gzip.compress(data,compresslevel=6,mtime=0));assert gzip.decompress(packed.read_bytes())==data
    original.unlink()
    out='evidence/lab_retention_ledger01.json';assert not (ROOT/out).exists()
    write(ROOT/out,dict(passed=True,source_sha256={n:sha(ROOT/n) for n in [receipt,'tools/finish_lab_retention.py']},private_sha256={packed.relative_to(ROOT).as_posix():sha(packed)},restored_plan_sha256=r['plan_sha256'],retired_plan_path=r['full_plan_private'],ledger_bytes=packed.stat().st_size,retired_samples_archived=False,logical_retired_bytes=r['retired_bytes'],removed_empty_directories=r['removed_empty_directories'],free_after_bytes=shutil.disk_usage(ROOT).free))
    print('RETENTION_LEDGER',packed.stat().st_size,'bytes; samples archived: false; free:',shutil.disk_usage(ROOT).free)
if __name__=='__main__':main()
