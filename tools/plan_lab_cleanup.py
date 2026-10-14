"""Plan retirement of regenerable private outputs; exclude every admitted input."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
QA='evidence/observed_note_tests01.json'
AREAS=['references-local/voice-circuit','references-local/vco1-circuit',
       'references-local/filter-vca-circuit','artifacts']
OUTPUTS={'.raw','.bin','.gz','.xz','.wav','.flac','.aif','.aiff','.exe','.dll',
         '.o','.obj','.a','.rlib','.csv','.tsv','.npy','.npz','.pyc'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    qa=json.loads((ROOT/QA).read_text(encoding='utf8'));assert qa['passed']
    protected=set(qa['private_input_sha256']);files=[];kept=[];directories=[]
    for area in AREAS:
        top=(ROOT/area).resolve();assert top.is_relative_to(ROOT.resolve()) and top.is_dir()
        for base,dirs,names in os.walk(top,followlinks=False):
            current=Path(base)
            assert not current.is_symlink() and not current.is_junction()
            for name in dirs:
                p=current/name
                assert not p.is_symlink() and not p.is_junction(),str(p)
            directories.append(current.relative_to(ROOT).as_posix())
            for name in names:
                p=current/name;assert not p.is_symlink()
                n=p.relative_to(ROOT).as_posix();s=p.stat();parts=p.relative_to(top).parts
                cache=any(v.startswith('newton-build') for v in parts) or n.startswith('artifacts/plot-libs/')
                top_receipt=cache and len(parts)==2 and p.suffix in {'.json','.log','.patch'}
                retire=n not in protected and not top_receipt and (cache or p.suffix.lower() in OUTPUTS or (p.suffix.lower()=='.txt' and s.st_size>65536))
                entry=dict(path=n,bytes=s.st_size,mtime_ns=s.st_mtime_ns)
                (files if retire else kept).append(entry)
    assert not protected.intersection(v['path'] for v in files)
    out=ROOT/'tmp/lab-cleanup-plan01.json';assert not out.exists()
    report=dict(schema='rf-d/lab-cleanup-plan/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),qa=QA,qa_sha256=sha(ROOT/QA),protected_input_count=len(protected),areas=AREAS,files=files,kept=kept,directories=sorted(directories,key=lambda v:len(Path(v).parts),reverse=True),retire_bytes=sum(v['bytes'] for v in files),retire_files=len(files),source_sha256={n:sha(ROOT/n) for n in ['tools/plan_lab_cleanup.py','tools/clean_lab_outputs.ps1']})
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('CLEANUP_PLAN',len(files),report['retire_bytes'],len(directories),len(kept))
if __name__=='__main__':main()
