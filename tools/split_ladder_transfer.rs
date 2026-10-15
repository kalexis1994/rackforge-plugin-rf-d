pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/split_ladder_voice.rs"]mod circuit;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use circuit::*;
use std::io::{self,BufRead};
fn copy_parts(p:&Parts)->Parts{Parts{dc:p.dc,j:p.j,dq:p.dq,mass:p.mass,now:p.now}}
fn copy_local(s:&ladder::Solution)->ladder::Solution{ladder::Solution{dc:s.dc,physical_j:s.physical_j,z:s.z,nodes:s.nodes,reaction:s.reaction,reaction_j:s.reaction_j,source:s.source,source_j:s.source_j,dz_dy:s.dz_dy,iterations:s.iterations,residual_a:s.residual_a,correction_v:s.correction_v}}
fn same(a:&Parts,b:&Parts){
    for(a,b)in a.dc.iter().chain(a.j.iter().flatten()).chain(a.dq.iter()).chain(a.mass.iter().flatten()).chain(a.now.high.iter()).chain(a.now.low.iter())
        .zip(b.dc.iter().chain(b.j.iter().flatten()).chain(b.dq.iter()).chain(b.mass.iter().flatten()).chain(b.now.high.iter()).chain(b.now.low.iter())){assert_eq!(a.to_bits(),b.to_bits());}
    assert_eq!(a.now.optional,b.now.optional);
}
fn main(){
    let line=io::stdin().lock().lines().next().unwrap().unwrap();let row:Vec<f64>=line.split(',').map(|v|v.parse().unwrap()).collect();assert_eq!(row.len(),1185);
    let t=row[0];let h=row[1];let c=Controls{key:row[2],short:false,optional:false};
    let state=|b:usize|State{high:std::array::from_fn(|k|row[3+b*M+k]),low:std::array::from_fn(|k|row[3+b*M+N+k]),optional:false};
    let(card,b,hp)=lab::lab_parameters();let recipe=rf_d_circuit::chain_charge::Parameters{circuit:card,conversion:b,headphone:hp,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()};
    let mut p=Parameters::new(recipe).unwrap();p.time=t;let old=state(0);let stage=evaluate::<true>(p,old,increment(state(3),old),c,h,t+h/3.).unwrap();
    let parent=binding::parent_parts::<true>(circuit::parent::Parameters::new(recipe).unwrap(),t,old,stage.delta,c,h,t+h/3.).unwrap();
    let mut expected=copy_parts(&parent);binding::merge::<true>(&mut expected,&stage.local).unwrap();same(&expected,&stage.physical);
    let retry=||{let mut x=copy_parts(&parent);binding::merge::<true>(&mut x,&stage.local).unwrap();same(&x,&expected);};
    let mut failures=0;let mut atomic=0;
    for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{
        for field in 0..4{
            let mut local=copy_local(&stage.local);match field{0=>local.dc[5]=value,1=>local.physical_j[5][5]=value,2=>local.nodes.high[5]=value,_=>local.nodes.low[5]=value};
            for full in[false,true]{let mut x=copy_parts(&parent);let saved=copy_parts(&x);let err=if full{binding::merge::<true>(&mut x,&local)}else{binding::merge::<false>(&mut x,&local)};assert!(err.is_err());same(&x,&saved);retry();failures+=1;atomic+=1;}
        }
        let mut x=copy_parts(&parent);x.j[0][0]=value;let saved=copy_parts(&x);assert!(binding::merge::<true>(&mut x,&stage.local).is_err());same(&x,&saved);retry();failures+=1;atomic+=1;
    }
    // Finite transfer data whose sums overflow. Neither DC nor J is published.
    for field in 0..2{
        let mut local=copy_local(&stage.local);let mut x=copy_parts(&parent);
        if field==0{x.dc[LOCAL[5]]=1e308;local.dc[5]=1e308;}else{x.j[LOCAL[5]][LOCAL[5]]=1e308;local.physical_j[5][5]=1e308;}
        let saved=copy_parts(&x);assert!(binding::merge::<true>(&mut x,&local).is_err());same(&x,&saved);retry();failures+=1;atomic+=1;
    }
    let mut x=copy_parts(&parent);let mut delta=[0.;N];delta[LOCAL[5]]=1e-24;x.now=x.now.advanced(delta);assert!(x.now.valid());let saved=copy_parts(&x);
    assert!(binding::merge::<true>(&mut x,&stage.local).is_err());same(&x,&saved);retry();failures+=1;atomic+=1;
    println!("TRANSFER,{failures},{failures},{atomic},2,1");
}
