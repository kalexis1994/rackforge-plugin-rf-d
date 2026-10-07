"""Exact archival of this campaign's new intermediates; never sweeps directories."""
from contextlib import contextmanager
import gzip, hashlib, lzma, stat
from pathlib import Path
import voice_lossless_archive as archive
import voice_binary_runner as runner
import vco1_circuit_reference as vco

SCENES=('nominal500','nominal250','nominal125','nominal-trap125')
SUFFIX={'gzip9':'.raw.gz','xz6-crc64':'.raw.xz'}

def member(work, name, suffix):
    work=Path(work)
    if name not in SCENES or suffix not in ('.raw','.json','.archive.json','.raw.gz','.raw.xz'):
        raise ValueError('exact scene artifact required')
    if not work.is_dir() or work.is_symlink() or work.is_junction():
        raise ValueError('direct campaign directory required')
    path=work/(name+suffix)
    if path.is_symlink() or path.is_junction() or path.resolve().parent!=work.resolve():
        raise ValueError('artifact must stay inside campaign')
    if path.exists() and (not stat.S_ISREG(path.stat().st_mode) or path.stat().st_nlink!=1):
        raise ValueError('single regular artifact required')
    return path

def archive_run(work, name, receipt, codec):
    if codec not in SUFFIX:raise ValueError('admitted codec required')
    raw=member(work,name,'.raw');stored=member(work,name,'.json')
    manifest=member(work,name,'.archive.json');target=member(work,name,SUFFIX[codec])
    if manifest.exists() or target.exists():raise ValueError('preserve archival attempt')
    if runner.six.canonical(vco.read(stored))!=runner.six.canonical(receipt):
        raise ValueError('original private receipt required')
    if vco.sha(raw)!=receipt.get('raw_sha256') or raw.stat().st_size!=receipt.get('raw_bytes'):
        raise ValueError('original raw receipt identity')
    before={p.name:vco.sha(p) for p in (raw,stored)}
    proof=archive.encode(raw,target,codec)
    if proof['original_sha256']!=receipt['raw_sha256'] or proof['original_bytes']!=receipt['raw_bytes']:
        raise ValueError('encoder source identity')
    # Independently reopen and verify the entire container before retiring the raw.
    archive.verify(target,codec,receipt['raw_sha256'],receipt['raw_bytes'])
    if before!={p.name:vco.sha(p) for p in (raw,stored)} or vco.sha(target)!=proof['archive_sha256']:
        raise ValueError('archive transaction inputs changed')
    result=dict(schema='rf-d/serial-raw-archive/v1',scene=name,codec=codec,
        original_path=raw.name,original_sha256=receipt['raw_sha256'],original_bytes=receipt['raw_bytes'],
        receipt_path=stored.name,receipt_sha256=vco.sha(stored),archive_path=target.name,
        archive_sha256=proof['archive_sha256'],archive_bytes=proof['archive_bytes'],
        encoding_s=proof['encoding_s'],verification_s=proof['verification_s'],
        full_restoration_verified=True,raw_retired=False,original_receipt_retained=True,
        private_data_only=True,helper_sha256=vco.sha(Path(__file__)))
    runner.write(manifest,result)
    # One explicit, resolved, verified, newly generated file. No recursive cleanup.
    if member(work,name,'.raw')!=raw or vco.sha(raw)!=result['original_sha256'] or vco.sha(target)!=result['archive_sha256']:
        raise ValueError('retirement identity changed')
    raw.unlink()
    result['raw_retired']=True
    runner.write(manifest,result)
    return result

def archive_identity(work,name):
    manifest=member(work,name,'.archive.json');r=vco.read(manifest)
    if r['scene']!=name or r['codec'] not in SUFFIX or not r['raw_retired'] or not r['full_restoration_verified']:
        raise ValueError('completed archive required')
    raw=member(work,name,'.raw');stored=member(work,name,'.json');target=member(work,name,SUFFIX[r['codec']])
    if (r['original_path'],r['receipt_path'],r['archive_path'])!=(raw.name,stored.name,target.name):
        raise ValueError('exact manifest paths required')
    if r['helper_sha256']!=vco.sha(Path(__file__)) or vco.sha(stored)!=r['receipt_sha256']:
        raise ValueError('archive helper/receipt identity')
    receipt=vco.read(stored)
    if receipt.get('raw_sha256')!=r['original_sha256'] or receipt.get('raw_bytes')!=r['original_bytes']:
        raise ValueError('original receipt bytes')
    if vco.sha(target)!=r['archive_sha256'] or target.stat().st_size!=r['archive_bytes']:
        raise ValueError('container identity')
    return r,raw,target,manifest

@contextmanager
def restored(work,name):
    r,raw,target,manifest=archive_identity(work,name)
    if raw.exists():raise ValueError('never overwrite a retained or failed restoration')
    pins={p.name:vco.sha(p) for p in (target,manifest,member(work,name,'.json'))}
    digest=hashlib.sha256();count=0
    opener=gzip.open if r['codec']=='gzip9' else lzma.open
    with raw.open('xb') as output,opener(target,'rb') as incoming:
        while block:=incoming.read(archive.CHUNK):
            count+=len(block)
            if count>r['original_bytes']:raise ValueError('restoration exceeds original size')
            digest.update(block);output.write(block)
    if count!=r['original_bytes'] or digest.hexdigest()!=r['original_sha256']:
        raise ValueError('restored original identity')
    event=dict(scene=name,restored_sha256=digest.hexdigest(),restored_bytes=count,
               archive_sha256=r['archive_sha256'],manifest_sha256=vco.sha(manifest),
               passed=False,temporary_retired=False)
    # A failed decode or consumer deliberately retains its new diagnostic raw.
    yield raw,event
    if pins!={p.name:vco.sha(p) for p in (target,manifest,member(work,name,'.json'))}:
        raise ValueError('restoration inputs changed')
    if member(work,name,'.raw')!=raw or vco.sha(raw)!=r['original_sha256']:
        raise ValueError('restored raw changed during observation')
    raw.unlink()
    event.update(passed=True,temporary_retired=True)
