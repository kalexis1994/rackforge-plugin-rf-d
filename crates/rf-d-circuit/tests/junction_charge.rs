use rf_d_circuit::junction_charge::{Parameters,Error};
fn parameters(row:&[f64])->Parameters {Parameters{zero_bias_capacitance_f:row[1],potential_v:row[2],grading:row[3],forward_fraction:row[4]}}
fn rows()->Vec<Vec<f64>> {include_str!("../../../evidence/voice_junction_charge_vectors01.txt").lines().map(|line|line.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect()}
fn close(actual:f64,expected:f64,absolute:f64,relative:f64) {assert!((actual-expected).abs()<=absolute+relative*expected.abs(),"actual={actual:.17e}, expected={expected:.17e}");}
#[test]
fn decimal100_charge_and_fixed_history_companions() {
 let bank=rows();assert_eq!(bank.len(),1280);let mut maxima=[0_f64;5];
 for r in &bank {
  assert_eq!(r.len(),14);let p=parameters(r);let q0=p.charge(r[5]).unwrap();let q=p.charge(r[6]).unwrap();let a=p.companion(r[6],r[5],r[7]).unwrap();
  close(q0.charge_c,r[8],1e-24,1e-12);close(q.charge_c,r[9],1e-24,1e-12);
  for (i,(x,y,abs)) in [(q.charge_c,r[9],1e-24),(q.capacitance_f,r[10],5e-24),(a.delta_charge_c,r[11],1e-30),(a.current_a,r[12],1e-22),(a.conductance_s,r[13],5e-20)].into_iter().enumerate() {close(x,y,abs,1e-12);maxima[i]=maxima[i].max((x-y).abs());}
  assert_eq!(a.next_charge_c,q.charge_c);assert_eq!(a.capacitance_f,q.capacitance_f);
  let again=p.companion(r[6],r[5],r[7]).unwrap();assert_eq!(a.current_a,again.current_a);
  if r[5]!=r[6] && (r[5]-r[6]).abs()<1e-12 && r[11]!=0. {close(a.delta_charge_c,r[11],0.,2e-12);assert_ne!(a.delta_charge_c,0.);}
 }
 println!("JUNCTION_ORACLE,rows=1280,max_q_c={:.17e},max_c_f={:.17e},max_delta_c={:.17e},max_i_a={:.17e},max_g_s={:.17e}",maxima[0],maxima[1],maxima[2],maxima[3],maxima[4]);
}
#[test]
fn derivatives_splice_and_reverse_increments() {
 for r in rows() {
  let p=parameters(&r);let v=r[6];let old=r[5];let dt=r[7];let delta=1e-6;
  if v-delta>=-40. && v+delta<=40. {
   let fd=(p.charge(v+delta).unwrap().charge_c-p.charge(v-delta).unwrap().charge_c)/(2.*delta);
   close(p.charge(v).unwrap().capacitance_f,fd,1e-21,1e-5);
   let fd_i=(p.companion(v+delta,old,dt).unwrap().current_a-p.companion(v-delta,old,dt).unwrap().current_a)/(2.*delta);
   close(p.companion(v,old,dt).unwrap().conductance_s,fd_i,1e-21/dt,1e-5);
  }
  assert_eq!(p.charge_increment(old,v).unwrap(),-p.charge_increment(v,old).unwrap());
  let vf=p.potential_v*p.forward_fraction;
  let q=p.charge(vf).unwrap();let left=p.charge(vf-1e-10).unwrap();let right=p.charge(vf+1e-10).unwrap();
  close(left.charge_c,q.charge_c,1e-19,0.);close(right.charge_c,q.charge_c,1e-19,0.);
  close(left.capacitance_f,q.capacitance_f,1e-19,0.);close(right.capacitance_f,q.capacitance_f,1e-19,0.);
 }
}
#[test]
fn zero_equal_history_and_rejections() {
 let p=Parameters{zero_bias_capacitance_f:7e-12,potential_v:0.75,grading:0.5,forward_fraction:0.4};
 for v in [-40.,0.,0.3,40.] {let a=p.companion(v,v,125e-9).unwrap();assert_eq!(a.current_a,0.);assert_eq!(a.delta_charge_c,0.);}
 let zero=Parameters{zero_bias_capacitance_f:0.,..p};let a=zero.companion(40.,-40.,125e-9).unwrap();assert_eq!(a.next_charge_c,0.);assert_eq!(a.conductance_s,0.);assert_eq!(a.current_a,0.);
 for v in [f64::NAN,f64::INFINITY,-40.01,40.01] {assert_eq!(p.charge(v).unwrap_err(),Error::InvalidInput);assert_eq!(p.companion(0.,v,1.).unwrap_err(),Error::InvalidInput);}
 for dt in [0.,-1.,f64::NAN,f64::INFINITY] {assert_eq!(p.companion(0.,0.,dt).unwrap_err(),Error::InvalidInput);}
 for bad in [Parameters{zero_bias_capacitance_f:-1.,..p},Parameters{zero_bias_capacitance_f:f64::INFINITY,..p},Parameters{potential_v:0.,..p},Parameters{potential_v:f64::NAN,..p},Parameters{grading:1.,..p},Parameters{grading:-0.1,..p},Parameters{forward_fraction:-0.1,..p},Parameters{forward_fraction:0.96,..p}] {assert_eq!(bad.charge(0.).unwrap_err(),Error::InvalidInput);}
 assert_eq!(p.companion(40.,-40.,f64::from_bits(1)).unwrap_err(),Error::NonFiniteResult);
 let overflow=Parameters{zero_bias_capacitance_f:f64::MAX,..p};assert_eq!(overflow.charge(40.).unwrap_err(),Error::NonFiniteResult);
}
