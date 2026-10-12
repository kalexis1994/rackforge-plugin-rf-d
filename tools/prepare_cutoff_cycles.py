"""Exact continuation inputs and declared caller/wrapper mutations."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/tools/joint_cutoff_cycles_runner.rs text eol=lf\n'
MARKS=[k*131072000 for k in range(2,22)]
CALLER_REPLACEMENTS=[
 ('const GOAL:u64=131072000;const MARKS:[u64;5]=[1048576,8388608,33554432,65536000,131072000];','const GOAL:u64=2752512000;const MARKS:[u64;20]=['+','.join(map(str,MARKS))+'];'),
 ('let v=vco1_startup::startup(controls).map_err(|e|format!("startup:{e:?}"))?.nodes;','let v=[0.;134];'),
 ('q.elapsed_ticks!=0','q.elapsed_ticks!=131072000'),
 ('as_secs_f64()>900.','as_secs_f64()>2400.'),
 ('before.elapsed_ticks==0||before.elapsed_ticks==33554432','before.elapsed_ticks==131072000||before.elapsed_ticks==1310720000'),
 ('if crossings!=0||restores!=2||balance>0.002','if crossings!=2||restores!=2||balance>0.002')]
WRAPPER_REPLACEMENTS=[
 ('voice_candidate_cycles_native01','voice_cutoff_cycles_native01'),('candidate-cycles01','cutoff-cycles01'),
 ('voice_dynamic_direction_tests01','voice_cutoff_temporal_tests01'),('voice_candidate_cycles_inputs01','voice_cutoff_cycles_inputs01'),
 ('run_candidate_cycles.py','run_cutoff_cycles.py'),('prepare_candidate_cycles.py','prepare_cutoff_cycles.py'),
 ('joint_candidate_cycles_runner.rs','joint_cutoff_cycles_runner.rs'),('joint_corrected_cycles_runner.rs','joint_cutoff_temporal_runner.rs'),
 ('VOZ_CANDIDATO_CICLOS_PROTOCOLO','VOZ_CUTOFF_CICLOS_PROTOCOLO'),
 ('5373952000','2752512000'),('7200','2400'),('7400','2600'),('9000','3200'),
 ("str(65000 if maximum==65536 else 100000),str(ROOT/seed['path'])]","str(60000),str(ROOT/seed['path']),'1.0']"),
 ("str(Path(profile['command'][3])/'final.ckp'),match[1]]","str(Path(profile['command'][3])/'final.ckp'),match[1],'1.0']"),
 ('CANDIDATE_PROFILE','CUTOFF_CYCLES_PROFILE'),('CANDIDATE_NATIVE','CUTOFF_CYCLES_NATIVE'),
 ('rf-d/candidate-cycles-native/v1','rf-d/cutoff-cycles-native/v1')]
def rendered(name,replacements):
 s=(ROOT/name).read_text(encoding='utf8')
 for a,b in replacements:require(a in s,'declared substitution '+a);s=s.replace(a,b)
 return s
def main():
 previous='evidence/voice_cutoff_temporal_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='5ebf6a2ac10d01575271e720f6b0004ceaee4f44','base');write('evidence/voice_cutoff_cycles_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 for name,source,changes in [('tools/joint_cutoff_cycles_runner.rs','tools/joint_cutoff_temporal_runner.rs',CALLER_REPLACEMENTS),('tools/run_cutoff_cycles.py','tools/run_candidate_cycles.py',WRAPPER_REPLACEMENTS)]:
  p=ROOT/name;require(not p.exists(),'exclusive generated source');p.write_text(rendered(source,changes),encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);outputs=[]
 for maximum in [65536,32768]:
  name=f'references-local/cutoff-temporal01/1.0-{maximum}/final.ckp';require(sha(ROOT/name)==old['private_input_sha256'][name],'open prefix identity');outputs.append(dict(path=name,sha256=sha(ROOT/name),maximum_half_ticks=maximum))
 write('evidence/voice_cutoff_cycles_inputs01.json',dict(passed=True,outputs=outputs,candidate_path=outputs[0]['path'],candidate_sha256=outputs[0]['sha256'],start_ticks=131072000,goal_ticks=2752512000,marks=MARKS,cutoff_fraction=1.,caller_substitutions=CALLER_REPLACEMENTS,wrapper_substitutions=WRAPPER_REPLACEMENTS,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_cutoff_cycles.py','tools/joint_cutoff_temporal_runner.rs','tools/run_candidate_cycles.py','tools/joint_cutoff_cycles_runner.rs','tools/run_cutoff_cycles.py','docs/VOZ_CUTOFF_CICLOS_PROTOCOLO.md']}));print('CUTOFF_CYCLES_INPUTS',len(outputs))
if __name__=='__main__':main()
