pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/split_ladder_voice.rs"]mod circuit;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use circuit::*;
#[path="../crates/rf-d-circuit/src/ladder_voice.rs"]mod previous;
fn copy_parts(p:&Parts)->Parts{Parts{dc:p.dc,j:p.j,dq:p.dq,mass:p.mass,now:p.now}}
fn equal_parts(a:&Parts,b:&Parts){
 for(a,b)in a.dc.iter().chain(a.dq.iter()).chain(a.j.iter().flatten()).chain(a.mass.iter().flatten()).chain(a.now.high.iter()).chain(a.now.low.iter())
 .zip(b.dc.iter().chain(b.dq.iter()).chain(b.j.iter().flatten()).chain(b.mass.iter().flatten()).chain(b.now.high.iter()).chain(b.now.low.iter())){assert_eq!(a.to_bits(),b.to_bits());}
 assert_eq!(a.now.optional,b.now.optional);
}
fn oldstate(s:State)->previous::State{previous::State{high:s.high,low:s.low,optional:s.optional}}
fn parent_scene()->parent::Parameters{let(a,b,c)=lab::lab_parameters();parent::Parameters::new(rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn previous_scene()->previous::Parameters{let(a,b,c)=lab::lab_parameters();previous::Parameters::new(rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn transfer_guards(parent:&Parts,local:&ladder::Solution)->usize{
 let mut valid=copy_parts(parent);binding::validate_parent::<true>(&valid).unwrap();binding::merge::<true>(&mut valid,local).unwrap();
 let retry=||{let mut q=copy_parts(parent);binding::validate_parent::<true>(&q).unwrap();binding::merge::<true>(&mut q,local).unwrap();equal_parts(&q,&valid);};
 let mut count=0;
 for k in Z.into_iter().chain([67,68,69]){
  let mut q=copy_parts(parent);q.dc[k]=1e-30;assert!(binding::validate_parent::<true>(&q).is_err());assert!(binding::validate_parent::<false>(&q).is_err());retry();count+=2;
  for flip in[false,true]{let mut q=copy_parts(parent);if flip{q.j[0][k]=1e-30;}else{q.j[k][0]=1e-30;}assert!(binding::validate_parent::<true>(&q).is_err());retry();count+=1;}
 }
 for v in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{let mut q=copy_parts(parent);q.j[0][Z[0]]=v;assert!(binding::validate_parent::<true>(&q).is_err());retry();count+=1;}
 let mut q=copy_parts(parent);let mut delta=[0.;N];delta[Z[0]]=1e-6;q.now=q.now.advanced(delta);let saved=copy_parts(&q);assert!(binding::merge::<true>(&mut q,local).is_err());equal_parts(&q,&saved);retry();count+=1;
 for v in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{let mut q=copy_parts(parent);q.dc[0]=v;let saved=copy_parts(&q);assert!(binding::merge::<true>(&mut q,local).is_err());equal_parts(&q,&saved);retry();count+=1;}
 let mut q=copy_parts(parent);q.now.low[Z[0]]=1.;let saved=copy_parts(&q);assert!(binding::merge::<true>(&mut q,local).is_err());equal_parts(&q,&saved);retry();count+=1;
 // Retained-parent topology may grow: a legal new edge is kept, then removed.
 let column=(0..54).find(|k|parent.j[0][*k]==0.).unwrap();let mut q=copy_parts(parent);q.j[0][column]=1e-20;
 binding::validate_parent::<true>(&q).unwrap();binding::merge::<true>(&mut q,local).unwrap();assert_eq!(q.j[0][column],1e-20);retry();
 count
}

use std::io::{self,BufRead};
fn scene()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn maximum(x:impl Iterator<Item=f64>)->f64{x.fold(0_f64,|m,v|m.max(v.abs()))}
fn same(a:[f64;M],b:[f64;M]){for k in 0..M{assert_eq!(a[k].to_bits(),b[k].to_bits());}}
fn main(){
    let mut workspace=Workspace::new();let mut stages=0;let mut pairs=0;let mut fdcols=0;let mut directions=0;let mut rejects=0;
    let mut reconstruction_v=0_f64;let mut original_a=0_f64;let mut direction_fraction=0_f64;let mut fd_fraction=0_f64;let mut charge_a=0_f64;
    let mut physical_dc=0_f64;let mut physical_j=0_f64;let mut reduced_j=0_f64;let mut offsets=0_f64;let mut kernel_seeds=0;let mut kernel_error=0_f64;let mut guards=0;let mut mode_checks=0;
    let mut congruence_entries=0;
    for variant in 0..8{
     let j:[[f64;16];16]=std::array::from_fn(|i|std::array::from_fn(|k|{let v=(((i*17+k*5+variant)%23)as f64-11.)/8.;if variant==7&&i%3==0{v*1e20}else{v}}));
     let a=ladder::congruence(&j);let b=previous::ladder::congruence(&j);for i in 0..16{for k in 0..16{if a[i][k]==0.{assert_eq!(b[i][k],0.);}else{assert_eq!(a[i][k].to_bits(),b[i][k].to_bits());}congruence_entries+=1;}}
    }
    for line in io::stdin().lock().lines(){
        let v:Vec<f64>=line.unwrap().split(',').map(|x|x.parse().unwrap()).collect();assert_eq!(v.len(),1185);
        let t=v[0];let h=v[1];let c=Controls{key:v[2],short:false,optional:false};let mut p=scene();p.time=t;
        let state=|b:usize|State{high:std::array::from_fn(|k|v[3+b*M+k]),low:std::array::from_fn(|k|v[3+b*M+N+k]),optional:false};
        let old=state(0);let a=state(3);let b=state(4);let da=increment(a,old);let db=increment(b,old);
        let s=[evaluate::<true>(p,old,da,c,h,t+h/3.).unwrap(),evaluate::<true>(p,old,db,c,h,t+h).unwrap()];
        let mut pp=previous_scene();pp.time=t;let po=oldstate(old);
        let pd=|d:Reduced|previous::Reduced{high:d.high,low:d.low};
        let reference=[previous::evaluate::<true>(pp,po,pd(da),previous::Controls{key:c.key,short:c.short,optional:c.optional},h,t+h/3.).unwrap(),previous::evaluate::<true>(pp,po,pd(db),previous::Controls{key:c.key,short:c.short,optional:c.optional},h,t+h).unwrap()];
        for stage in 0..2{
         let original=parts::<true>(p,old,s[stage].delta,c,h,t+h*if stage==0{1./3.}else{1.}).unwrap();
         let fast=evaluate::<false>(p,old,if stage==0{da}else{db},c,h,t+h*if stage==0{1./3.}else{1.}).unwrap();
         for i in 0..N{
          physical_dc=physical_dc.max((original.dc[i]-s[stage].physical.dc[i]).abs());assert_eq!(original.dq[i],s[stage].physical.dq[i]);
          assert_eq!(fast.physical.dc[i].to_bits(),s[stage].physical.dc[i].to_bits());assert_eq!(fast.physical.dq[i].to_bits(),s[stage].physical.dq[i].to_bits());
          for k in 0..N{physical_j=physical_j.max((original.j[i][k]-s[stage].physical.j[i][k]).abs());assert_eq!(original.mass[i][k],s[stage].physical.mass[i][k]);}
         }
         assert!(physical_dc<=20e-12&&physical_j<=2e-9);
         for i in 0..R{for k in 0..R{let prior=reference[stage].j[i][k];let fraction=(s[stage].j[i][k]-prior).abs()/(2e-9+2e-5*prior.abs());reduced_j=reduced_j.max(fraction);assert!(fraction<=1.);assert_eq!(s[stage].mass[i][k],reference[stage].mass[i][k]);}}
         let parent=binding::parent_parts::<true>(parent_scene(),t,old,s[stage].delta,c,h,t+h*if stage==0{1./3.}else{1.}).unwrap();let mut transferred=copy_parts(&parent);let offset=binding::merge::<true>(&mut transferred,&s[stage].local).unwrap();offsets=offsets.max(offset);equal_parts(&transferred,&s[stage].physical);mode_checks+=1;
         if pairs==0&&stage==0{guards=transfer_guards(&parent,&s[stage].local);}
         let(card,_,_)=lab::lab_parameters();let current=ladder::Nodes{high:LOCAL.map(|k|s[stage].physical.now.high[k]),low:LOCAL.map(|k|s[stage].physical.now.low[k])};let(z,y)=ladder::coordinates(current).unwrap();
         for amplitude in[0.001,-0.01]{
          let seed=z.advanced(std::array::from_fn(|k|if k%2==0{amplitude}else{-amplitude}));
          let new=ladder::Model::new(card).unwrap().solve(y,seed,ladder::Budget::default()).unwrap();
          let old=previous::ladder::Model::new(card).unwrap().solve(previous::ladder::Retained{high:y.high,low:y.low},previous::ladder::Algebraic{high:seed.high,low:seed.low},previous::ladder::Budget::default()).unwrap();
          let error=maximum((0..16).map(|k|(new.nodes.high[k]-old.nodes.high[k])+(new.nodes.low[k]-old.nodes.low[k])));kernel_error=kernel_error.max(error);assert!(error<=2e-9);kernel_seeds+=1;
          for i in 0..9{assert!((new.reaction[i]-old.reaction[i]).abs()<=20e-12);for k in 0..9{assert!((new.reaction_j[i][k]-old.reaction_j[i][k]).abs()<=2e-9+2e-5*old.reaction_j[i][k].abs());}}
         }
        }
        for(stage,target)in[(0,a),(1,b)]{
            let phys=&s[stage].physical;let err=maximum((0..N).map(|k|(phys.now.high[k]-target.high[k])+(phys.now.low[k]-target.low[k])));reconstruction_v=reconstruction_v.max(err);assert!(err<=2e-9,"reconstruction {err}");
            let expected=parts::<true>(p,old,state(1+stage),c,h,t+h*if stage==0{1./3.}else{1.}).unwrap();
            let err=maximum((0..N).map(|k|phys.dq[k]-expected.dq[k]));charge_a=charge_a.max(err);assert!(err<=20e-12,"charge {err}");
            // Exact zero charge along eliminated coordinates, in both rows and columns.
            for k in 0..7{for row in 0..N{
                assert_eq!(phys.mass[row][Z[k]]+if k>=4{phys.mass[row][67+k-4]}else{0.},0.);
                assert_eq!(phys.mass[Z[k]][row]+if k>=4{phys.mass[67+k-4][row]}else{0.},0.);
            }}
            for row in 0..R{for col in 0..R{assert!(s[stage].mass[row][col].is_finite());}}
            if pairs==0{
                for col in 0..R{
                    let base=if stage==0{da}else{db};let mut step=[0.;R];step[col]=1e-6;
                    let plus=evaluate::<false>(p,old,base.advanced(step),c,h,t+h*if stage==0{1./3.}else{1.}).unwrap();step[col]=-1e-6;
                    let minus=evaluate::<false>(p,old,base.advanced(step),c,h,t+h*if stage==0{1./3.}else{1.}).unwrap();
                    for row in 0..R{let a=RETAINED[row];let sign=if(67..=69).contains(&a){-1.}else{1.};let fd=sign*(plus.physical.dc[a]-minus.physical.dc[a])/2e-6;let frac=(fd-s[stage].j[row][col]).abs()/(2e-9+2e-5*fd.abs());fd_fraction=fd_fraction.max(frac);assert!(frac<=1.,"FD {stage} {row},{col}: {frac}");}
                    fdcols+=1;
                }
            }
            stages+=1;
        }
        let r=residual(&s);let root_error=maximum(r.into_iter());original_a=original_a.max(root_error);assert!(root_error<=20e-12);
        // The physical correction of the actual reduced residual vs complete system.
        let(_,d)=direction(&mut workspace,&s,r.map(|v|-v)).unwrap();let control=original_direction(&mut workspace,&s,r.map(|v|-v)).unwrap();
        let frac=(0..M).fold(0_f64,|m,k|m.max((d[k]-control[k]).abs()/(2e-9+1e-7*control[k].abs())));direction_fraction=direction_fraction.max(frac);assert!(frac<=1.,"direction {frac}");directions+=1;
        // Arbitrary retained RHS, with exactly zero eliminated covector equations.
        for port in[54,55,Y[0],Y[8],R-1]{
            let mut rhs=[0.;M];let phys=RETAINED[port];rhs[phys]=if(67..=69).contains(&phys){-1.}else{1.};
            if (67..=69).contains(&phys){rhs[Z[4+phys-67]]=-rhs[phys];}
            let(_,got)=direction(&mut workspace,&s,rhs).unwrap();let expected=original_direction(&mut workspace,&s,rhs).unwrap();
            let frac=(0..M).fold(0_f64,|m,k|m.max((got[k]-expected[k]).abs()/(2e-9+1e-7*expected[k].abs())));direction_fraction=direction_fraction.max(frac);assert!(frac<=1.,"port direction {port} {frac}");directions+=1;
        }
        if pairs==0{
            let rhs=r.map(|v|-v);let(_,good)=direction(&mut workspace,&s,rhs).unwrap();
            for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{
                for k in[0,54,55,56,63,67,117,118,235]{let mut bad=rhs;bad[k]=value;assert!(direction(&mut workspace,&s,bad).is_err());same(good,direction(&mut workspace,&s,rhs).unwrap().1);rejects+=1;}
                let mut bad=da;bad.high[Y[0]]=value;assert!(evaluate::<true>(p,old,bad,c,h,t).is_err());same(good,direction(&mut workspace,&s,rhs).unwrap().1);rejects+=1;
            }
            let mut bad=da;bad.low[55]=1.;assert!(evaluate::<true>(p,old,bad,c,h,t).is_err());rejects+=1;
            for budget in[0,81]{assert!(radau(&mut workspace,p,old,c,h,budget).is_err());same(good,direction(&mut workspace,&s,rhs).unwrap().1);rejects+=1;}
            for value in[f64::NAN,f64::INFINITY,-1.]{let mut bad=p;bad.time=value;assert!(evaluate::<true>(bad,old,da,c,h,t).is_err());same(good,direction(&mut workspace,&s,rhs).unwrap().1);rejects+=1;}
        }
        pairs+=1;
    }
    assert_eq!(pairs,24);assert_eq!(stages,48);let z=workspace.statistics;
    println!("LOCAL,{pairs},{stages},{directions},{fdcols},{rejects},{reconstruction_v:.17e},{original_a:.17e},{direction_fraction:.17e},{fd_fraction:.17e},{charge_a:.17e},{},{},{:.17e},{:.17e},{}",z.solves,z.refinements,z.max_initial_backward,z.max_final_backward,z.max_nonzeros);
    println!("SPLIT,{physical_dc:.17e},{physical_j:.17e},{reduced_j:.17e},{offsets:.17e},{kernel_seeds},{kernel_error:.17e},{guards},{mode_checks},{congruence_entries},1");
}
