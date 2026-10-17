"""Lossless numeric-window codec; modular uint64 differences, never float quantization."""
import base64,hashlib,json,lzma,sys,zlib
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from check_hybrid_voice import packed,unpack
CODEC='f64-u64-delta2-byte-shuffle-xz-base64-v1'
PACK_CODEC='f64-u64-delta2-byte-shuffle-xz-pack-v1'
def encode(item):
    raw=unpack(item['window']);a=np.frombuffer(raw,dtype='<u8').reshape(item['shape']);d=a.copy()
    for _ in range(2):d[1:]=d[1:]-d[:-1]
    b=d.view(np.uint8).reshape(*a.shape,8).transpose(1,2,0).tobytes();p=dict(codec=CODEC,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),payload_base64=base64.b64encode(lzma.compress(b,preset=9)).decode());assert decode(dict(item,window=p))==raw;return p
def decode(item):
    p=item['window']
    if p['codec']=='gzip-base64-v1':return unpack(p)
    assert p['codec'] in [CODEC,PACK_CODEC]
    if p['codec']==CODEC:compressed=base64.b64decode(p['payload_base64'])
    else:
        assert p['pack']=='evidence/vco_cv_load_windows01.xz'
        with(ROOT/p['pack']).open('rb') as f:f.seek(p['offset_bytes']);compressed=f.read(p['compressed_bytes'])
        assert len(compressed)==p['compressed_bytes'] and hashlib.sha256(compressed).hexdigest()==p['compressed_sha256']
    n,cols=item['shape'];b=lzma.decompress(compressed);assert len(b)==n*cols*8;a=np.frombuffer(b,dtype=np.uint8).reshape(cols,8,n).transpose(2,0,1).copy().reshape(n,cols*8).view('<u8').reshape(n,cols)
    for _ in range(2):np.add.accumulate(a,axis=0,out=a)
    raw=a.astype('<u8').tobytes();assert len(raw)==p['raw_bytes'] and hashlib.sha256(raw).hexdigest()==p['raw_sha256'];return raw
def legacy(item):return dict(item,window=packed(decode(item)))
def compact(name):
    p=ROOT/name;original=p.read_bytes();r=json.loads(original);assert r['temporary_area_empty']
    name_pack='evidence/vco_cv_load_windows01.xz';pack=ROOT/name_pack;assert not pack.exists();windows=0
    with pack.open('xb') as sink:
        for group in ['spice','profiles']:
            for x in r[group]:
                old=x['cycle']['window'];q=encode(x['cycle']);compressed=base64.b64decode(q.pop('payload_base64'));q.update(codec=PACK_CODEC,pack=name_pack,offset_bytes=sink.tell(),compressed_bytes=len(compressed),compressed_sha256=hashlib.sha256(compressed).hexdigest());sink.write(compressed);sink.flush();x['cycle']['window']=q;assert legacy(x['cycle'])['window']==old;windows+=1
    restored=json.loads(json.dumps(r))
    for group in ['spice','profiles']:
        for x in restored[group]:x['cycle']['window']=packed(decode(x['cycle']))
    assert(json.dumps(restored,indent=2,ensure_ascii=False)+'\n').encode()==original
    write(p,r);proof=dict(passed=True,path=name,original_json_sha256=hashlib.sha256(original).hexdigest(),original_json_bytes=len(original),compact_json_sha256=sha(p),compact_json_bytes=p.stat().st_size,pack=name_pack,pack_sha256=sha(pack),pack_bytes=pack.stat().st_size,windows=windows,restored_original_json_bitwise_identical=True,all_float64_windows_bitwise_identical=True,unused_samples_removed=False,no_new_trajectory=True,restoration_environment=dict(python_version=sys.version,python_executable=sys.executable,numpy_version=np.__version__,zlib_runtime_version=zlib.ZLIB_RUNTIME_VERSION,zlib_compile_version=zlib.ZLIB_VERSION,byte_order=sys.byteorder,scope='old gzip/JSON bytes restored in this environment; decoded float64 bytes identified independently'))
    write(ROOT/'evidence/vco_cv_load_storage01.json',proof);print('VCO_STORAGE',proof['original_json_bytes'],proof['compact_json_bytes'])
if __name__=='__main__':
    import sys
    compact(sys.argv[1])
