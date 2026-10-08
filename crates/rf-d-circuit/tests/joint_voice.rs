use rf_d_circuit::{joint_voice as joint,chain_charge::{self,Parameters as Chain},mixer_on::OnMixer,vco1_engine::State as VcoState,vco1_radau,vco1_startup,vco1_stamp::Controls};
#[allow(dead_code)] #[path="support/mixer_chain_lab.rs"] mod lab;
fn scene(mask:bool)->(joint::Parameters,joint::State,VcoState,chain_charge::State) {
 let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.;
 let p=Chain {circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([true;5],[0.5;4]).unwrap()};
 let controls=Controls::default();let v=VcoState::from_nodes(vco1_startup::startup(controls).unwrap().nodes);
 let row:Vec<f64>=include_str!("../../../evidence/voice_chain_charge_vectors06.txt").lines().next().unwrap().split_whitespace().map(|x|x.parse().unwrap()).collect();
 let c=chain_charge::State::from_nodes(row[8..76].try_into().unwrap());
 let p=joint::Parameters::new(controls,p,[mask;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap();
 (p,joint::State::lift(v.high,v.low,c),v,c)
}
fn near(a:f64,b:f64,t:f64) {assert!(a.is_finite()&&b.is_finite()&&(a-b).abs()<=t,"{a:e} != {b:e}, gate {t:e}");}
#[test]
fn interface_kcl_and_all_matrix_entries_preserve_single_ownership() {
 let mut entries=0;
 for mask in [false,true] {let(p,old,mut v,mut c)=scene(mask);v.high[108]=0.;v.low[108]=0.;c.high[66]=v.high[12];c.low[66]=v.low[12];
  for h in [125e-9,joint::MIN_DT_S] {
   let dv=[[0.;134];2];let dc=[[0.;68];2];let j=joint::linearize(p,old,[joint::State::from_nodes([0.;joint::N]);2],h).unwrap();
   let vr=vco1_radau::linearize(p.controls,v,dv,h).unwrap();let cr=rf_d_circuit::chain_radau::linearize(p.chain(),p.sources,c,dc,h).unwrap();
   let mut r=[0.;joint::M];let mut matrix=[[0.;joint::M];joint::M];
   for stage in 0..2 {for a in 0..134 {if let Some(i)=joint::vco_index(a) {
    r[stage*joint::N+i]+=vr.residual[stage*134+a];
    for t in 0..2 {for b in 0..134 {if let Some(k)=joint::vco_index(b) {matrix[stage*joint::N+i][t*joint::N+k]+=vr.jacobian[stage*134+a][t*134+b];}}}
   }}for a in 0..68 {let i=joint::chain_index(a);r[stage*joint::N+i]+=cr.residual[stage*68+a];
    for t in 0..2 {for b in 0..68 {matrix[stage*joint::N+i][t*joint::N+joint::chain_index(b)]+=cr.jacobian[stage*68+a][t*68+b];}}
   }}
   for a in 0..joint::M {near(j.residual[a],r[a],1e-12+1e-12*r[a].abs());for b in 0..joint::M {near(j.jacobian[a][b],matrix[a][b],1e-12+1e-12*matrix[a][b].abs());entries+=1;}}
   let y=p.chain().mixer.admittance_s();assert!(y[0].iter().all(|v|*v==0.));
   // Direct resistor law, independent of block assembly and VMIXER current.
   let bus=old.high[12];let cursor=old.high[39];let reduced=p.chain().mixer.evaluate([p.sources[0],p.sources[1],p.sources[2],p.sources[3],p.sources[4],bus]).unwrap().current_a[5];
   for stage in 0..2 {near(j.residual[stage*joint::N+12],(bus-cursor)/33000.+reduced,1e-12);}
   // R45 cross-coupling and C27 incidence exist in both stage directions.
   for stage in 0..2 {near(j.jacobian[stage*joint::N+12][stage*joint::N+39],-1./33000.,1e-18);
    for t in 0..2 {near(j.jacobian[stage*joint::N+12][t*joint::N+joint::chain_index(6)],-joint::B[stage][t]*10e-6/h,1e-10);}}
  }
 }
 println!("JOINT_TOPOLOGY,scenes=4,matrix_entries={entries},unknowns=200,stage_rows=400");
}
#[test]
fn coupled_steps_interface_derivatives_and_atomic_rejection() {
 let mut columns=0;let mut pairs=0;let mut worst=0_f64;
 for mask in [false,true] {let(p,old,_,_)=scene(mask);
  for h in [125e-9,joint::MIN_DT_S] {
   let pair=joint::step(p,old,h).unwrap();assert!(pair.residual_ratio<=1.&&pair.correction_ratio<=1.);pairs+=1;
   let stamp=joint::linearize(p,old,pair.increments,h).unwrap();
   // Export exact high/low histories and increments for an independent oracle.
   println!("JOINT_ROOT,{},{h:e},{:e},{:e}",usize::from(mask),pair.residual_ratio,pair.correction_ratio);
   for s in [old,pair.increments[0],pair.increments[1],pair.candidates[0],pair.candidates[1]] {println!("JOINT_STATE,{}",s.high.into_iter().chain(s.low).map(|v|format!("{v:.17e}")).collect::<Vec<_>>().join(","));}
   for t in 0..2 {for k in [12,39,46,joint::chain_index(6),joint::chain_index(67)] {
    let mut a=pair.increments;let mut b=a;let mut perturb=[0.;joint::N];perturb[k]=1e-7;a[t]=a[t].advanced(perturb);perturb[k]=-1e-7;b[t]=b[t].advanced(perturb);
    let sa=joint::linearize(p,old,a,h).unwrap();let sb=joint::linearize(p,old,b,h).unwrap();
    for row in 0..joint::M {let fd=(sa.residual[row]-sb.residual[row])/2e-7;let tol=1e-8+2e-5*fd.abs();let ratio=(stamp.jacobian[row][t*joint::N+k]-fd).abs()/tol;worst=worst.max(ratio);near(stamp.jacobian[row][t*joint::N+k],fd,tol);}columns+=1;
   }}
   let before=old;assert!(joint::step(p,old,h*0.).is_err());assert_eq!(old,before);
   let cursor=pair.candidates[1].high[39];let bus=pair.candidates[1].high[12];let saw=pair.candidates[1].high[46];
   near((cursor-saw)/12500.+cursor/12500.+(cursor-bus)/33000.,0.,1e-12);
  }
 }
 println!("JOINT_STEPS,pairs={pairs},stages={},fd_columns={columns},fd_entries={},max_fd_gate={worst:e},reject_preserved=4",2*pairs,columns*joint::M);
}
