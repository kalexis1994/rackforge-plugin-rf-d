"""Declare the finite loaded retrigger by adapting the admitted tail caller/auditor."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import once
from joint_cycles_analysis import require
START=73632055296;BOUNDARIES=[0,2097152,4196401152,8390705152];SPAN=BOUNDARIES[-1];CUT=419430400
KEY=[0.,10.,0.];SHORT=[False,True,False];DECAY=1000.
EXAMPLE='crates/rf-d-circuit/examples/voice_retrigger.rs'
ATTR=b'\n/crates/rf-d-circuit/examples/voice_retrigger.rs text eol=lf\n'
def cuts(phase):
 end=START+BOUNDARIES[phase+1]
 return list(range(START+BOUNDARIES[phase]+CUT,end,CUT))+[end]
def caller():
 s=(ROOT/'crates/rf-d-circuit/examples/long_tail.rs').read_text(encoding='utf8')
 s=s.replace('//! Continue the own loaded assembly history by 64 ms; no new source event.','//! Retrigger the loaded own history: 4 us rest, 8 ms gate, 8 ms release.').replace('VOZ_COLA_LARGA_PROTOCOLO','VOZ_RETRIGGER_PROTOCOLO').replace('const START:u64=40077623296;const REL:[u64;2]=[0,33554432000];','const START:u64=73632055296;const REL:[u64;4]=[0,2097152,4196401152,8390705152];').replace('const KEY:[f64;1]=[0.];const SHORT:[bool;1]=[false];','const KEY:[f64;3]=[0.,10.,0.];const SHORT:[bool;3]=[false,true,false];').replace('phase!=0||u(32)!=1||flags!=1','phase>=3||u(32)!=1||!matches!(flags,1|3)').replace('ticks<14911799296','ticks<START+REL[phase as usize]').replace('usage: long_tail <extended-final.ckp>','usage: voice_retrigger <tail-final.ckp>')
 begin=s.index(' // Compare four complete advances');end=s.index(' let mut engine=temporal::Engine::restore',begin);old=s[begin:end]
 helper=old.replace('restored.q','q').replace('START+CUT','target').replace('elapsed_ticks:START','elapsed_ticks:q.elapsed_ticks').replace('dir.join("seam-old.bin")','dir.join(format!("{name}-old.bin"))').replace('dir.join("seam-new.bin")','dir.join(format!("{name}-new.bin"))')
 helper=helper.replace('p.decay_ohm=DECAY;','p.decay_ohm=q.parameters.decay_ohm;p.keyboard=q.parameters.keyboard;p.short=q.parameters.short;')
 helper='fn compare_previous(q:temporal::Checkpoint,dir:&std::path::Path,name:&str,target:u64)->Result<(),String>{\n'+helper+' Ok(())\n}\n'
 s=s[:begin]+' compare_previous(restored.q,dir,"seam",START+REL[1])?;\n'+s[end:]
 s=once(s,'fn run()->Result<(),String>{',helper+'fn run()->Result<(),String>{')
 s=s.replace('for phase in 0..1{','for phase in 0..3{')
 s=once(s,'let incoming=encode(saved);// Sources are inherited without a new trigger.','let incoming=encode(saved);engine.trigger(KEY[phase],SHORT[phase]).map_err(|e|format!("trigger:{e:?}"))?;')
 s=once(s,'if incoming[56..]!=changed[56..]','if incoming[56..]!=changed[56..]||incoming[8..28]!=changed[8..28]')
 anchor='  let end=START+REL[phase+1];let p=saved.q.parameters;'
 s=once(s,anchor,'  if phase>0{fs::write(dir.join(format!("event{phase}-before.ckp")),incoming).unwrap();fs::write(dir.join(format!("event{phase}-after.ckp")),changed).unwrap();compare_previous(saved.q,dir,&format!("event{phase}"),START+REL[phase+1])?;}\n'+anchor)
 s=s.replace('Saved{q:old,phase:0},format!("phase0-transition{transition_count}.ckp")','Saved{q:old,phase:phase as u32},format!("phase{phase}-transition{transition_count}.ckp")')
 s=s.replace('for target in targets{','let first_target=targets[0];for target in targets{').replace('if target==START+CUT{','if target==first_target{')
 return s
def auditor():
 s=(ROOT/'tools/check_long_tail.py').read_text(encoding='utf8')
 s=s.replace('prepare_long_tail','prepare_voice_retrigger').replace('check_long_tail','check_voice_retrigger').replace('VOZ_COLA_LARGA_PROTOCOLO','VOZ_RETRIGGER_PROTOCOLO').replace('voice_tail_native','voice_retrigger_native').replace('voice_tail_inputs','voice_retrigger_inputs')
 s=s.replace('phase==0 and model==1','phase in range(3) and model==1').replace('flags==1 and reserved','flags in [1,3] and reserved').replace('82*3728','25*3728').replace('pc==82','pc==25').replace('for phase in range(1):','for phase in range(3):')
 s=s.replace("published=json.loads((ROOT/'evidence/voice_extended_reference01.json')", "published=json.loads((ROOT/'evidence/voice_tail_reference01.json')")
 s=s.replace("f'references-local/extended-release01/{maximum}/final.ckp'", "f'references-local/long-tail01/{maximum}/final.ckp'")
 s=s.replace("directory=ROOT/f'references-local/long-tail01/{maximum}'", "directory=ROOT/f'references-local/voice-retrigger01/{maximum}'")
 s=s.replace(".replace('release-voice01','long-tail01')", ".replace('release-voice01','voice-retrigger01')")
 a=s.index('  if phase==1:\n');b=s.index('  count=0;',a);s=s[:a]+s[b:]
 a=s.index(' transition_cps=');b=s.index(' for phase in range(3):',a);trans=s[a:b].replace("glob('phase0-transition*.ckp')", "glob(f'phase{phase}-transition*.ckp')").replace('\n','\n ')
 s=s[:a]+s[b:];s=once(s,' for phase in range(3):\n',' all_transition_count=0\n for phase in range(3):\n  '+trans.strip()+'\n  all_transition_count+=len(transition_cps)\n')
 s=s.replace('2+len(resets)+len(transition_cps)','6+len(resets)+all_transition_count')
 s=s.replace('==81 and len(a','==22 and len(a').replace('continued_duration_s=.064,joined_duration_s=.132004','continued_duration_s=.016004,joined_duration_s=.148008')
 s=s.replace("parent=json.loads((ROOT/'evidence/voice_extended_reference01.json')", "parent=json.loads((ROOT/'evidence/voice_tail_reference01.json')")
 s=s.replace("D(p['phases'][0]['native_integrals_c'][k])", "sum(D(phase['native_integrals_c'][k]) for phase in p['phases'])")
 s=s.replace('seam_compared_accepted=8,new_source_event=False,source_voltage_event=False','seam_compared_accepted=8,event_compared_accepted=16,new_source_event=True,source_voltage_event=True')
 anchor="seams=[seam(p) for p in profiles];flux="
 s=once(s,anchor,"seams=[seam(p) for p in profiles];events=[source_events(p) for p in profiles];flux=")
 s=s.replace('profiles=profiles,seams=seams,same_clock_refinement','profiles=profiles,seams=seams,source_events=events,same_clock_refinement')
 s=s.replace("'evidence/voice_extended_reference01.json'", "'evidence/voice_tail_reference01.json'")
 s=s.replace("write('evidence/voice_tail_reference01.json',r)", "write('evidence/voice_retrigger_reference01.json',r)")
 extra='''\ndef source_events(p):
 directory=ROOT/f"references-local/voice-retrigger01/{p['maximum_half_ticks']}";out=[]
 for phase in [1,2]:
  a=(directory/f'event{phase}-before.ckp').read_bytes();b=(directory/f'event{phase}-after.ckp').read_bytes();u,v=checkpoint(a),checkpoint(b)
  require(a[56:]==b[56:] and a[8:28]==b[8:28] and u['phase']==phase-1 and v['phase']==phase and u['ticks']==v['ticks']==START+BOUNDARIES[phase] and v['key']==KEY[phase] and v['short']==SHORT[phase], 'source event preserves charge clock proposal and resistance')
  old=(directory/f'event{phase}-old.bin').read_bytes();require(old==(directory/f'event{phase}-new.bin').read_bytes() and old,'four complete event advances by bits')
  out.append(dict(phase=phase,ticks=v['ticks'],keyboard_v=v['key'],short=v['short'],preserved_values=458,complete_accepted_bit_comparisons=4,comparison_bytes=len(old)))
 return out
'''
 s=once(s,'def audit():',extra+'\ndef audit():')
 return s
def main():
 qa=json.loads((ROOT/'evidence/voice_tail_tests01.json').read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(qa['passed'] and head=='beef9dae6db96015e6bf7081fb3c5bbc38ac5076','frozen admitted base');require(not (ROOT/'evidence/voice_retrigger_before01.json').exists(),'exclusive retrigger')
 write('evidence/voice_retrigger_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_tail_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 for n,t in [(EXAMPLE,caller()),('tools/check_voice_retrigger.py',auditor())]:require(not (ROOT/n).exists(),'exclusive source');(ROOT/n).write_text(t,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);lib=qa['public_assembly_library_path'];seeds=[]
 for m in [1048576,524288]:
  n=f'references-local/long-tail01/{m}/final.ckp';require(sha(ROOT/n)==qa['private_input_sha256'][n],'own tail seed');seeds.append(dict(path=n,sha256=sha(ROOT/n),maximum_half_ticks=m))
 write('evidence/voice_retrigger_inputs01.json',dict(passed=True,start_ticks=START,end_ticks=START+SPAN,span_ticks=SPAN,boundaries_relative_ticks=BOUNDARIES,keyboard_v=KEY,short=SHORT,decay_ohm=DECAY,new_source_event=True,seeds=seeds,source_sha256={n:sha(ROOT/n) for n in [EXAMPLE,'tools/prepare_voice_retrigger.py','tools/check_voice_retrigger.py','docs/VOZ_RETRIGGER_PROTOCOLO.md']},private_used_sha256={lib:sha(ROOT/lib),**{s['path']:s['sha256'] for s in seeds}}))
 print('RETRIGGER_PREPARED',START+SPAN)
if __name__=='__main__':main()
