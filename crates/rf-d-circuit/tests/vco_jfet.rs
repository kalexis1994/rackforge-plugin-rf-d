use rf_d_circuit::vco_jfet::{self as jfet, Error};
fn bank(text:&str)->Vec<Vec<f64>> {text.lines().map(|l| l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect()}
fn node(r:&[f64],start:usize)->[f64;3] {r[start..start+3].try_into().unwrap()}
fn close(a:f64,e:f64,absolute:f64,relative:f64) {assert!((a-e).abs()<=absolute+relative*e.abs(),"actual={a:.17e},expected={e:.17e}");}
fn conservation(values:&[f64],absolute:f64) {let sum:f64=values.iter().sum();let scale:f64=values.iter().map(|v|v.abs()).sum();assert!(sum.abs()<=absolute+1e-14*scale,"conservation {values:?}");}
#[test]
fn decimal100_and_independent_spice_stamps() {
 let rows=bank(include_str!("../../../evidence/voice_vco_jfet_vectors01.txt"));assert_eq!(rows.len(),2028);let mut max=[0_f64;5];
 for r in rows {
  assert_eq!(r.len(),48);let op=jfet::evaluate(node(&r,0)).unwrap();let step=jfet::companion(node(&r,0),node(&r,3),r[6]).unwrap();
  for i in 0..3 {
   for (a,e) in [(op.current_a[i],r[7+i]),(step.current_a[i],r[10+i])] {close(a,e,1e-14,3e-12);max[0]=max[0].max((a-e).abs());}
   close(op.terminal_charge_c[i],r[13+i],1e-24,3e-12);max[1]=max[1].max((op.terminal_charge_c[i]-r[13+i]).abs());
   for j in 0..3 {
    let k=3*i+j;
    for (a,e) in [(op.jacobian_s[i][j],r[16+k]),(step.jacobian_s[i][j],r[25+k])] {close(a,e,1e-12,3e-12);max[2]=max[2].max((a-e).abs());}
    close(op.charge_jacobian_f[i][j],r[34+k],5e-24,3e-12);max[3]=max[3].max((op.charge_jacobian_f[i][j]-r[34+k]).abs());
   }
  }
  for k in 0..2 {close(step.delta_charge_c[k],r[43+k],1e-30,3e-12);max[4]=max[4].max((step.delta_charge_c[k]-r[43+k]).abs());close(op.junction_charge_c[k],r[45+k],1e-24,3e-12);}
  close(op.channel_current_a,r[47],1e-14,3e-12);
  conservation(&op.current_a,1e-14);conservation(&step.current_a,1e-14);conservation(&op.terminal_charge_c,1e-23);
  for (matrix,absolute) in [(op.jacobian_s,1e-14),(step.jacobian_s,1e-14),(op.charge_jacobian_f,1e-23)] {
   for i in 0..3 {conservation(&matrix[i],absolute);conservation(&std::array::from_fn::<_,3,_>(|j|matrix[j][i]),absolute);}
  }
 }
 let spice=bank(include_str!("../../../evidence/voice_vco_jfet_spice01.txt"));assert_eq!(spice.len(),12);let mut y_max=0_f64;
 for r in spice {
  assert_eq!(r.len(),28);let op=jfet::evaluate(node(&r,0)).unwrap();
  for k in 0..2 {close(op.junction_charge_c[k],r[3+k],1e-20,1e-7);}
  close(op.charge_jacobian_f[2][2],r[5],1e-19,1e-7);close(op.charge_jacobian_f[0][0],r[6],1e-19,1e-7);
  for i in 0..3 {close(op.current_a[i],r[7+i],2e-14,1e-7);
   for j in 0..3 {let k=3*i+j;let real=op.jacobian_s[i][j];let imag=2.*std::f64::consts::PI*1000.*op.charge_jacobian_f[i][j];let error=(real-r[10+k]).hypot(imag-r[19+k]);let expected=r[10+k].hypot(r[19+k]);assert!(error<=2e-12+1e-7*expected);y_max=y_max.max(error);}
  }
 }
 println!("VCO_JFET_ORACLE,rows=2028,spice=12,max_i_a={:.17e},max_q_c={:.17e},max_j_s={:.17e},max_c_f={:.17e},max_delta_c={:.17e},max_spice_y_s={y_max:.17e}",max[0],max[1],max[2],max[3],max[4]);
}
#[test]
fn all_terminal_derivatives_with_fixed_history() {
 let rows=bank(include_str!("../../../evidence/voice_vco_jfet_vectors01.txt"));let delta=1e-6;
 for r in rows {
  let n=node(&r,0);let history=node(&r,3);let original=history;
  let op=jfet::evaluate(n).unwrap();let step=jfet::companion(n,history,r[6]).unwrap();
  for j in 0..3 {
   let mut plus=n;let mut minus=n;plus[j]+=delta;minus[j]-=delta;
   let a=jfet::evaluate(plus).unwrap();let b=jfet::evaluate(minus).unwrap();
   let sa=jfet::companion(plus,history,r[6]).unwrap();let sb=jfet::companion(minus,history,r[6]).unwrap();
   for i in 0..3 {
    close(op.jacobian_s[i][j],(a.current_a[i]-b.current_a[i])/(2.*delta),2e-9,2e-6);
    close(step.jacobian_s[i][j],(sa.current_a[i]-sb.current_a[i])/(2.*delta),2e-9,2e-6);
    close(op.charge_jacobian_f[i][j],(a.terminal_charge_c[i]-b.terminal_charge_c[i])/(2.*delta),1e-21,2e-6);
   }
  }
  assert_eq!(history,original);let repeat=jfet::companion(n,history,r[6]).unwrap();assert_eq!(step.current_a,repeat.current_a);assert_eq!(step.delta_charge_c,repeat.delta_charge_c);
 }
}
#[test]
fn neighbors_terminal_inversion_equal_history_and_rejections() {
 let neighbors=bank(include_str!("../../../evidence/voice_vco_jfet_neighbors01.txt"));assert_eq!(neighbors.len(),20);
 for r in neighbors {
  let step=jfet::companion(node(&r,0),node(&r,3),r[6]).unwrap();
  for k in 0..2 {close(step.delta_charge_c[k],r[7+k],0.,3e-12);if r[7+k]!=0. {assert_ne!(step.delta_charge_c[k],0.);}}
 }
 for r in bank(include_str!("../../../evidence/voice_vco_jfet_vectors01.txt")) {
  let n=node(&r,0);let mirrored=[n[2],n[1],n[0]];let op=jfet::evaluate(n).unwrap();let reverse=jfet::evaluate(mirrored).unwrap();
  close(op.channel_current_a,-reverse.channel_current_a,1e-14,3e-12);
  for (i,j) in [(0,2),(1,1),(2,0)] {close(op.current_a[i],reverse.current_a[j],1e-14,3e-12);}
  let step=jfet::companion(n,n,125e-9).unwrap();assert_eq!(op.current_a,step.current_a);assert_eq!(step.delta_charge_c,[0.;2]);
 }
 // Unequal physical GS/GD capacitors do not follow channel inversion.
 let op=jfet::evaluate([0.;3]).unwrap();close(op.charge_jacobian_f[0][0],5.4990908339470075e-12,1e-24,0.);close(op.charge_jacobian_f[2][2],3.3e-12,1e-24,0.);
 assert_ne!(op.charge_jacobian_f[0][0],op.charge_jacobian_f[2][2]);
 for n in [[2.,0.,1.],[1.,0.,2.]] {let op=jfet::evaluate(n).unwrap();let current=jfet::companion(n,[0.;3],125e-9).unwrap().current_a;let permuted=jfet::companion([n[2],n[1],n[0]],[0.;3],125e-9).unwrap().current_a;
  assert!((current[0]-permuted[2]).abs()>1e-6);assert_eq!(op.terminal_charge_c[0],-op.junction_charge_c[1]);}
 for j in 0..3 {for v in [f64::NAN,f64::INFINITY,40.01,-40.01] {let mut bad=[0.;3];bad[j]=v;assert_eq!(jfet::evaluate(bad).unwrap_err(),Error::InvalidInput);assert!(jfet::companion([0.;3],bad,125e-9).is_err());}}
 for dt in [0.,-1.,124e-9,1.001e-3,f64::NAN,f64::INFINITY] {assert_eq!(jfet::companion([0.;3],[0.;3],dt).unwrap_err(),Error::InvalidInput);}
 for n in [[0.,0.,-0.91],[0.,-0.01,40.]] {assert_eq!(jfet::evaluate(n).unwrap_err(),Error::JunctionDomain);}
 assert_eq!(jfet::evaluate([40.,0.,-0.5]).unwrap_err(),Error::ChannelDomain);
}
