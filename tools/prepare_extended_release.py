"""Freeze a finite continuation from the own 44.442 ms loaded checkpoint."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import once
from joint_cycles_analysis import require
START=23300407296
SPAN=16777216000
CUT=419430400
BOUNDARIES=[0,SPAN];KEY=[0.];SHORT=[False];DECAY=1000.
EXAMPLE='crates/rf-d-circuit/examples/extended_release.rs'
ATTR=b'\n/crates/rf-d-circuit/examples/extended_release.rs text eol=lf\n'
def cuts(phase):
 require(phase==0,'one unchanged phase');return list(range(START+CUT,START+SPAN,CUT))+[START+SPAN]
def caller():
 s=(ROOT/'crates/rf-d-circuit/examples/decay_control.rs').read_text(encoding='utf8')
 s=once(s,'//! Continue released ON history by 8 ms; no new source event.','//! Continue the loaded ON/R=1k history by 32 ms; no new source event.')
 s=s.replace('docs/DECAY_CONTROL_PROTOCOLO.md','docs/VOZ_LIBERACION_EXTENDIDA_PROTOCOLO.md')
 s=once(s,'use rf_d_circuit::{decay_voice as joint,decay_engine as temporal};','use rf_d_circuit::{block_decay_voice as joint,block_decay_engine as temporal};')
 s=once(s,'const START:u64=14911799296;const REL:[u64;2]=[0,8388608000];','const START:u64=23300407296;const REL:[u64;2]=[0,16777216000];')
 s=once(s,'ticks<START+REL[phase as usize]','ticks<14911799296')
 a=s.index('use rf_d_circuit::{conditioned_voice as legacy_joint');b=s.index('fn new_blob(',a)
 s=s[:a]+'use rf_d_circuit::{decay_voice as legacy_joint,decay_engine as legacy_temporal};\n'+s[b:]
 a=s.index(' let raw=fs::read(&args[1])');b=s.index(' for kind in 0..4',a)
 s=s[:a]+''' let raw=fs::read(&args[1]).map_err(|e|e.to_string())?;let restored=decode(&raw)?;
 if restored.q.elapsed_ticks!=START||restored.q.parameters.decay_ohm.to_bits()!=DECAY.to_bits()||encode(restored).as_slice()!=raw.as_slice(){return Err("own final source recipe/bytes".into());}
 let dir=std::path::Path::new(&args[2]);fs::create_dir(dir).map_err(|e|e.to_string())?;fs::write(dir.join("incoming-original.ckp"),&raw).map_err(|e|e.to_string())?;
 // Compare four complete advances with the admitted original assembly at the seam.
 let mut p=legacy_joint::Parameters::from_nominal(rf_d_circuit::conditioned_recipe::Recipe{final_decay:rf_d_circuit::conditioned_recipe::FinalDecay::On,resolution:rf_d_circuit::conditioned_recipe::Resolution::Half2Us}.parameters());p.decay_ohm=DECAY;
 let oq=legacy_temporal::Checkpoint{state:legacy_joint::State{high:restored.q.state.high,low:restored.q.state.low},parameters:p,settings:legacy_temporal::Settings{maximum_half_ticks:restored.q.settings.maximum_half_ticks,attempt_limit:restored.q.settings.attempt_limit},elapsed_ticks:START,next_full_ticks:restored.q.next_full_ticks};
 let mut old=legacy_temporal::Engine::restore(oq).map_err(|e|format!("legacy:{e:?}"))?;let mut ow=legacy_joint::Workspace::new();let mut new=temporal::Engine::restore(restored.q).map_err(|e|format!("optimized:{e:?}"))?;let mut nw=joint::Workspace::new();let mut old_bits=Vec::new();let mut new_bits=Vec::new();
 for _ in 0..4{let a=old.advance_to(&mut ow,START+CUT).map_err(|e|format!("legacy step:{e:?}"))?;let b=new.advance_to(&mut nw,START+CUT).map_err(|e|format!("optimized step:{e:?}"))?;old_bits.extend(old_blob(&a,old.checkpoint()));new_bits.extend(new_blob(&b,new.checkpoint()));}
 if old_bits!=new_bits{return Err("seam full accepted bits".into());}fs::write(dir.join("seam-old.bin"),old_bits).unwrap();fs::write(dir.join("seam-new.bin"),new_bits).unwrap();
 let mut engine=temporal::Engine::restore(restored.q).map_err(|e|format!("own restore:{e:?}"))?;let mut saved=restored;let bytes=encode(saved);let mut workspace=joint::Workspace::new();
'''+s[b:]
 s=once(s,'usage: decay_control <release-final.ckp> <new-output-directory>','usage: extended_release <decay-final.ckp> <new-output-directory>')
 s=once(s,'return Err("1500 s wall budget".into())','return Err("1800 s wall budget".into())')
 return s
def auditor():
 s=(ROOT/'tools/check_decay_control.py').read_text(encoding='utf8')
 s=s.replace('from prepare_decay_control import START,BOUNDARIES,KEY,SHORT,CUT,cuts,DECAY','from prepare_extended_release import START,BOUNDARIES,KEY,SHORT,CUT,cuts,DECAY')
 s=s.replace("published=json.loads((ROOT/'evidence/voice_release_reference01.json')", "published=json.loads((ROOT/'evidence/voice_decay_reference02.json')")
 s=s.replace('22*3728','42*3728').replace('pc==22','pc==42')
 s=once(s,"struct.unpack('<8sQ6IdQ458d',(ROOT/f'references-local/release-voice01/{maximum}/final.ckp').read_bytes())[4]","struct.unpack('<8sQ6IdQd458d',(ROOT/f'references-local/decay-voice02/{maximum}/final.ckp').read_bytes())[4]")
 a=s.index('def seam(p):');b=s.index('# Exact prior flux-observer',a)
 s=s[:a]+'''def seam(p):
 maximum=p['maximum_half_ticks'];directory=ROOT/f'references-local/extended-release01/{maximum}';parent=ROOT/f'references-local/decay-voice02/{maximum}/final.ckp';raw=parent.read_bytes();copy=(directory/'incoming-original.ckp').read_bytes();new=(directory/'checkpoints.bin').read_bytes()[:3728]
 require(raw==copy==new,'all seed metadata, parameters and state preserved by bits');q=checkpoint(new);require(q['ticks']==START and q['decay_ohm']==DECAY,'unchanged electrical recipe');a=(directory/'seam-old.bin').read_bytes();require(a==(directory/'seam-new.bin').read_bytes(),'four complete original/optimized advances by bits')
 return dict(maximum_half_ticks=maximum,parent_path=parent.relative_to(ROOT).as_posix(),parent_sha256=sha(parent),preserved_high_low_values=458,preserved_next_full_ticks=q['next_full'],event_ticks=None,decay_ohm=DECAY,new_source_event=False,complete_accepted_bit_comparisons=4,comparison_bytes=len(a))

'''+s[b:]
 s=s.replace(".replace('release-voice01','decay-voice02')", ".replace('release-voice01','extended-release01')")
 s=s.replace('evidence/voice_decay_native02.json','evidence/voice_extended_native01.json').replace('evidence/voice_decay_inputs01.json','evidence/voice_extended_inputs01.json')
 s=s.replace("parent=json.loads((ROOT/'evidence/voice_release_reference01.json')", "parent=json.loads((ROOT/'evidence/voice_decay_reference02.json')")
 s=s.replace("native['nominal_three_way_identical']","native['seam_bits_identical']")
 s=s.replace('==21 and len(a','==41 and len(a')
 s=once(s,'continued_duration_s=.016,joined_duration_s=.036004','continued_duration_s=.032,joined_duration_s=.068004')
 s=once(s,'nominal_compared_accepted=8,invalid_control_rejections=12,invalid_control_restore_rejections=2,new_source_event=True','seam_compared_accepted=8,new_source_event=False')
 s=s.replace("'tools/check_decay_control.py','tools/decay_audit_body.py','tools/prepare_decay_auditor.py','tools/prepare_decay_control.py'","'tools/check_extended_release.py','tools/prepare_extended_release.py','tools/decay_control_reference.py'")
 s=s.replace("'docs/DECAY_CONTROL_PROTOCOLO.md'","'docs/VOZ_LIBERACION_EXTENDIDA_PROTOCOLO.md'")
 # Parent receipt is separate from the new auditor's output.
 s=s.replace("'evidence/voice_release_reference01.json','evidence/voice_sustained_reference01.json'","'evidence/voice_decay_reference02.json','evidence/voice_sustained_reference01.json'")
 s=s.replace("write('evidence/voice_decay_reference02.json',r)","write('evidence/voice_extended_reference01.json',r)")
 return s
def main():
 qa=json.loads((ROOT/'evidence/voice_block_tests01.json').read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(qa['passed'] and head=='330b7f1bf684e181ce57e900fa3e47a42ec3dbc9','frozen admitted base')
 mutable=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
 require(not (ROOT/'evidence/voice_extended_before01.json').exists(),'exclusive continuation')
 write('evidence/voice_extended_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_block_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
 for n,s in [(EXAMPLE,caller()),('tools/check_extended_release.py',auditor())]:
  require(not (ROOT/n).exists(),'exclusive source');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
 seeds=[]
 for maximum in [1048576,524288]:
  n=f'references-local/decay-voice02/{maximum}/final.ckp';require(sha(ROOT/n)==qa['private_input_sha256'][n],'own frozen final seed');seeds.append(dict(path=n,sha256=sha(ROOT/n),maximum_half_ticks=maximum))
 lib='references-local/voice-block-library02/librf_d_circuit.rlib';require(sha(ROOT/lib)==qa['public_block_library_sha256'],'admitted optimized library')
 write('evidence/voice_extended_inputs01.json',dict(passed=True,seeds=seeds,start_ticks=START,span_ticks=SPAN,end_ticks=START+SPAN,decay_ohm=DECAY,new_source_event=False,source_sha256={n:sha(ROOT/n) for n in [EXAMPLE,'tools/prepare_extended_release.py','tools/check_extended_release.py','docs/VOZ_LIBERACION_EXTENDIDA_PROTOCOLO.md']},private_used_sha256={lib:sha(ROOT/lib),**{s['path']:s['sha256'] for s in seeds}}))
 print('EXTENDED_INPUTS_PREPARED')
if __name__=='__main__':main()
