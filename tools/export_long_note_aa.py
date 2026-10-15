"""One current float WAV; unity V-to-FS convention, no peak normalization."""
import hashlib,json,struct,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from check_long_note_aa import arrays
ARTIFACT='artifacts/rf-d-nominal-current.wav'
def wav_bytes(samples):
    assert len(samples)==14400 and np.isfinite(samples).all() and max(abs(samples))<1
    payload=samples.astype('<f4').tobytes();fmt=struct.pack('<HHIIHH',3,1,48000,192000,4,32)
    chunks=b'fmt '+struct.pack('<I',16)+fmt+b'fact'+struct.pack('<II',4,len(samples))+b'data'+struct.pack('<I',len(payload))+payload
    return b'RIFF'+struct.pack('<I',4+len(chunks))+b'WAVE'+chunks
def prepare():
    names=['evidence/long_note_aa_native01.json','evidence/long_note_aa_design01.json','evidence/long_note_aa_filter01.json','evidence/long_note_aa_audit01.json']
    for n in names:assert json.loads((ROOT/n).read_text())['passed'],n
    native=json.loads((ROOT/names[0]).read_text());d,a,seam,g=arrays(unpack(native['profiles'][1]['stdout']));samples=a['AA8'][:14400];data=wav_bytes(samples)
    restored=np.frombuffer(data[56:],dtype='<f4').astype(float);roundtrip=float(max(abs(restored-samples)));assert roundtrip<=1e-9
    assert not list((ROOT/'tmp/lab-current').iterdir());old=json.loads((ROOT/'evidence/j7_readout_tests01.json').read_text());assert ARTIFACT not in old['private_input_sha256']
    r=dict(inputs={n:sha(ROOT/n) for n in names},path=ARTIFACT,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),frames=14400,rate_hz=48000,channels=1,format='IEEE-float32',duration_s=.3,v_per_full_scale=1.,peak_v=float(max(abs(samples))),float32_roundtrip_max_error_v=roundtrip,normalized=False,faded=False,dithered=False,regenerable=True,required_private_input=False,new_private_input_ids=0,temporary_area_empty=True)
    return data,r
def main():
    sources=Sources(['tools/export_long_note_aa.py','tools/check_long_note_aa.py','docs/LONG_NOTE_AA_PROTOCOLO.md']);r=dict(passed=False,**sources.fields())
    try:data,metadata=prepare();r.update(metadata)
    except Exception:
        r['failure']=traceback.format_exc()
        try:prepare();r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
        sources.unchanged();k=1
        while(ROOT/f'evidence/long_note_aa_listening_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/long_note_aa_listening_failure{k:02d}.json',r);raise
    receipt=ROOT/'evidence/long_note_aa_listening01.json'
    if receipt.exists():
        existing=json.loads(receipt.read_text());assert existing['passed'] and existing['source_sha256']==sources.hashes
        assert all(existing[k]==v for k,v in metadata.items())
    p=ROOT/ARTIFACT;p.parent.mkdir(exist_ok=True);p.write_bytes(data);assert p.read_bytes()==data;sources.unchanged();r['passed']=True
    if not receipt.exists():write(receipt,r)
    print('LONG_NOTE_AA_LISTENING',ARTIFACT,len(data),r['float32_roundtrip_max_error_v'],flush=True)
if __name__=='__main__':main()
