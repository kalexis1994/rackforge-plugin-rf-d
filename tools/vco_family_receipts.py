"""Exact gzip JSON storage; logical receipt bytes remain bound by SHA256."""
import gzip,hashlib,json
from prepare_dual_chain import ROOT,sha,write
INDEX='evidence/vco_family_receipt_storage01.json'
def receipt_bytes(name):
    p=ROOT/name
    if p.exists():return p.read_bytes()
    index=json.loads((ROOT/INDEX).read_text(encoding='utf8'));x=index['items'][name];blob=(ROOT/x['archive']).read_bytes()
    assert hashlib.sha256(blob).hexdigest()==x['archive_sha256'];raw=gzip.decompress(blob)
    assert len(raw)==x['original_bytes'] and hashlib.sha256(raw).hexdigest()==x['original_sha256'];return raw
def read(name):return json.loads(receipt_bytes(name))
def logical_sha(name):return hashlib.sha256(receipt_bytes(name)).hexdigest()
def main():
    out={};saved=0
    for name in ['evidence/vco_family_oracle01.json','evidence/vco_family_oracle02.json','evidence/vco_family_oracle03.json']:
        p=ROOT/name;raw=p.read_bytes();archive=name+'.gz';q=ROOT/archive;assert not q.exists();blob=gzip.compress(raw,compresslevel=9,mtime=0);q.write_bytes(blob);assert gzip.decompress(q.read_bytes())==raw
        out[name]=dict(archive=archive,archive_sha256=sha(q),archive_bytes=len(blob),original_sha256=sha(p),original_bytes=len(raw),all_original_json_bytes_restored=True);saved+=len(raw)-len(blob)
    write(ROOT/INDEX,dict(passed=True,items=out,saved_bytes=saved,lossless=True,numeric_changes=False))
    for n in out:
        p=(ROOT/n).resolve();assert p.parent==(ROOT/'evidence').resolve() and p.suffix=='.json';p.unlink();assert logical_sha(n)==out[n]['original_sha256']
    print('FAMILY_RECEIPT_STORAGE',saved,'bytes saved; all original JSON bytes restored')
if __name__=='__main__':main()
