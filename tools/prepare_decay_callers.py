"""Public controlled caller and a frozen-library comparator from declared sources."""
from prepare_vco1_portable import ROOT
from prepare_release_voice import once
from prepare_decay_control import RUST
from joint_cycles_analysis import require

def blob_function(name,namespace):
 return f'''fn {name}(a:&{namespace}::Accepted,q:{namespace}::Checkpoint)->Vec<u8>{{
 let mut b=Vec::new();for p in [&a.coarse,&a.endpoints[0].pair,&a.endpoints[1].pair]{{
  for s in p.candidates.iter().chain(p.increments.iter()){{for v in s.high.iter().chain(s.low.iter()){{b.extend_from_slice(&v.to_le_bytes());}}}}
  for v in [p.residual_ratio,p.correction_ratio]{{b.extend_from_slice(&v.to_le_bytes());}}for v in [p.iterations,p.trials]{{b.extend_from_slice(&(v as u64).to_le_bytes());}}
 }}
 for ep in &a.endpoints{{b.extend_from_slice(&ep.elapsed_ticks.to_le_bytes());let o=ep.observations;for v in [o.saw_v,o.ramp_v,o.bus_v,o.cursor_v,o.j7_v,o.panel_current_a,o.series_current_a,o.c27_current_a,o.bus_kcl_a]{{b.extend_from_slice(&v.to_le_bytes());}}}}
 b.extend_from_slice(&a.half_ticks.to_le_bytes());b.extend_from_slice(&a.error_ratio.to_le_bytes());b.extend_from_slice(&a.attempts.to_le_bytes());
 for v in q.state.high.iter().chain(q.state.low.iter()){{b.extend_from_slice(&v.to_le_bytes());}}b.extend_from_slice(&q.elapsed_ticks.to_le_bytes());for v in [q.settings.maximum_half_ticks,q.settings.attempt_limit,q.next_full_ticks]{{b.extend_from_slice(&v.to_le_bytes());}}
 b.extend_from_slice(&q.parameters.keyboard.to_le_bytes());b.push(q.parameters.final_decay as u8);b.push(q.parameters.short as u8);b
}}
'''

