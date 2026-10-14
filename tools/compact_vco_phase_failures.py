"""Lossless compact receipts, including original sources, fixtures and replay."""
import base64,gzip,hashlib,json
from prepare_dual_chain import ROOT,sha,write
def decoded(path):
    data=json.loads(path.read_text(encoding='utf8'))
    if data.get('codec')=='gzip-json-v1':
        raw=gzip.decompress(base64.b64decode(data['payload_base64']))
        assert hashlib.sha256(raw).hexdigest()==data['original_sha256']
        return json.loads(raw)
    return data
def main():
    out=ROOT/'evidence/vco_phase_failure_storage01.json';assert not out.exists();records=[]
    for k in [1,2,3]:
        path=ROOT/f'evidence/vco_phase_native{k:02d}.json';raw=path.read_bytes();old=json.loads(raw);assert not old['passed']
        compressed=gzip.compress(raw,compresslevel=6,mtime=0);assert gzip.decompress(compressed)==raw
        wrapper=dict(codec='gzip-json-v1',passed=False,original_sha256=hashlib.sha256(raw).hexdigest(),original_bytes=len(raw),payload_base64=base64.b64encode(compressed).decode())
        write(path,wrapper);assert json.dumps(decoded(path),sort_keys=True,separators=(',',':'))==json.dumps(old,sort_keys=True,separators=(',',':'))
        records.append(dict(path=path.relative_to(ROOT).as_posix(),original_sha256=wrapper['original_sha256'],original_bytes=len(raw),stored_sha256=sha(path),stored_bytes=path.stat().st_size,restitution_exact=True))
    write(out,dict(passed=True,source_sha256={'tools/compact_vco_phase_failures.py':sha(ROOT/'tools/compact_vco_phase_failures.py')},records=records,original_bytes=sum(v['original_bytes'] for v in records),stored_bytes=sum(v['stored_bytes'] for v in records)))
    print('VCO_PHASE_FAILURE_STORAGE',sum(v['original_bytes'] for v in records),sum(v['stored_bytes'] for v in records))
if __name__=='__main__':main()
