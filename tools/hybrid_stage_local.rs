pub use rf_d_circuit::{junction_charge,StepError};
#[path="../crates/rf-d-circuit/src/stage_hybrid_voice.rs"] mod circuit;
#[path="../crates/rf-d-circuit/src/hybrid_schur_solver.rs"] mod solver;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use circuit::*;
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
fn main(){
    let mut w=solver::Workspace::new();let mut cases=0;let mut fraction=0_f64;
    for line in io::stdin().lock().lines(){
        let v:Vec<f64>=line.unwrap().split(',').map(|s|s.parse().unwrap()).collect();assert_eq!(v.len(),3+5*M+2);
        let t=v[0];let h=v[1];let c=Controls{key:v[2],short:false,optional:false};let mut p=scene();p.time=t;
        let state=|index:usize|State{high:std::array::from_fn(|k|v[3+index*M+k]),low:std::array::from_fn(|k|v[3+index*M+N+k]),optional:false};
        let old=state(0);let a=parts::<true>(p,old,state(1),c,h,t+h/3.).unwrap();let b=parts::<true>(p,old,state(2),c,h,t+h).unwrap();
        let s=[a,b];let r:[f64;M]=std::array::from_fn(|k|s[k/N].dc[k%N]+B[k/N][0]*s[0].dq[k%N]+B[k/N][1]*s[1].dq[k%N]);
        let j:[[f64;M];M]=std::array::from_fn(|k|std::array::from_fn(|l|B[k/N][l/N]*s[l/N].mass[k%N][l%N]+if k/N==l/N{s[k/N].j[k%N][l%N]}else{0.}));
        let mut contiguous=[[0.;M];M];
        for i in 0..2{for jj in 0..2{let stage=&s[jj];let weight=B[i][jj];
            for a in 0..N{let row=&mut contiguous[i*N+a];let mass=&stage.mass[a];let dc=&stage.j[a];
                for b in 0..N{row[jj*N+b]=weight*mass[b]+if i==jj{dc[b]}else{0.};}
            }
        }}
        for i in 0..M{for k in 0..M{assert_eq!(j[i][k].to_bits(),contiguous[i][k].to_bits());}}
        let valid=w.solve(&j,r.map(|v|-v)).unwrap();
        let mut corrupt=j;corrupt[54][54]=f64::NAN;
        assert!(w.solve(&corrupt,r.map(|v|-v)).is_err());
        assert_eq!(w.solve(&j,r.map(|v|-v)).unwrap(),valid);
        let mut rhses=[[0.;M];8];rhses[0]=r.map(|v|-v);
        for (i,k) in [54,55,116,172,173,234].into_iter().enumerate(){rhses[i+1][k]=1.;}
        rhses[7]=std::array::from_fn(|k|(((k*17+11)%31) as f64-15.)/31.);
        for rhs in rhses{
            let d=w.solve(&j,rhs).unwrap();let full=refined_reference(j,rhs);
            let worst=(0..M).fold(0_f64,|m,k|m.max((d[k]-full[k]).abs()/(2e-9+1e-7*full[k].abs())));assert!(worst<=1.,"direction {worst}");fraction=fraction.max(worst);cases+=1;
        }
        if cases==8{
            let rhs=rhses[0];let expected=w.solve(&j,rhs).unwrap();
            for (i,k) in [(0,56),(56,0)]{let mut bad=j;bad[i][k]=1e-20;assert!(w.solve(&bad,rhs).is_err());assert_eq!(w.solve(&j,rhs).unwrap(),expected);}
            let mut bad=rhs;bad[0]=f64::NAN;assert!(w.solve(&j,bad).is_err());assert_eq!(w.solve(&j,rhs).unwrap(),expected);
        }
    }
    let s=w.statistics;assert_eq!(cases,192);println!("LOCAL,{cases},{fraction:.17e},{},{},{:.17e},{:.17e},{},3",s.solves,s.refinements,s.max_initial_backward,s.max_final_backward,s.max_nonzeros);
}
