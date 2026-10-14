pub use rf_d_circuit::{junction_charge,StepError};
#[path="../crates/rf-d-circuit/src/dual_chain.rs"] mod circuit;
#[allow(dead_code)] #[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use circuit::*;
use rf_d_circuit::{chain_charge::Parameters as Chain,mixer_on::OnMixer};
use std::{fs,io::{Write,BufWriter},time::Instant};
const TICK:f64=1e-6/1073741824.;
fn scene()->Parameters{let(a,b,c)=lab::lab_parameters();Parameters::new(Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([true,false,false,false,false],[0.5;4]).unwrap()}).unwrap()}
fn vals(w:&mut impl Write,a:impl IntoIterator<Item=f64>){for v in a{write!(w,",{v:.17e}").unwrap();}}
fn state(w:&mut impl Write,s:State){vals(w,s.high.into_iter().chain(s.low));}
fn root(w:&mut impl Write,old:State,q:&Pair,c:Controls,p:Parameters,h:f64,jac:bool){
    write!(w,"ROOT,{:.17e},{h:.17e},{}",p.time,c.key).unwrap();state(w,old);
    for s in q.delta.into_iter().chain(q.stages){state(w,s);}vals(w,[q.residual_a,q.correction_v]);writeln!(w).unwrap();
    if jac{for (i,d) in q.delta.into_iter().enumerate(){let a=parts(p,old,d,c,h,p.time+h*if i==0{1./3.}else{1.}).unwrap();write!(w,"STAMP").unwrap();vals(w,a.j.into_iter().flatten());vals(w,a.mass.into_iter().flatten());writeln!(w).unwrap();}}
}
fn main()->Result<(),String>{
    let args:Vec<_>=std::env::args().collect();let bytes=fs::read(&args[1]).map_err(|e|e.to_string())?;if bytes.len()!=8*N{return Err("seed".into());}
    let seed=std::array::from_fn(|k|f64::from_le_bytes(bytes[8*k..8*k+8].try_into().unwrap()));
    let maximum:u64=args[2].parse().unwrap();let start=Instant::now();let p=scene();let mut s=initial(p,seed,false).map_err(|e|format!("DC:{e:?}"))?;
    let mut w=BufWriter::new(std::io::stdout());write!(w,"DC").unwrap();state(&mut w,s);let d=dc(p,s,Controls::default()).unwrap();vals(&mut w,d.dc);vals(&mut w,d.j.into_iter().flatten());writeln!(w).unwrap();
    let old=s;for bad in [f64::NAN,0.,-1.]{assert!(advance(p,&mut s,Controls::default(),bad).is_err());assert_eq!(old,s);}
    let mut ticks=0_u64;let mut proposal=maximum*1073741824;let mut steps=0;let mut replays=0;let mut roots=0;
    let limit=36000*1073741824;let mut next_grid=250*1073741824;
    while ticks<limit{
        let event=[1000,10000,20000,30000,36000].into_iter().map(|v|v*1073741824).find(|&t|t>ticks).unwrap();
        let edge=event.min(next_grid);let remain=edge-ticks;let span=proposal.min(1_u64<<(63-remain.leading_zeros()));
        let time=ticks as f64*TICK;let p={let mut q=p;q.time=time;q};let c=Controls{key:if (1000*1073741824..10000*1073741824).contains(&ticks)||(20000*1073741824..30000*1073741824).contains(&ticks){10.}else{0.},short:false,optional:false};
        let old=s;let q=advance(p,&mut s,c,span as f64*TICK).map_err(|e|format!("TRANSIENT ticks={ticks} error={e:?}"))?;
        let elapsed=(q.h/TICK).round() as u64;assert_eq!(q.h.to_bits(),(elapsed as f64*TICK).to_bits());assert!(elapsed>0&&elapsed<=span);ticks+=elapsed;steps+=1;
        let selected=steps==1 || (ticks==edge&&edge==event) || (old.high[40]-4.)*(s.high[40]-4.)<0.;
        if selected {
            let mut replay=old;let qq=advance(p,&mut replay,c,span as f64*TICK).unwrap();assert_eq!(s,replay);assert_eq!(q.h.to_bits(),qq.h.to_bits());replays+=1;
            root(&mut w,old,&q.coarse,c,p,q.h,roots<2);root(&mut w,old,&q.fine[0],c,p,q.h/2.,false);root(&mut w,q.fine[0].stages[1],&q.fine[1],c,{let mut pp=p;pp.time=time+q.h/2.;pp},q.h/2.,false);roots+=3;
        }
        proposal=if q.error<0.05{(2*elapsed).min(maximum*1073741824)}else{elapsed};
        if ticks==next_grid{write!(w,"GRID,{ticks}").unwrap();state(&mut w,s);vals(&mut w,currents(s));writeln!(w).unwrap();next_grid+=250*1073741824;}
    }
    write!(w,"FINAL,{steps},{replays},{roots},3").unwrap();vals(&mut w,[start.elapsed().as_secs_f64()]);state(&mut w,s);writeln!(w).unwrap();w.flush().unwrap();Ok(())
}
