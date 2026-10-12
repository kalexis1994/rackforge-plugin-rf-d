"""Extract the admitted candidate by bytes; declare every caller substitution."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require,checkpoint

ATTR=b'\n/tools/joint_candidate_cycles_runner.rs text eol=lf\n'
REPLACEMENTS=[
 ('const GOAL:u64=2752512000;', 'const GOAL:u64=5373952000;'),
 ('as_secs_f64()>1800.', 'as_secs_f64()>7200.'),
 ('before.elapsed_ticks==ANCHOR||before.elapsed_ticks==9*ANCHOR', 'before.elapsed_ticks==ANCHOR||before.elapsed_ticks==9*ANCHOR||before.elapsed_ticks==29*ANCHOR'),
 ('if crossings<=2 {event=true;}', 'event=true;'),
 ('if balance>0.002 {', 'if crossings!=4||restores!=3||balance>0.002 {'),
 ('if !same(&accepted,&echo)', 'if !same(&accepted,&echo)||!same_bits(&accepted,&echo)'),
 ('fn run(maximum:', '''fn state_bits(a:joint::State,b:joint::State)->bool {
 a.high.into_iter().chain(a.low).zip(b.high.into_iter().chain(b.low)).all(|(x,y)|x.to_bits()==y.to_bits())
}
fn same_bits(a:&Accepted,b:&Accepted)->bool {
 let pairs=[(&a.coarse,&b.coarse),(&a.endpoints[0].pair,&b.endpoints[0].pair),(&a.endpoints[1].pair,&b.endpoints[1].pair)];
 a.error_ratio.to_bits()==b.error_ratio.to_bits()&&pairs.into_iter().all(|(x,y)|x.residual_ratio.to_bits()==y.residual_ratio.to_bits()&&x.correction_ratio.to_bits()==y.correction_ratio.to_bits()&&(0..2).all(|k|state_bits(x.candidates[k],y.candidates[k])&&state_bits(x.increments[k],y.increments[k])))
}
fn run(maximum:''')]

def main():
 previous='evidence/voice_dynamic_direction_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='19a18ad0e44cedeedf39ea7656f6a5882e97ee61','admitted base')
 write('evidence/voice_candidate_cycles_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 name='references-local/dynamic-direction01/own-4.bin';require(sha(ROOT/name)==old['private_input_sha256'][name],'candidate provenance')
 with (ROOT/name).open('rb') as f:
  raw=f.read(3224)
 require(raw[:8]==b'RFJDIRO1' and struct.unpack_from('<IId',raw,8)==(4,42544,1.),'candidate header')
 state=raw[24:3224];require(len(state)==3200,'complete HIGH/LOW state')
 generated=(ROOT/'tools/joint_corrected_cycles_runner.rs').read_text(encoding='utf8')
 for a,b in REPLACEMENTS:require(generated.count(a)==1,'single substitution '+a);generated=generated.replace(a,b)
 p=ROOT/'tools/joint_candidate_cycles_runner.rs';require(not p.exists(),'exclusive caller');p.write_text(generated,encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
 outputs=[]
 for maximum in [65536,32768]:
  p=ROOT/f'references-local/candidate-cycles-seed-{maximum}01.ckp';require(not p.exists(),'exclusive seed');packed=struct.pack('<QIIII',0,2*maximum,maximum,20,0)+state;checkpoint(packed);p.write_bytes(packed);outputs.append(dict(path=p.relative_to(ROOT).as_posix(),maximum_half_ticks=maximum,sha256=sha(p),bytes=len(packed)))
 write('evidence/voice_candidate_cycles_inputs01.json',dict(passed=True,candidate_path=name,candidate_sha256=sha(ROOT/name),state_offset=24,state_bytes=3200,outputs=outputs,goal_ticks=5373952000,substitutions=REPLACEMENTS,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_candidate_cycles.py','tools/joint_corrected_cycles_runner.rs','tools/joint_candidate_cycles_runner.rs','docs/VOZ_CANDIDATO_CICLOS_PROTOCOLO.md']}));print('CANDIDATE_INPUTS',head,len(outputs))
if __name__=='__main__':main()
