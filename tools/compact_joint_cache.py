"""Transparent compression of three frozen lab caches; no deletion or moving."""
import ctypes,json,os,shutil,subprocess,time,traceback
from ctypes import wintypes
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require

DIRECTORIES=['tmp/vco1-portable-build01','tmp/vco1-portable-build02','tmp/vco1-portable-build03']
def allocation(path):
    high=wintypes.DWORD();ctypes.set_last_error(0)
    low=allocated(str(path),ctypes.byref(high));error=ctypes.get_last_error()
    require(low!=0xffffffff or error==0,'GetCompressedFileSizeW '+str(error))
    return (high.value<<32)|low

def inventory():
    rows={}
    for name in DIRECTORIES:
        target=(ROOT/name).resolve();require(target.is_relative_to((ROOT/'tmp').resolve()) and target.is_dir(),'cache scope')
        for directory,dirs,files in os.walk(target,followlinks=False):
            require(not os.path.islink(directory) and not os.path.isjunction(directory),'no linked directory')
            for n in dirs:require(not os.path.islink(os.path.join(directory,n)) and not os.path.isjunction(os.path.join(directory,n)),'no linked child')
            for n in files:
                p=__import__('pathlib').Path(directory)/n;require(not p.is_symlink(),'no linked file')
                rows[p.relative_to(ROOT).as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size,allocated_bytes=allocation(p))
    return rows

def main():
    out=ROOT/'evidence/voice_joint_cache_compression01.json';require(not out.exists(),'preserve maintenance receipt')
    qa_name='evidence/voice_joint_startup_tests01.json';qa=json.loads((ROOT/qa_name).read_text());require(qa['passed'],'admitted release')
    before=inventory();protected=qa['private_input_sha256'];require(all(n in protected and r['sha256']==protected[n] for n,r in before.items()),'exact protected caches')
    command=__import__('pathlib').Path(os.environ['SystemRoot'])/'System32/compact.exe';require(command.is_file(),'Windows compact')
    r=dict(schema='rf-d/joint-cache-compression/v1',passed=False,source_sha256={qa_name:sha(ROOT/qa_name),'tools/compact_joint_cache.py':sha(ROOT/'tools/compact_joint_cache.py')},utility_sha256=sha(command),directories=DIRECTORIES,files_before=before,commands=[],free_before_bytes=shutil.disk_usage(ROOT).free,deleted_files=0,moved_files=0,logical_bytes_changed=False)
    started=time.perf_counter()
    try:
        for name in DIRECTORIES:
            args=[str(command),'/C','/S:'+str((ROOT/name).resolve()),'/A','/I','/Q'];s=time.perf_counter();p=subprocess.run(args,capture_output=True,timeout=60)
            r['commands'].append(dict(command=args,exit_code=p.returncode,wall_s=time.perf_counter()-s,stdout=p.stdout.decode('oem',errors='replace'),stderr=p.stderr.decode('oem',errors='replace')))
            require(p.returncode==0,'compression command')
        after=inventory();r['files_after']=after
        require(before.keys()==after.keys(),'same file inventory')
        require(all(before[n]['sha256']==after[n]['sha256'] and before[n]['bytes']==after[n]['bytes'] for n in before),'all logical bytes preserved')
        r['allocated_before_bytes']=sum(x['allocated_bytes'] for x in before.values());r['allocated_after_bytes']=sum(x['allocated_bytes'] for x in after.values());r['allocation_reclaimed_bytes']=r['allocated_before_bytes']-r['allocated_after_bytes'];r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['files_after_failure']=inventory();r['failure_identity_recheck']=all(n in r['files_after_failure'] and before[n]['sha256']==r['files_after_failure'][n]['sha256'] for n in before)
    r['free_after_bytes']=shutil.disk_usage(ROOT).free;r['wall_s']=time.perf_counter()-started;r['source_sha256_after']={n:sha(ROOT/n) for n in r['source_sha256']};require(r['source_sha256']==r['source_sha256_after'],'maintenance sources unchanged')
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CACHE_COMPRESSION',r['passed'],r.get('allocation_reclaimed_bytes'),r['free_after_bytes'],r.get('failure',''),flush=True)

kernel=ctypes.WinDLL('kernel32',use_last_error=True);allocated=kernel.GetCompressedFileSizeW;allocated.argtypes=[wintypes.LPCWSTR,ctypes.POINTER(wintypes.DWORD)];allocated.restype=wintypes.DWORD
if __name__=='__main__':main()
