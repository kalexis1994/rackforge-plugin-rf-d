"""Pair the unchanged engine with the quadrant assembly at every Accepted."""
from prepare_vco1_portable import ROOT
from prepare_release_voice import once
from joint_cycles_analysis import require
RUST=['tools/voice_block_engine.rs','tools/voice_pivot_paired.rs']
ATTR=b'\n/tools/voice_block_engine.rs text eol=lf\n'

def engine():return (ROOT/'crates/rf-d-circuit/src/decay_engine.rs').read_text(encoding='utf8').replace('crate::decay_voice','crate::candidate')

def paired(public=False):
 old=(ROOT/'crates/rf-d-circuit/examples/decay_control.rs').read_text(encoding='utf8');s=old[:old.index('use rf_d_circuit::{conditioned_voice as legacy_joint')]
 s=once(s,'use rf_d_circuit::{decay_voice','pub use rf_d_circuit::*;\nuse rf_d_circuit::{decay_voice')
 aliases='use rf_d_circuit::{block_decay_voice as candidate,block_decay_engine as alt};\n' if public else '#[path="voice_block_kernel.rs"] mod candidate;\n#[path="voice_block_engine.rs"] mod alt;\n'
 s+=aliases
 s+='''
fn as_old(s:candidate::State)->joint::State{joint::State{high:s.high,low:s.low}}
fn fast_encode(q:alt::Checkpoint)->[u8;SIZE]{let mut p=scene();p.decay_ohm=q.parameters.decay_ohm;p.keyboard=q.parameters.keyboard;p.short=q.parameters.short;p.final_decay=q.parameters.final_decay;encode(Saved{q:temporal::Checkpoint{state:as_old(q.state),parameters:p,settings:temporal::Settings{maximum_half_ticks:q.settings.maximum_half_ticks,attempt_limit:q.settings.attempt_limit},elapsed_ticks:q.elapsed_ticks,next_full_ticks:q.next_full_ticks},phase:0})}
fn pair_equal(a:&joint::Pair,b:&candidate::Pair)->bool{a.residual_ratio.to_bits()==b.residual_ratio.to_bits()&&a.correction_ratio.to_bits()==b.correction_ratio.to_bits()&&a.iterations==b.iterations&&a.trials==b.trials&&a.candidates.iter().chain(a.increments.iter()).zip(b.candidates.iter().chain(b.increments.iter())).all(|(a,b)|a.high.iter().chain(a.low.iter()).zip(b.high.iter().chain(b.low.iter())).all(|(a,b)|a.to_bits()==b.to_bits()))}
fn amotor(o:alt::Observations)->[f64;9]{[o.saw_v,o.ramp_v,o.bus_v,o.cursor_v,o.j7_v,o.panel_current_a,o.series_current_a,o.c27_current_a,o.bus_kcl_a]}
fn rows(w:&mut impl Write,old:u64,after:u64,a:&temporal::Accepted,q:temporal::Checkpoint){writeln!(w,"STEP,0,{old},{after},{},{:.17e},{},{}",a.half_ticks,a.error_ratio,a.attempts,q.next_full_ticks).unwrap();for ep in &a.endpoints{let o=observations(ep.pair.candidates[1],q.parameters).unwrap();write!(w,"OBS,{},0",ep.elapsed_ticks).unwrap();for v in o.into_iter().chain(motor(ep.observations)){write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();}}
fn alt_rows(w:&mut impl Write,old:u64,after:u64,a:&alt::Accepted,q:alt::Checkpoint){writeln!(w,"STEP,0,{old},{after},{},{:.17e},{},{}",a.half_ticks,a.error_ratio,a.attempts,q.next_full_ticks).unwrap();let mut p=scene();p.decay_ohm=q.parameters.decay_ohm;for ep in &a.endpoints{let o=observations(as_old(ep.pair.candidates[1]),p).unwrap();write!(w,"OBS,{},0",ep.elapsed_ticks).unwrap();for v in o.into_iter().chain(amotor(ep.observations)){write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();}}
fn run()->Result<(),String>{let args:Vec<_>=std::env::args().collect();let raw=fs::read(&args[1]).unwrap();let saved=decode(&raw)?;if saved.q.elapsed_ticks!=START||saved.q.parameters.decay_ohm!=1000.{return Err("own control entry".into());}let dir=std::path::Path::new(&args[2]);fs::create_dir(dir).map_err(|e|e.to_string())?;fs::write(dir.join("entry.ckp"),&raw).unwrap();
 let q=saved.q;let mut p=candidate::Parameters::from_nominal(rf_d_circuit::conditioned_recipe::Recipe{final_decay:rf_d_circuit::conditioned_recipe::FinalDecay::On,resolution:rf_d_circuit::conditioned_recipe::Resolution::Half2Us}.parameters());p.decay_ohm=q.parameters.decay_ohm;p.keyboard=q.parameters.keyboard;p.short=q.parameters.short;p.final_decay=q.parameters.final_decay;
 let aq=alt::Checkpoint{state:candidate::State{high:q.state.high,low:q.state.low},parameters:p,settings:alt::Settings{maximum_half_ticks:q.settings.maximum_half_ticks,attempt_limit:q.settings.attempt_limit},elapsed_ticks:q.elapsed_ticks,next_full_ticks:q.next_full_ticks};let mut a=temporal::Engine::restore(q).map_err(|e|format!("baseline restore:{e:?}"))?;let mut b=alt::Engine::restore(aq).map_err(|e|format!("candidate restore:{e:?}"))?;if raw!=fast_encode(b.checkpoint()){return Err("logical entry".into());}
 let mut w=joint::Workspace::new();let mut aw=candidate::Workspace::new();let bytes=encode(Saved{q:a.checkpoint(),phase:0});if a.advance_to(&mut w,START).is_ok()||b.advance_to(&mut aw,START).is_ok()||bytes!=encode(Saved{q:a.checkpoint(),phase:0})||bytes!=fast_encode(b.checkpoint()){return Err("atomic destination".into());}
 let mut x=std::io::BufWriter::new(fs::File::create(dir.join("baseline.txt")).unwrap());let mut y=std::io::BufWriter::new(fs::File::create(dir.join("candidate.txt")).unwrap());let mut grids=fs::File::create(dir.join("grids.bin")).unwrap();grids.write_all(&bytes).unwrap();
 let(mut base_ns,mut cand_ns,mut count)=(0_u128,0_u128,0_u64);let mut sums:[Sum;9]=std::array::from_fn(|_|Sum::default());let mut asum:[Sum;9]=std::array::from_fn(|_|Sum::default());let started=Instant::now();
 for k in 1..=5{let target=START+k*CUT;while a.checkpoint().elapsed_ticks<target{if started.elapsed().as_secs_f64()>850.{return Err("paired wall guard".into());}let before=a.checkpoint();let t=Instant::now();let aa=a.advance_to(&mut w,target).map_err(|e|format!("baseline:{e:?}"))?;base_ns+=t.elapsed().as_nanos();let t=Instant::now();let bb=b.advance_to(&mut aw,target).map_err(|e|format!("candidate:{e:?}"))?;cand_ns+=t.elapsed().as_nanos();let after=a.checkpoint();let bc=b.checkpoint();
  if aa.half_ticks!=bb.half_ticks||aa.attempts!=bb.attempts||aa.error_ratio.to_bits()!=bb.error_ratio.to_bits()||!pair_equal(&aa.coarse,&bb.coarse)||!aa.endpoints.iter().zip(&bb.endpoints).all(|(a,b)|a.elapsed_ticks==b.elapsed_ticks&&pair_equal(&a.pair,&b.pair)&&motor(a.observations).map(f64::to_bits)==amotor(b.observations).map(f64::to_bits))||encode(Saved{q:after,phase:0})!=fast_encode(bc){return Err(format!("whole accepted bits:{count}"));}
  rows(&mut x,before.elapsed_ticks,after.elapsed_ticks,&aa,after);alt_rows(&mut y,before.elapsed_ticks,after.elapsed_ticks,&bb,bc);let h=f64::from(aa.half_ticks)*temporal::TICK_S;let mut previous=before.state;let mut aprev=candidate::State{high:before.state.high,low:before.state.low};
  for(ep,ap)in aa.endpoints.iter().zip(&bb.endpoints){for(i,weight)in[0.75,0.25].into_iter().enumerate(){let part=joint::parts(q.parameters,previous,ep.pair.increments[i],h).unwrap();let apart=candidate::parts(p,aprev,ap.pair.increments[i],h).unwrap();for(k,row)in[205,195,139,221,223,225,226,227,228].into_iter().enumerate(){sums[k].add(h*weight*part.dc[row]);asum[k].add(h*weight*apart.dc[row]);}}previous=ep.pair.candidates[1];aprev=ap.pair.candidates[1];}
  count+=1;
 }let cp=a.checkpoint();writeln!(x,"GRID,0,{target}").unwrap();write_state(&mut x,cp.state);writeln!(y,"GRID,0,{target}").unwrap();write_state(&mut y,as_old(b.checkpoint().state));grids.write_all(&encode(Saved{q:cp,phase:0})).unwrap();}
 x.flush().unwrap();y.flush().unwrap();grids.flush().unwrap();for k in 0..9{if sums[k].value.to_bits()!=asum[k].value.to_bits()||sums[k].low.to_bits()!=asum[k].low.to_bits(){return Err("oriented integral bits".into());}}
 let values:Vec<u8>=sums.iter().flat_map(|s|s.value.to_le_bytes()).collect();fs::write(dir.join("integrals.bin"),values).unwrap();fs::write(dir.join("final.ckp"),encode(Saved{q:a.checkpoint(),phase:0})).unwrap();fs::write(dir.join("candidate-final.ckp"),fast_encode(b.checkpoint())).unwrap();eprintln!("PAIRED_PASSED,{},count={count},baseline_ns={base_ns},candidate_ns={cand_ns},wall_s={}",q.settings.maximum_half_ticks,started.elapsed().as_secs_f64());Ok(())}
fn main(){if let Err(e)=run(){eprintln!("FAILURE,{e}");std::process::exit(1);}}
'''
 return s

def main():
 for n,s in [(RUST[0],engine()),(RUST[1],paired())]:require(not (ROOT/n).exists(),'exclusive paired source');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);print('PAIRED_PREPARED')
if __name__=='__main__':main()
