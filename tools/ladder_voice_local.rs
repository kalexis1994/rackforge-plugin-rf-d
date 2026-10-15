pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/ladder_voice.rs"]mod circuit;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use circuit::*;
use std::io::{self,BufRead};
fn scene()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn maximum(x:impl Iterator<Item=f64>)->f64{x.fold(0_f64,|m,v|m.max(v.abs()))}
fn same(a:[f64;M],b:[f64;M]){for k in 0..M{assert_eq!(a[k].to_bits(),b[k].to_bits());}}
fn main(){
    let mut workspace=Workspace::new();let mut stages=0;let mut pairs=0;let mut fdcols=0;let mut directions=0;let mut rejects=0;
    let mut reconstruction_v=0_f64;let mut original_a=0_f64;let mut direction_fraction=0_f64;let mut fd_fraction=0_f64;let mut charge_a=0_f64;
    for line in io::stdin().lock().lines(){
        let v:Vec<f64>=line.unwrap().split(',').map(|x|x.parse().unwrap()).collect();assert_eq!(v.len(),1185);
        let t=v[0];let h=v[1];let c=Controls{key:v[2],short:false,optional:false};let mut p=scene();p.time=t;
        let state=|b:usize|State{high:std::array::from_fn(|k|v[3+b*M+k]),low:std::array::from_fn(|k|v[3+b*M+N+k]),optional:false};
        let old=state(0);let a=state(3);let b=state(4);let da=increment(a,old);let db=increment(b,old);
        let s=[evaluate::<true>(p,old,da,c,h,t+h/3.).unwrap(),evaluate::<true>(p,old,db,c,h,t+h).unwrap()];
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
}
