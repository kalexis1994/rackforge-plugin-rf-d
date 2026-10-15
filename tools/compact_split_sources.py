"""Losslessly share repeated source images; reconstruct the measured receipt bytes."""
import hashlib,json,sys,zlib,gzip,inspect
from prepare_dual_chain import ROOT,sha,write
from check_hybrid_voice import packed,unpack
BASE='evidence/split_ladder_native01.json'
TARGET='evidence/split_ladder_native02.json'
CODEC='rf-d/shared-failed-sources-v1'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def images(r):
    p=r['failed_sources']
    if p['codec']!=CODEC:return json.loads(unpack(p))
    assert p['base_receipt']==BASE and sha(ROOT/BASE)==p['base_receipt_sha256']
    base=json.loads(unpack(read(BASE)['failed_sources']));changes=json.loads(unpack(p['replacements']))
    assert set(changes)<=set(base)
    base.update(changes);raw=json.dumps(base,sort_keys=True).encode();assert hashlib.sha256(raw).hexdigest()==p['original_descriptor']['raw_sha256']
    assert len(raw)==p['original_descriptor']['raw_bytes'];return base
def expanded_bytes(r):
    if r.get('failed_sources',{}).get('codec')!=CODEC:
        return (json.dumps(r,indent=2,ensure_ascii=False)+'\n').encode('utf8')
    p=r['failed_sources'];raw=json.dumps(images(r),sort_keys=True).encode();full=packed(raw)
    assert {k:v for k,v in full.items() if k!='payload_base64'}==p['original_descriptor']
    assert hashlib.sha256(full['payload_base64'].encode()).hexdigest()==p['original_payload_base64_sha256']
    out=dict(r);out['failed_sources']=full
    return (json.dumps(out,indent=2,ensure_ascii=False)+'\n').encode('utf8')
def main():
    proof=ROOT/'evidence/split_ladder_compaction01.json';assert not proof.exists()
    original=(ROOT/TARGET).read_bytes();r=read(TARGET);base=images(read(BASE));current=images(r);assert set(base)==set(current)
    differences={n:v for n,v in current.items() if v!=base[n]};p=r['failed_sources'];assert p['codec']=='gzip-base64-v1'
    r['failed_sources']=dict(codec=CODEC,base_receipt=BASE,base_receipt_sha256=sha(ROOT/BASE),replacements=packed(json.dumps(differences,sort_keys=True).encode()),original_descriptor={k:v for k,v in p.items() if k!='payload_base64'},original_payload_base64_sha256=hashlib.sha256(p['payload_base64'].encode()).hexdigest())
    assert expanded_bytes(r)==original
    write(ROOT/TARGET,r);assert expanded_bytes(read(TARGET))==original
    write(proof,dict(passed=True,source_sha256={'tools/compact_split_sources.py':sha(ROOT/'tools/compact_split_sources.py')},target=TARGET,base_receipt=BASE,base_receipt_sha256=sha(ROOT/BASE),original_sha256=hashlib.sha256(original).hexdigest(),original_bytes=len(original),compact_sha256=sha(ROOT/TARGET),compact_bytes=(ROOT/TARGET).stat().st_size,original_byte_reconstruction_exact=True,replaced_source_names=sorted(differences),shared_source_count=len(current)-len(differences),budget_bytes=8*1024*1024,reconstruction_runtime=dict(python=sys.version,implementation=sys.implementation.name,zlib_runtime=zlib.ZLIB_RUNTIME_VERSION,gzip_default_compresslevel=inspect.signature(gzip.compress).parameters['compresslevel'].default)))
    print('LOSSLESS_SHARED_SOURCES',len(original),(ROOT/TARGET).stat().st_size,'shared',len(current)-len(differences),'changed',len(differences))
if __name__=='__main__':main()
