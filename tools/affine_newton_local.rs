pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/affine_newton_voice.rs"]mod circuit;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use circuit::*;
use std::io::{self,BufRead};
fn scene()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap()}
fn exact(a:[f64;M],b:[f64;M]){for k in 0..M{assert_eq!(a[k].to_bits(),b[k].to_bits());}}
fn main(){
    let mut w=Workspace::new();let mut reference=full::Workspace::new();let mut pairs=0;let mut cases=0;let mut entries=0;let mut retries=0;let mut rejects=0;
    let mut fraction=0_f64;let mut physical_backward=0_f64;let mut reduced_coeff=0_f64;let mut stages=0;
    for line in io::stdin().lock().lines(){
        let v:Vec<f64>=line.unwrap().split(',').map(|x|x.parse().unwrap()).collect();assert_eq!(v.len(),1185);let t=v[0];let h=v[1];let c=Controls{key:v[2],short:false,optional:false};let mut p=scene();p.time=t;
        let state=|b:usize|State{high:std::array::from_fn(|k|v[3+b*M+k]),low:std::array::from_fn(|k|v[3+b*M+N+k]),optional:false};
        let old=state(0);let mut s=[evaluate::<true>(p,old,increment(state(3),old),c,h,t+h/3.).unwrap(),evaluate::<true>(p,old,increment(state(4),old),c,h,t+h).unwrap()];
        let mut rhses=[[0.;M];24];rhses[0]=residual(&s).map(|v|-v);
        for i in 0..14{rhses[1+i][(i/7)*N+Z[i%7]]=1.;}
        for(i,k)in[54,55,66,70,172,173,184,188].into_iter().enumerate(){rhses[15+i][k]=1.;}
        rhses[23]=std::array::from_fn(|k|(((k*17+11)%31)as f64-15.)/31.);
        let mut originals=[[0.;M];24];for i in 0..24{originals[i]=reference.solve([full::solver::Stage{dc:&s[0].physical.j,mass:&s[0].physical.mass},full::solver::Stage{dc:&s[1].physical.j,mass:&s[1].physical.mass}],B,rhses[i]).unwrap();}
        let before=w.affine_statistics.preparations;let mut expected=[[0.;M];2];
        {
            let mut frame=w.prepare(&s).unwrap();let retained=frame.reduced_coefficients();let physical=frame.physical_coefficients();
            for i in 0..M{for k in 0..M{let expected=B[i/N][k/N]*s[k/N].physical.mass[i%N][k%N]+if i/N==k/N{s[i/N].physical.j[i%N][k%N]}else{0.};if expected==0.{assert_eq!(physical[i][k],0.);}else{assert_eq!(physical[i][k].to_bits(),expected.to_bits());}entries+=1;}}
            // Inspect the actual retained matrix; full directions below are the equivalence gate.
            for i in 0..RM{for k in 0..RM{assert!(retained[i][k].is_finite());reduced_coeff=reduced_coeff.max(retained[i][k].abs());}}
            for i in 0..24{
                let(_,dx)=frame.solve(rhses[i]).unwrap();let metric=frame.backward(rhses[i],dx).unwrap();physical_backward=physical_backward.max(metric);assert!(metric<=1e-11);
                let worst=(0..M).fold(0_f64,|m,k|m.max((dx[k]-originals[i][k]).abs()/(2e-9+1e-7*originals[i][k].abs())));fraction=fraction.max(worst);assert!(worst<=1.,"pair {pairs} rhs {i} direction {worst}");
                if i==0{expected[0]=dx;}if i==23{expected[1]=dx;}cases+=1;
            }
            if pairs==0{
                for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{for k in[0,54,55,56,63,67,117,118,235]{let mut bad=rhses[0];bad[k]=value;assert!(frame.solve(bad).is_err());exact(expected[0],frame.solve(rhses[0]).unwrap().1);rejects+=1;retries+=1;}}
            }
        }
        assert_eq!(w.affine_statistics.preparations,before+1);
        {let mut frame=w.prepare(&s).unwrap();exact(expected[0],frame.solve(rhses[0]).unwrap().1);exact(expected[1],frame.solve(rhses[23]).unwrap().1);retries+=2;}
        if pairs==0{
            // Finite products can cancel while their normalization overflows.
            let saved=s[0].physical.j[0];s[0].physical.j[0]=[0.;N];
            for k in 0..4{s[0].physical.j[0][k]=if k%2==0{1e308}else{-1e308};}
            let mut csr=affine::Sparse::new();csr.initialize(&s,B).unwrap();
            let mut d=[0.;M];d[..4].fill(0.5);
            assert!(csr.residual(&[0.;M],&d).is_err());s[0].physical.j[0]=saved;
            let retry=|w:&mut Workspace,s:&[Stage;2]|{let mut f=w.prepare(s).unwrap();exact(expected[0],f.solve(rhses[0]).unwrap().1);};
            for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{
                for(stage,row,col,mass)in[(0,0,0,false),(1,55,55,false),(0,117,117,true),(1,Z[0],0,true)]{
                    let original=if mass{s[stage].physical.mass[row][col]}else{s[stage].physical.j[row][col]};
                    if mass{s[stage].physical.mass[row][col]=value;}else{s[stage].physical.j[row][col]=value;}
                    // Drop the retry closure's borrow only around preparing a bad stage.
                    assert!(w.prepare(&s).is_err());
                    if mass{s[stage].physical.mass[row][col]=original;}else{s[stage].physical.j[row][col]=original;}retry(&mut w,&s);rejects+=1;retries+=1;
                }
            }
            let original=s[0].physical.mass[Z[0]][Z[0]];s[0].physical.mass[Z[0]][Z[0]]=1e-20;assert!(w.prepare(&s).is_err());s[0].physical.mass[Z[0]][Z[0]]=original;retry(&mut w,&s);rejects+=1;retries+=1;
            let row=s[0].physical.j[Z[0]];s[0].physical.j[Z[0]]=[0.;N];assert!(w.prepare(&s).is_err());s[0].physical.j[Z[0]]=row;retry(&mut w,&s);rejects+=1;retries+=1;
            let original=s[0].physical.j[0][Z[0]];s[0].physical.j[0][Z[0]]=1e-6;assert!(w.prepare(&s).is_err());s[0].physical.j[0][Z[0]]=original;retry(&mut w,&s);rejects+=1;retries+=1;
            let original=s[0].physical.j[Z[4]][Z[5]];let other=s[0].physical.j[67][Z[5]];s[0].physical.j[Z[4]][Z[5]]=1e308;s[0].physical.j[67][Z[5]]=1e308;assert!(w.prepare(&s).is_err());s[0].physical.j[Z[4]][Z[5]]=original;s[0].physical.j[67][Z[5]]=other;retry(&mut w,&s);rejects+=1;retries+=1;
            let saved=[s[0].physical.j,s[1].physical.j];
            for stage in &mut s{for i in 0..54{for k in 0..54{stage.physical.j[i][k]=if i==k{2.}else{0.001};}}}
            assert!(w.prepare(&s).is_err());s[0].physical.j=saved[0];s[1].physical.j=saved[1];retry(&mut w,&s);rejects+=1;retries+=1;
            // A legal new retained edge is incorporated, never masked by prior support.
            let col=(0..54).find(|k|s[0].physical.j[0][*k]==0.).unwrap();s[0].physical.j[0][col]=1e-20;
            {let mut f=Workspace::new();let frame=f.prepare(&s).unwrap();assert_eq!(frame.physical_coefficients()[0][col],1e-20);}
            s[0].physical.j[0][col]=0.;retry(&mut w,&s);retries+=1;
        }
        pairs+=1;stages+=2;
    }
    assert_eq!(pairs,24);assert_eq!(cases,576);let a=w.affine_statistics;let r=w.reduced.statistics;
    println!("LOCAL,{pairs},{stages},{cases},{entries},{rejects},{retries},{fraction:.17e},{physical_backward:.17e},{},{},{},{},{:.17e},{:.17e},{},{},{:.17e}",a.preparations,a.physical_solves,a.reduced_rhs,a.physical_refinements,a.maximum_initial_backward,a.maximum_final_backward,r.solves,r.refinements,r.max_final_backward);
}
