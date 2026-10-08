use rf_d_circuit::{vco1_increment::{self,State},vco1_newton::Budget,vco1_stamp::{Controls,N,NV}};
fn main() {
 let a:Vec<f64>=include_str!("../evidence/voice_vco1_increment_floor_history01.txt").split_whitespace().map(|x|x.parse().unwrap()).collect();let old=State{high:a[..N].try_into().unwrap(),low:a[N..].try_into().unwrap()};let c=Controls::default();let tick=vco1_increment::MIN_DT_S;
 let full=vco1_increment::solve(c,old,2.*tick,Budget::default()).unwrap();let mid=vco1_increment::solve(c,old,tick,Budget::default()).unwrap();let end=vco1_increment::solve(c,mid.candidate,tick,Budget::default()).unwrap();
 for (name,s) in [("full",&full),("mid",&mid),("end",&end)] {print!("ROOT,{name},{:.17e},{:.17e},{},{}",s.residual_ratio,s.correction_ratio,s.iterations,s.trials);for v in s.candidate.high.into_iter().chain(s.candidate.low) {print!(",{v:.17e}");}println!();}
 let d=full.candidate.difference(end.candidate);let k=(0..N).max_by(|a,b|(d[*a].abs()/if *a<NV {2e-6} else {2e-9}).total_cmp(&(d[*b].abs()/if *b<NV {2e-6} else {2e-9}))).unwrap();println!("LIMIT,index={k},error_ratio={:.17e},difference={:.17e}",d[k].abs()/if k<NV {2e-6} else {2e-9},d[k]);
}
