pub use rf_d_circuit::{junction_charge,StepError};
#[path="../crates/rf-d-circuit/src/hybrid_schur_voice.rs"] mod old;
#[path="../crates/rf-d-circuit/src/prepared_hybrid_voice.rs"] mod new;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer};
use std::io::{self,BufRead};
fn chain()->Chain{let(a,b,c)=lab::lab_parameters();Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn main(){
    for mode in 0..3{let mut p=chain();match mode{0=>p.circuit.r61_ohm=f64::NAN,1=>p.boundary.recovery.vca.second.output.output.tip_load_ohm=Some(0.),_=>p.conversion.temperature_k=f64::NAN};assert!(new::Parameters::new(p).is_err());}
    let mut count=0;let mut f=[0_f64;4];let mut fd=0_f64;let mut columns=0;let mut fast=[0_f64;2];
    for line in io::stdin().lock().lines(){
        let v:Vec<f64>=line.unwrap().split(',').map(|s|s.parse().unwrap()).collect();assert_eq!(v.len(),1185);
        let mut po=old::Parameters::new(chain()).unwrap();po.time=v[0];let mut pn=new::Parameters::new(chain()).unwrap();pn.time=v[0];let h=v[1];let key=v[2];
        let oh: [f64;118]=std::array::from_fn(|k|v[3+k]);let ol:[f64;118]=std::array::from_fn(|k|v[121+k]);
        for stage in 0..2{
            let dh:[f64;118]=std::array::from_fn(|k|v[3+(stage+1)*236+k]);let dl:[f64;118]=std::array::from_fn(|k|v[121+(stage+1)*236+k]);let t=v[0]+h*if stage==0{1./3.}else{1.};
            let os=old::State{high:oh,low:ol,optional:false};let od=old::State{high:dh,low:dl,optional:false};let ns=new::State{high:oh,low:ol,optional:false};let nd=new::State{high:dh,low:dl,optional:false};let oc=old::Controls{key,short:false,optional:false};let nc=new::Controls{key,short:false,optional:false};
            let a=old::parts(po,os,od,oc,h,t).unwrap();let b=new::parts::<true>(pn,ns,nd,nc,h,t).unwrap();let r=new::parts::<false>(pn,ns,nd,nc,h,t).unwrap();assert_eq!(a.now.high,b.now.high);assert_eq!(a.now.low,b.now.low);assert_eq!(r.now.high,b.now.high);assert_eq!(r.now.low,b.now.low);
            for i in 0..118{
                f[0]=f[0].max((a.dc[i]-b.dc[i]).abs()/(20e-12+1e-7*a.dc[i].abs()));f[1]=f[1].max((a.dq[i]-b.dq[i]).abs()/(20e-12+1e-7*a.dq[i].abs()));
                fast[0]=fast[0].max((r.dc[i]-b.dc[i]).abs()/(20e-12+1e-7*b.dc[i].abs()));fast[1]=fast[1].max((r.dq[i]-b.dq[i]).abs()/(20e-12+1e-7*b.dq[i].abs()));
                for k in 0..118{f[2]=f[2].max((a.j[i][k]-b.j[i][k]).abs()/(2e-9+2e-7*a.j[i][k].abs()));f[3]=f[3].max((a.mass[i][k]-b.mass[i][k]).abs()/(2e-9+2e-7*a.mass[i][k].abs()));}
            }
            if [0,6,12,18].contains(&count)&&stage==0{
                for k in 0..118{
                    let mut up=[0.;118];up[k]=1e-6;let mut down=[0.;118];down[k]=-1e-6;
                    let u=new::parts::<true>(pn,ns,nd.advanced(up),nc,h,t).unwrap();let d=new::parts::<true>(pn,ns,nd.advanced(down),nc,h,t).unwrap();
                    for i in 0..118{for (got,want) in [(b.j[i][k],(u.dc[i]-d.dc[i])/2e-6),(b.mass[i][k],(u.dq[i]-d.dq[i])/2e-6)]{fd=fd.max((got-want).abs()/(2e-9+2e-5*want.abs()));}}
                    columns+=1;
                }
            }
        }count+=1;
    }
    assert_eq!(count,24);assert_eq!(columns,472);assert!(f.iter().chain(fast.iter()).all(|v|*v<=1.)&&fd<=1.,"stamp {f:?} fd {fd} fast {fast:?}");println!("LOCAL,48,{},{},{},{},{fd:.17e},{columns},3,{},{}",f[0],f[1],f[2],f[3],fast[0],fast[1]);
}
