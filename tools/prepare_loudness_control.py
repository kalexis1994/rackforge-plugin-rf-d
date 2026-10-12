"""Extract exact own 205-node final states and declare the control schedule."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/tools/joint_loudness_control_body.rs text eol=lf\n/tools/joint_loudness_control_runner.rs text eol=lf\n'
START=2753560576;SPAN=1048576;SOURCES=[[3.2,.7],[6.,.7],[6.,.01],[.8469345758149237,.01],[3.2,.7]]
def caller():return (ROOT/'tools/joint_loudness_runner.rs').read_text(encoding='utf8').split('fn run()->')[0]+(ROOT/'tools/joint_loudness_control_body.rs').read_text(encoding='utf8')
def native_finals():
 lines=(ROOT/'references-local/joint-loudness02/selected.txt').read_text(encoding='utf8').splitlines();out={};profile=None
 for i,line in enumerate(lines):
  if line.startswith('PROFILE,'):profile=tuple(map(float,line.split(',')[1:4]))
  if line=='FINAL' and profile[:2]==(3.2,.7):out[profile[2]]=list(map(float,lines[i+1].split(',')[1:]))
 require(len(out)==2,'two native own finals');return out
def main():
 previous='evidence/voice_loudness_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));require(old['passed'],'previous QA');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='4270f2faeaa0232c0ae6a641b318d2d5388ae04c','base')
 write('evidence/voice_loudness_control_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 origin='references-local/joint-loudness02/selected.txt';require(sha(ROOT/origin)==old['private_input_sha256'][origin],'protected native origin');ref=json.loads((ROOT/'evidence/voice_loudness_reference01.json').read_text(encoding='utf8'));finals=native_finals();work=ROOT/'references-local/loudness-control-inputs01';require(not work.exists(),'exclusive inputs');work.mkdir();seeds=[]
 for half,h in [(65536,125e-9),(32768,62.5e-9)]:
  values=next(p['final_high_low'] for p in ref['profiles'] if p['c2_v']==3.2 and p['reset_v']==.7 and p['h_s']==h);require(struct.pack('<410d',*values)==struct.pack('<410d',*finals[h]),'reference/native by bits');raw=b'RFLCTL01'+struct.pack('<QII2d410d',START,half,0,3.2,.7,*values);require(len(raw)==3320,'seed codec');p=work/f'{half}.ckp';p.write_bytes(raw);seeds.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),half_ticks=half,source_h_s=h))
 p=ROOT/'tools/joint_loudness_control_runner.rs';require(not p.exists(),'exclusive caller');p.write_text(caller(),encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
 write('evidence/voice_loudness_control_inputs01.json',dict(passed=True,start_ticks=START,phase_span_ticks=SPAN,sources=SOURCES,seeds=seeds,origin_path=origin,origin_sha256=sha(ROOT/origin),source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_loudness_control.py','tools/joint_loudness_control_body.rs','tools/joint_loudness_control_runner.rs','tools/joint_loudness_runner.rs','tools/joint_loudness_kernel.rs','docs/VOZ_SEGUIDOR_CONTROL_PROTOCOLO.md','evidence/voice_loudness_reference01.json']}));print('LOUDNESS_CONTROL_INPUTS',len(seeds))
if __name__=='__main__':main()
