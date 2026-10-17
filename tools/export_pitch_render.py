"""Recover the qualified scene without solving it again; one atomic current WAV."""
import argparse,hashlib,json
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import recover
from check_hybrid_voice import unpack
from check_pitch_render import analyse,parse
from export_long_note_aa import wav_bytes

REFERENCE='evidence/pitch_render_listening01.json'

def prepare(native_name):
    native=json.loads((ROOT/native_name).read_text(encoding='utf8'));assert native['passed'] and native['temporary_area_empty']
    for n,b in recover(native).items():assert(ROOT/n).read_bytes()==b,n
    assert json.dumps(analyse(native['profiles']),sort_keys=True)==json.dumps(native['analysis'],sort_keys=True)
    fine=native['profiles'][1];d,a=parse(unpack(fine['stdout']));samples=a['AA8'][:14400];data=wav_bytes(samples);h=hashlib.sha256(data).hexdigest();assert h==fine['wav_sha256']
    restored=np.frombuffer(data[56:],dtype='<f4').astype(float);roundtrip=float(max(abs(restored-samples)));assert roundtrip<=1e-9
    old=json.loads((ROOT/'evidence/pitch_program_tests01.json').read_text(encoding='utf8'));path='artifacts/rf-d-nominal-current.wav';assert path not in old['private_input_sha256']
    return data,dict(passed=True,native=native_name,native_sha256=sha(ROOT/native_name),path=path,sha256=h,bytes=len(data),frames=14400,rate_hz=48000,channels=1,format='IEEE-float32',duration_s=.3,electrical_end_s=.301,maximum_step_us=.5,frequency_ratios=[1.,1.5,.5],retune_times_s=[.1,.2],key_on_s=.001,key_off_s=.25,v_per_full_scale=1.,normalized=False,faded=False,dithered=False,physical_cv_model=False,real_time=False,regenerable=True,required_private_input=False,previous_sha256=old['new_listening']['sha256'],previous_regenerator='python -B tools/export_long_note_aa.py',regenerator='python -B tools/export_pitch_render.py',complete=d['complete'],final_state=d['state'],float32_roundtrip_max_error_v=roundtrip,peak_v=float(max(abs(samples))))

def reference(native_name=None):
    path=ROOT/REFERENCE
    if path.exists():
        stored=json.loads(path.read_text(encoding='utf8'));assert native_name is None or native_name==stored['native'];data,meta=prepare(stored['native']);assert stored==meta;return data,meta
    if native_name is None:raise ValueError('first qualification requires --native evidence/pitch_render_nativeNN.json')
    data,meta=prepare(native_name);write(path,meta);return data,meta

def main():
    ap=argparse.ArgumentParser(description='Recuperar escena experimental admitida sin otra integracion; sustituye unica escucha actual.');ap.add_argument('--native');args=ap.parse_args();data,meta=reference(args.native)
    from render_pitch import Laboratory,promote
    with Laboratory() as lab:
        stage=lab.own('render.wav.part');stage.write_bytes(data);output=promote(stage)
    print('PITCH_LISTENING',output['path'],output['sha256'])
if __name__=='__main__':main()
