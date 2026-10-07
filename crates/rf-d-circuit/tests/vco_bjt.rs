use rf_d_circuit::vco_bjt::{self as bjt, Error, Polarity};
fn polarity(v:f64)->Polarity { if v==1. {Polarity::Npn} else {assert_eq!(v,-1.);Polarity::Pnp} }
fn bank(text:&str)->Vec<Vec<f64>> {text.lines().map(|l| l.split_whitespace().map(|v|v.parse().unwrap()).collect()).collect()}
fn node(r:&[f64],start:usize)->[f64;4] {r[start..start+4].try_into().unwrap()}
fn close(a:f64,e:f64,absolute:f64,relative:f64) {assert!((a-e).abs()<=absolute+relative*e.abs(),"actual={a:.17e},expected={e:.17e}");}
fn conservation(values:&[f64],absolute:f64) {let sum:f64=values.iter().sum();let scale:f64=values.iter().map(|v|v.abs()).sum();assert!(sum.abs()<=absolute+1e-14*scale,"conservation {values:?}");}
#[test]
fn decimal100_and_independent_spice_stamps() {
 let rows=bank(include_str!("../../../evidence/voice_vco_bjt_vectors01.txt"));assert_eq!(rows.len(),1536);let mut max=[0_f64;5];
 for r in rows {
  assert_eq!(r.len(),74);let p=polarity(r[0]);let op=bjt::evaluate(p,node(&r,1)).unwrap();let step=bjt::companion(p,node(&r,1),node(&r,5),r[9]).unwrap();
  for i in 0..4 {
   for (a,e) in [(op.current_a[i],r[10+i]),(step.current_a[i],r[14+i])] {close(a,e,1e-14,3e-12);max[0]=max[0].max((a-e).abs());}
   close(op.terminal_charge_c[i],r[18+i],1e-23,3e-12);max[1]=max[1].max((op.terminal_charge_c[i]-r[18+i]).abs());
   for j in 0..4 {
    let k=4*i+j;
    for (a,e) in [(op.jacobian_s[i][j],r[22+k]),(step.jacobian_s[i][j],r[38+k])] {close(a,e,1e-12,3e-12);max[2]=max[2].max((a-e).abs());}
    close(op.charge_jacobian_f[i][j],r[54+k],1e-23,3e-12);max[3]=max[3].max((op.charge_jacobian_f[i][j]-r[54+k]).abs());
   }
  }
  for k in 0..2 {close(step.delta_charge_c[k],r[70+k],1e-30,3e-12);max[4]=max[4].max((step.delta_charge_c[k]-r[70+k]).abs());close(op.oriented_junction_charge_c[k],r[72+k],1e-23,3e-12);}
  conservation(&op.current_a,1e-14);conservation(&step.current_a,1e-14);conservation(&op.terminal_charge_c,1e-23);
  for matrix in [op.jacobian_s,step.jacobian_s,op.charge_jacobian_f] {
   let absolute=if matrix==op.charge_jacobian_f {1e-23} else {1e-14};
   for i in 0..4 {conservation(&matrix[i],absolute);conservation(&std::array::from_fn::<_,4,_>(|j|matrix[j][i]),absolute);}
  }
 }
 let spice=bank(include_str!("../../../evidence/voice_vco_bjt_spice02.txt"));assert_eq!(spice.len(),12);let mut y_max=0_f64;
 for r in spice {
  assert_eq!(r.len(),45);let op=bjt::evaluate(polarity(r[0]),node(&r,1)).unwrap();
  for k in 0..2 {close(op.oriented_junction_charge_c[k],r[5+k],1e-20,1e-7);}
  close(op.charge_jacobian_f[2][2],r[7],1e-19,1e-7);close(op.charge_jacobian_f[0][0],r[8],1e-19,1e-7);
  for i in 0..4 {close(op.current_a[i],r[9+i],2e-14,1e-7);
   for j in 0..4 {let k=4*i+j;let real=op.jacobian_s[i][j];let imag=2.*std::f64::consts::PI*1000.*op.charge_jacobian_f[i][j];let error=(real-r[13+k]).hypot(imag-r[29+k]);let expected=r[13+k].hypot(r[29+k]);assert!(error<=2e-12+1e-7*expected);y_max=y_max.max(error);}
  }
 }
 println!("VCO_BJT_ORACLE,rows=1536,spice=12,max_i_a={:.17e},max_q_c={:.17e},max_j_s={:.17e},max_c_f={:.17e},max_delta_c={:.17e},max_spice_y_s={y_max:.17e}",max[0],max[1],max[2],max[3],max[4]);
}
#[test]
fn all_terminal_derivatives_with_fixed_history() {
 let rows=bank(include_str!("../../../evidence/voice_vco_bjt_vectors01.txt"));let delta=1e-6;
 for r in rows {
  let p=polarity(r[0]);let n=node(&r,1);let history=node(&r,5);let original=history;
  let op=bjt::evaluate(p,n).unwrap();let step=bjt::companion(p,n,history,r[9]).unwrap();
  for j in 0..4 {
   let mut plus=n;let mut minus=n;plus[j]+=delta;minus[j]-=delta;
   let a=bjt::evaluate(p,plus).unwrap();let b=bjt::evaluate(p,minus).unwrap();
   let sa=bjt::companion(p,plus,history,r[9]).unwrap();let sb=bjt::companion(p,minus,history,r[9]).unwrap();
   for i in 0..4 {
    close(op.jacobian_s[i][j],(a.current_a[i]-b.current_a[i])/(2.*delta),2e-9,2e-6);
    close(step.jacobian_s[i][j],(sa.current_a[i]-sb.current_a[i])/(2.*delta),2e-9,2e-6);
    close(op.charge_jacobian_f[i][j],(a.terminal_charge_c[i]-b.terminal_charge_c[i])/(2.*delta),1e-21,2e-6);
   }
  }
  assert_eq!(history,original);let repeat=bjt::companion(p,n,history,r[9]).unwrap();assert_eq!(step.current_a,repeat.current_a);assert_eq!(step.delta_charge_c,repeat.delta_charge_c);
 }
}
#[test]
fn neighbors_substrate_equal_history_and_rejections() {
 let neighbors=bank(include_str!("../../../evidence/voice_vco_bjt_neighbors01.txt"));assert_eq!(neighbors.len(),20);
 for r in neighbors {
  let step=bjt::companion(polarity(r[0]),node(&r,1),node(&r,5),r[9]).unwrap();
  for k in 0..2 {close(step.delta_charge_c[k],r[10+k],0.,3e-12);if r[10+k]!=0. {assert_ne!(step.delta_charge_c[k],0.);}}
 }
 for p in [Polarity::Npn,Polarity::Pnp] {
  let n=[0.;4];let op=bjt::evaluate(p,n).unwrap();let step=bjt::companion(p,n,n,125e-9).unwrap();assert_eq!(op.current_a,step.current_a);assert_eq!(step.delta_charge_c,[0.;2]);
  let n=[0.,0.,0.,0.25];let op=bjt::evaluate(p,n).unwrap();let target=if p==Polarity::Npn {0} else {1};
  assert_eq!(op.current_a[target],-2.5e-13);assert_eq!(op.current_a[3],2.5e-13);assert_eq!(op.terminal_charge_c[3],0.);
  for j in 0..4 {for v in [f64::NAN,f64::INFINITY,40.01,-40.01] {let mut bad=[0.;4];bad[j]=v;assert_eq!(bjt::evaluate(p,bad).unwrap_err(),Error::InvalidInput);assert!(bjt::companion(p,[0.;4],bad,125e-9).is_err());}}
  for dt in [0.,-1.,124e-9,1.001e-3,f64::NAN,f64::INFINITY] {assert_eq!(bjt::companion(p,[0.;4],[0.;4],dt).unwrap_err(),Error::InvalidInput);}
 }
 for n in [[0.,0.,-0.91,0.],[0.,-0.01,40.,0.]] {assert_eq!(bjt::evaluate(Polarity::Npn,n).unwrap_err(),Error::JunctionDomain);}
}