def callers():
 source=(ROOT/'crates/rf-d-circuit/examples/release_continuation.rs').read_text(encoding='utf8');prefix=source[:source.index('const PARENT_START')]
 legacy=prefix+blob_function('nominal_blob','temporal')+'''fn main(){let args:Vec<_>=std::env::args().collect();let q=decode(&fs::read(&args[1]).unwrap()).unwrap().q;let dir=std::path::Path::new(&args[2]);fs::create_dir(dir).unwrap();let mut e=temporal::Engine::restore(q).unwrap();let mut w=joint::Workspace::new();let mut out=Vec::new();for _ in 0..4{let a=e.advance_to(&mut w,q.elapsed_ticks+419430400).unwrap();out.extend(nominal_blob(&a,e.checkpoint()));}fs::write(dir.join("nominal.bin"),out).unwrap();eprintln!("NOMINAL_LEGACY,{},4",q.settings.maximum_half_ticks);}
'''
 # Preserve an independent nominal decoder in the public new caller.
 decoder=prefix[prefix.index('fn decode('):prefix.index('fn observations(')]
 decoder=decoder.replace('fn decode(','fn incoming_decode(').replace('Result<Saved','Result<LegacySaved').replace('Ok(Saved','Ok(LegacySaved').replace('joint::','legacy_joint::').replace('temporal::','legacy_temporal::').replace('scene()','legacy_scene()').replace('SIZE','3720').replace('START','OLD_START').replace('REL[','OLD_REL[')
 prefix=prefix.replace('conditioned_voice as joint,conditioned_engine as temporal','decay_voice as joint,decay_engine as temporal')
 prefix=prefix.replace('VOZ_LIBERACION_PROTOCOLO','DECAY_CONTROL_PROTOCOLO')
 prefix=once(prefix,'}.parameters()','}.parameters())');prefix=once(prefix,' rf_d_circuit::conditioned_recipe::Recipe',' joint::Parameters::from_nominal(rf_d_circuit::conditioned_recipe::Recipe')
 prefix=once(prefix,'const START:u64=10717495296;const REL:[u64;2]=[0,4194304000];const CUT:u64=157286400;const SIZE:usize=3720;','const START:u64=14911799296;const REL:[u64;2]=[0,8388608000];const CUT:u64=419430400;const SIZE:usize=3728;const DECAY:f64=1000.;')
 prefix=prefix.replace('RFREL001','RFDCY001').replace('b[56+8*k..64+8*k]','b[64+8*k..72+8*k]')
 prefix=once(prefix,'let mut p=scene();','let mut p=scene();p.decay_ohm=f64::from_le_bytes(b[56..64].try_into().unwrap());if !joint::Parameters::valid_decay(p.decay_ohm){return Err("decay resistance".into());}')
 prefix=once(prefix,'b[40..48].copy_from_slice(&q.parameters.keyboard.to_le_bytes());','b[40..48].copy_from_slice(&q.parameters.keyboard.to_le_bytes());b[56..64].copy_from_slice(&q.parameters.decay_ohm.to_le_bytes());')
 prefix=once(prefix,'p.keyboard,p.final_decay,p.short).map_err','p.keyboard,p.final_decay,p.short,p.decay_ohm).map_err')
 prefix+='''use rf_d_circuit::{conditioned_voice as legacy_joint,conditioned_engine as legacy_temporal};
const OLD_START:u64=10717495296;const OLD_REL:[u64;2]=[0,4194304000];
#[derive(Clone,Copy)]struct LegacySaved{q:legacy_temporal::Checkpoint,phase:u32}
fn legacy_scene()->legacy_joint::Parameters{rf_d_circuit::conditioned_recipe::Recipe{final_decay:rf_d_circuit::conditioned_recipe::FinalDecay::On,resolution:rf_d_circuit::conditioned_recipe::Resolution::Half2Us}.parameters()}
'''+decoder+blob_function('new_blob','temporal')+blob_function('old_blob','legacy_temporal')
 observers=(ROOT/'tools/release_observers.rs').read_text(encoding='utf8').replace('/100000.','/DECAY')
 body=source[source.index('// Offline replay storage'):]
 a=body.index(' let args:Vec<_>');b=body.index(' for kind in 0..4')
 body=body[:a]+''' let args:Vec<_>=std::env::args().collect();if args.len()!=3{return Err("usage: decay_control <release-final.ckp> <new-output-directory>".into());}
 let raw=fs::read(&args[1]).map_err(|e|e.to_string())?;let incoming=incoming_decode(&raw)?;
 if incoming.phase!=0||incoming.q.elapsed_ticks!=START||!incoming.q.parameters.final_decay||incoming.q.parameters.keyboard!=0.||incoming.q.parameters.short{return Err("released source recipe".into());}
 let restored=Saved{q:temporal::Checkpoint{state:joint::State{high:incoming.q.state.high,low:incoming.q.state.low},parameters:joint::Parameters::from_nominal(incoming.q.parameters),settings:temporal::Settings{maximum_half_ticks:incoming.q.settings.maximum_half_ticks,attempt_limit:incoming.q.settings.attempt_limit},elapsed_ticks:incoming.q.elapsed_ticks,next_full_ticks:incoming.q.next_full_ticks},phase:0};
 let dir=std::path::Path::new(&args[2]);fs::create_dir(dir).map_err(|e|e.to_string())?;fs::write(dir.join("incoming-original.ckp"),raw).map_err(|e|e.to_string())?;
 // Finite nominal regression before changing the electrical resistance.
 let mut old=legacy_temporal::Engine::restore(incoming.q).map_err(|e|format!("legacy:{e:?}"))?;let mut ow=legacy_joint::Workspace::new();let mut new=temporal::Engine::restore(restored.q).map_err(|e|format!("nominal:{e:?}"))?;let mut nw=joint::Workspace::new();let mut old_bits=Vec::new();let mut new_bits=Vec::new();
 for _ in 0..4{let a=old.advance_to(&mut ow,START+CUT).map_err(|e|format!("legacy step:{e:?}"))?;let b=new.advance_to(&mut nw,START+CUT).map_err(|e|format!("nominal step:{e:?}"))?;old_bits.extend(old_blob(&a,old.checkpoint()));new_bits.extend(new_blob(&b,new.checkpoint()));}
 if old_bits!=new_bits{return Err("nominal full accepted bits".into());}fs::write(dir.join("nominal-old.bin"),old_bits).unwrap();fs::write(dir.join("nominal-new.bin"),new_bits).unwrap();
 let mut engine=temporal::Engine::restore(restored.q).map_err(|e|format!("own restore:{e:?}"))?;let before=encode(restored);fs::write(dir.join("incoming-nominal.ckp"),before).unwrap();
 for ohm in [0.,-1.,f64::NAN,f64::INFINITY,1000001.,f64::from_bits(1)]{if engine.set_decay_ohm(ohm).is_ok()||encode(Saved{q:engine.checkpoint(),phase:0})!=before{return Err("invalid decay mutated checkpoint".into());}}
 let mut invalid=restored.q;invalid.parameters.decay_ohm=f64::NAN;if temporal::Engine::restore(invalid).is_ok(){return Err("invalid restore decay".into());}
 engine.set_decay_ohm(DECAY).map_err(|e|format!("decay event:{e:?}"))?;let mut saved=Saved{q:engine.checkpoint(),phase:0};let bytes=encode(saved);let mut expected=before;expected[56..64].copy_from_slice(&DECAY.to_le_bytes());if bytes!=expected{return Err("control event changed state/source/clock".into());}
 fs::write(dir.join("control-event.txt"),format!("DECAY_CONTROL,{START},100000,1000\\n")).unwrap();let mut workspace=joint::Workspace::new();
''' +body[b:]
 body=body.replace('b[56+8*225..64+8*225]','b[64+8*225..72+8*225]')
 body=body.replace('1500.','1800.')
 return {RUST[3]:prefix+observers+body,RUST[4]:legacy}

def main():
 for n,s in callers().items():require(not (ROOT/n).exists(),'exclusive controlled caller');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 print('DECAY_CALLERS_PREPARED')
if __name__=='__main__':main()
