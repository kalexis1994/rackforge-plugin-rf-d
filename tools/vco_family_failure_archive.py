"""Exact storage deduplication of the two identical rejected/replay windows."""
import hashlib,json
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
ORIGINAL='evidence/vco_family_windows01.xz'
ARCHIVE='evidence/vco_family_failed_windows01.xz'
RECEIPT='evidence/vco_family_failure_storage01.json'
def restore_bytes():
    r=json.loads((ROOT/RECEIPT).read_text(encoding='utf8'));p=(ROOT/r['archive']).read_bytes()
    assert hashlib.sha256(p).hexdigest()==r['archive_sha256']
    raw=p*r['repeat'];assert len(raw)==r['original_bytes'] and hashlib.sha256(raw).hexdigest()==r['original_sha256']
    return raw
def main():
    r=json.loads((ROOT/'evidence/vco_family_oracle01.json').read_text(encoding='utf8'));assert not r['passed'] and r['pack']==ORIGINAL
    x=r['failed_process']['window'];y=r['replay_process']['window'];assert x['offset_bytes']==0 and y['offset_bytes']==x['compressed_bytes'] and x['compressed_bytes']==y['compressed_bytes'] and x['compressed_sha256']==y['compressed_sha256']
    original=(ROOT/ORIGINAL).read_bytes();assert len(original)==2*x['compressed_bytes'] and sha(ROOT/ORIGINAL)==r['pack_sha256']
    half=original[:x['compressed_bytes']];assert original==half+half
    out=ROOT/ARCHIVE;assert not out.exists();out.write_bytes(half);assert out.read_bytes()*2==original
    receipt=dict(passed=True,**Sources(['tools/vco_family_failure_archive.py']).fields(),original=ORIGINAL,original_sha256=hashlib.sha256(original).hexdigest(),original_bytes=len(original),archive=ARCHIVE,archive_sha256=sha(out),archive_bytes=len(half),repeat=2,saved_bytes=len(half),all_original_pack_bytes_restored=True,original_json_unchanged=True,quantization=False,sample_removal=False,reason='Two byte-identical compressed failure/replay windows share physical storage; keep frozen 32 MiB total evidence budget')
    write(ROOT/RECEIPT,receipt);assert restore_bytes()==original
    p=(ROOT/ORIGINAL).resolve();assert p.parent==(ROOT/'evidence').resolve() and p.name=='vco_family_windows01.xz';p.unlink()
    print('FAMILY_FAILURE_ARCHIVE',len(original),len(half),'full pack bitwise restorable')
if __name__=='__main__':main()
