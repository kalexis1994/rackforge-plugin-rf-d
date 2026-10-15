pub use rf_d_circuit::{junction_charge,StepError};
#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"] mod circuit;
#[path="../crates/rf-d-circuit/src/hybrid_schur_solver.rs"] mod solver;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use circuit::*;
use circuit::solver as direct;
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer};
use std::io::{self,BufRead};
fn scene()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn refined_reference(j:[[f64;M];M],b:[f64;M])->[f64;M]{
    let mut d=rf_d_circuit::block_decay_voice::solve_linear_extent(j,b).unwrap();
    for _ in 0..3{
        let mut r=[0.;M];for i in 0..M{let mut high=-b[i];let mut low=0.;for k in 0..M{let p=j[i][k]*d[k];let s=high+p;low+=if high.abs()>=p.abs(){(high-s)+p}else{(p-s)+high};low+=j[i][k].mul_add(d[k],-p);high=s;}r[i]=-(high+low);}
        let e=rf_d_circuit::block_decay_voice::solve_linear_extent(j,r).unwrap();for k in 0..M{d[k]+=e[k];}
    }
    let mut backward=0_f64;for i in 0..M{let mut high=-b[i];let mut low=0.;let mut scale=b[i].abs();for k in 0..M{let p=j[i][k]*d[k];let s=high+p;low+=if high.abs()>=p.abs(){(high-s)+p}else{(p-s)+high};low+=j[i][k].mul_add(d[k],-p);high=s;scale+=j[i][k].abs()*(d[k].abs()+2e-9);}backward=backward.max((high+low).abs()/scale.max(1e-300));}
    assert!(backward<=1e-11);d
}
fn views(s:&[Parts;2])->[direct::Stage<'_>;2]{[direct::Stage{dc:&s[0].j,mass:&s[0].mass},direct::Stage{dc:&s[1].j,mass:&s[1].mass}]}
fn retry(w:&mut direct::Workspace,s:&[Parts;2],rhs:[f64;M],expected:[f64;M]){let d=w.solve(views(s),B,rhs).unwrap();for k in 0..M{assert_eq!(d[k].to_bits(),expected[k].to_bits());}}
fn bad(w:&mut direct::Workspace,s:&[Parts;2],rhs:[f64;M],expected:[f64;M],dc:[[f64;N];N],mass:[[f64;N];N],stage:usize,guards:&mut usize){
 let mut a=views(s);a[stage]=direct::Stage{dc:&dc,mass:&mass};assert!(w.solve(a,B,rhs).is_err());retry(w,s,rhs,expected);*guards+=1;
}
fn main(){
 let mut w=direct::Workspace::new();let mut control=solver::Workspace::new();let mut cases=0;let mut fraction=0_f64;let mut entries=0;let mut guards=0;let mut changed=0;
 for line in io::stdin().lock().lines(){
  let v:Vec<f64>=line.unwrap().split(',').map(|s|s.parse().unwrap()).collect();assert_eq!(v.len(),3+5*M+2);
  let t=v[0];let h=v[1];let c=Controls{key:v[2],short:false,optional:false};let mut p=scene();p.time=t;
  let state=|index:usize|State{high:std::array::from_fn(|k|v[3+index*M+k]),low:std::array::from_fn(|k|v[3+index*M+N+k]),optional:false};
  let old=state(0);let s=[parts::<true>(p,old,state(1),c,h,t+h/3.).unwrap(),parts::<true>(p,old,state(2),c,h,t+h).unwrap()];
  let r:[f64;M]=std::array::from_fn(|k|s[k/N].dc[k%N]+B[k/N][0]*s[0].dq[k%N]+B[k/N][1]*s[1].dq[k%N]);
  let j:[[f64;M];M]=std::array::from_fn(|k|std::array::from_fn(|l|B[k/N][l/N]*s[l/N].mass[k%N][l%N]+if k/N==l/N{s[k/N].j[k%N][l%N]}else{0.}));
  let retained=w.coefficients(views(&s),B).unwrap();
  for i in 0..M{for k in 0..M{assert_eq!(j[i][k].to_bits(),retained[i][k].to_bits());entries+=1;}}
  let mut rhses=[[0.;M];8];rhses[0]=r.map(|v|-v);
  for (i,k) in [54,55,116,172,173,234].into_iter().enumerate(){rhses[i+1][k]=1.;}
  rhses[7]=std::array::from_fn(|k|(((k*17+11)%31) as f64-15.)/31.);
  for rhs in rhses{
   let d=w.solve(views(&s),B,rhs).unwrap();let previous=control.solve(&j,rhs).unwrap();for k in 0..M{assert_eq!(d[k].to_bits(),previous[k].to_bits());}
   let full=refined_reference(j,rhs);let worst=(0..M).fold(0_f64,|m,k|m.max((d[k]-full[k]).abs()/(2e-9+1e-7*full[k].abs())));assert!(worst<=1.,"direction {worst}");fraction=fraction.max(worst);cases+=1;
  }
  let rhs=rhses[0];let expected=w.solve(views(&s),B,rhs).unwrap();
  // Add an unseen legal edge, then remove it in the next initialization.
  let column=(0..54).find(|k|s[0].j[0][*k]==0.).unwrap();let mut dc=s[0].j;dc[0][column]=1e-20;
  let mut input=views(&s);input[0]=direct::Stage{dc:&dc,mass:&s[0].mass};let got=w.coefficients(input,B).unwrap();
  assert_eq!(got[0][column],j[0][column]+1e-20);retry(&mut w,&s,rhs,expected);changed+=1;
  if cases==8{
   for stage in 0..2{
    for value in [f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{
     let mut dc=s[stage].j;dc[117][117]=value;bad(&mut w,&s,rhs,expected,dc,s[stage].mass,stage,&mut guards);
     let mut mass=s[stage].mass;mass[0][56]=value;bad(&mut w,&s,rhs,expected,s[stage].j,mass,stage,&mut guards);
    }
    for (row,col) in [(0,56),(56,0)]{
     let mut dc=s[stage].j;dc[row][col]=1e-20;bad(&mut w,&s,rhs,expected,dc,s[stage].mass,stage,&mut guards);
     let mut mass=s[stage].mass;mass[row][col]=1e-20;bad(&mut w,&s,rhs,expected,s[stage].j,mass,stage,&mut guards);
    }
   }
   for value in [f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{let mut invalid=rhs;invalid[235]=value;assert!(w.solve(views(&s),B,invalid).is_err());retry(&mut w,&s,rhs,expected);guards+=1;}
   for i in 0..2{for jj in 0..2{for value in [f64::NAN,f64::INFINITY]{let mut weights=B;weights[i][jj]=value;assert!(w.solve(views(&s),weights,rhs).is_err());retry(&mut w,&s,rhs,expected);guards+=1;}}}
   let mut cancel_dc=s[0].j;let mut cancel_mass=s[0].mass;cancel_mass[0][column]=2e-20;cancel_dc[0][column]=-B[0][0]*cancel_mass[0][column];
   let mut input=views(&s);input[0]=direct::Stage{dc:&cancel_dc,mass:&cancel_mass};let retained=w.coefficients(input,B).unwrap();
   assert_eq!(retained[0][column],0.);assert_eq!(retained[N][column],B[1][0]*cancel_mass[0][column]);retry(&mut w,&s,rhs,expected);
   let zero=[[0.;N];N];let z=[direct::Stage{dc:&zero,mass:&zero};2];assert!(matches!(w.solve(z,B,rhs),Err(StepError::SingularJacobian)));retry(&mut w,&s,rhs,expected);guards+=1;
   let mut dense=zero;for i in 0..54{for k in 0..54{dense[i][k]=1e-8;}}let mut input=views(&s);input[0]=direct::Stage{dc:&s[0].j,mass:&dense};
   assert!(matches!(w.solve(input,B,rhs),Err(StepError::InvalidInput)));retry(&mut w,&s,rhs,expected);guards+=1;
  }
 }
 let s=w.statistics;assert_eq!(cases,192);assert_eq!(entries,24*M*M);assert_eq!(guards,33);assert_eq!(changed,24);
 println!("DIRECT,{cases},{fraction:.17e},{entries},{guards},{changed},{},{},{:.17e},{:.17e},{},{}",s.solves,s.refinements,s.max_initial_backward,s.max_final_backward,s.max_nonzeros,1);
}
