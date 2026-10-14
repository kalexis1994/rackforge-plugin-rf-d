"""Fork only the unchanged open branch from the exact pre-cutoff checkpoint."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import once
from joint_cycles_analysis import require
START=82024857600;SPAN=4194304000;BOUNDARIES=[0,SPAN];CUT=419430400
KEY=[0.];SHORT=[False];DECAY=1000.;ALPHA=[1.]
EXAMPLE='crates/rf-d-circuit/examples/cutoff_ab.rs';ATTR=b'\n/crates/rf-d-circuit/examples/cutoff_ab.rs text eol=lf\n'
def cuts(phase):require(phase==0,'one open phase');return list(range(START+CUT,START+SPAN,CUT))+[START+SPAN]
def caller():
 s=(ROOT/'crates/rf-d-circuit/examples/voice_cutoff.rs').read_text(encoding='utf8').replace('//! Loaded cutoff: 4 us continuity, 8 ms alpha=0.5, 8 ms alpha=1.','//! Counterfactual open branch from the exact pre-cutoff state; 8 ms.').replace('VOZ_CUTOFF_PROTOCOLO','VOZ_CUTOFF_AB_PROTOCOLO').replace('const START:u64=82022760448;const REL:[u64;4]=[0,2097152,4196401152,8390705152];','const START:u64=82024857600;const REL:[u64;2]=[0,4194304000];').replace('const KEY:[f64;3]=[0.;3];const SHORT:[bool;3]=[false;3];const ALPHA:[f64;3]=[1.,0.5,1.];','const KEY:[f64;1]=[0.];const SHORT:[bool;1]=[false];const ALPHA:[f64;1]=[1.];').replace('phase>=3','phase>=1').replace('for phase in 0..3{','for phase in 0..1{').replace('usage: voice_cutoff <retrigger-final.ckp>','usage: cutoff_ab <cutoff-event1-before.ckp>')
 a=s.index(' if raw.len()!=3728');b=s.index(' if restored.q.elapsed_ticks',a)
 s=s[:a]+' let restored=decode(&raw)?;\n'+s[b:];s=s.replace('encode(restored)!=converted','encode(restored).as_slice()!=raw.as_slice()');return s
def auditor():
 s=(ROOT/'tools/check_voice_cutoff.py').read_text(encoding='utf8');s=s[:s.index('def seam(p):')]
 s=s.replace('prepare_voice_cutoff','prepare_cutoff_ab').replace("and phase in range(3) and","and phase==0 and").replace('for phase in range(3):','for phase in range(1):').replace('25*3736','12*3736').replace('pc==25','pc==12').replace('6+len(resets)+all_transition_count','2+len(resets)+all_transition_count')
 s=s.replace("published=json.loads((ROOT/'evidence/voice_retrigger_reference01.json')", "published=json.loads((ROOT/'evidence/voice_cutoff_reference01.json')").replace("own['grids'][-1]['values']", "own['grids'][1]['values']")
 s=s.replace("struct.unpack('<8sQ6IdQd458d',(ROOT/f'references-local/voice-retrigger01/{maximum}/final.ckp').read_bytes())[4]", "struct.unpack('<8sQ6IdQ2d458d',(ROOT/f'references-local/voice-cutoff01/{maximum}/event1-before.ckp').read_bytes())[4]")
 return s+(ROOT/'tools/cutoff_ab_audit.py').read_text(encoding='utf8')
def main():
 qa=json.loads((ROOT/'evidence/voice_cutoff_tests01.json').read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(qa['passed'] and head=='14bbce669f4569d434cdafac436e4a866a5ab6ca','frozen base');require(not (ROOT/'evidence/cutoff_ab_before01.json').exists(),'exclusive A/B')
 write('evidence/cutoff_ab_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_cutoff_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 for n,t in [(EXAMPLE,caller()),('tools/check_cutoff_ab.py',auditor())]:require(not (ROOT/n).exists(),'exclusive source');compile(t,n,'exec') if n.endswith('.py') else None;(ROOT/n).write_text(t,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);lib=qa['public_assembly_library_path'];seeds=[]
 for m in [1048576,524288]:
  n=f'references-local/voice-cutoff01/{m}/event1-before.ckp';require(sha(ROOT/n)==qa['private_input_sha256'][n],'own common seed');seeds.append(dict(path=n,sha256=sha(ROOT/n),maximum_half_ticks=m))
 write('evidence/cutoff_ab_inputs01.json',dict(passed=True,start_ticks=START,end_ticks=START+SPAN,span_ticks=SPAN,new_source_event=False,open_cutoff_fraction=1.,closed_cutoff_fraction=.5,closed_phase=1,seeds=seeds,source_sha256={n:sha(ROOT/n) for n in [EXAMPLE,'tools/prepare_cutoff_ab.py','tools/check_cutoff_ab.py','tools/cutoff_ab_audit.py','docs/VOZ_CUTOFF_AB_PROTOCOLO.md']},private_used_sha256={lib:sha(ROOT/lib),**{s['path']:s['sha256'] for s in seeds}}));print('CUTOFF_AB_PREPARED')
if __name__=='__main__':main()
