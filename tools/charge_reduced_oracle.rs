use rf_d_circuit::{chain_charge::{self,Parameters,State,N},StepError};
#[path="vco_cv_load_linear.rs"]mod linear;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use std::io::{Write,BufWriter};
const BUS:usize=66;const Y:f64=1./39250.;const GAMMA:f64=1.-std::f64::consts::FRAC_1_SQRT_2;
fn parameters(case:usize)->Parameters{let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=if case==0{200.}else{200000.};Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new(if case==0{[false,true,true,true,true]}else{[false,false,false,false,true]},[0.5;4]).unwrap()}}
fn initial(p:Parameters)->Result<State,StepError>{let x=rf_d_circuit::circuit66::initial_state(p.circuit,p.conversion,p.headphone,p.boundary,lab::SEED)?;let mut s=[0.;N];s[..66].copy_from_slice(&x.node_v);s[67]=s[22];let mut s=State::from_nodes(s);
 for _ in 0..64{let a=chain_charge::linearize_compensated(p,[0.;5],s,State::from_nodes([0.;N]),1e-6)?;let mut r=a.dc;let mut j=a.dc_jacobian;r[BUS]+=Y*(s.high[BUS]+s.low[BUS]);j[BUS][BUS]+=Y;let d=linear::solve_linear_sparse(j,r.map(|x|-x))?;
  if r.iter().all(|x|x.abs()<=1e-13)&&d.iter().all(|x|x.abs()<=2e-9){return Ok(s);}s=s.advanced(d);
 }Err(StepError::IterationBudget)
}
fn step(p:Parameters,old:State,h:f64,u:f64)->Result<State,StepError>{let mut delta=State::from_nodes([0.;N]);for _ in 0..64{let a=chain_charge::linearize_compensated(p,[0.;5],old,delta,h)?;let mut r=[0.;N];let mut j=[[0.;N];N];for i in 0..N{r[i]=a.dc[i]+a.charge_over_h[i];for k in 0..N{j[i][k]=a.dc_jacobian[i][k]+a.mass_over_h[i][k];}}let now=old.advanced(delta.high).advanced(delta.low);r[BUS]+=Y*(now.high[BUS]+now.low[BUS]-0.5*u);j[BUS][BUS]+=Y;let d=linear::solve_linear_sparse(j,r.map(|x|-x))?;
 if r.iter().all(|x|x.abs()<=1e-13)&&d.iter().all(|x|x.abs()<=2e-9){return Ok(now);}delta=delta.advanced(d);
 }Err(StepError::IterationBudget)}
fn input(a:f64,t:f64)->f64{a*((std::f64::consts::TAU*137.*t).sin()+0.3*(std::f64::consts::TAU*1103.*t).sin())}
fn walk(case:usize,a:f64,h:f64)->Result<(),Box<dyn std::error::Error>>{let p=parameters(case);let mut s=initial(p).map_err(|e|format!("DC:{e:?}"))?;let n=(0.004/h).round()as usize;let mut out=BufWriter::new(std::io::stdout().lock());for k in 0..=n{for v in [k as f64*h,input(a,k as f64*h)].into_iter().chain(s.high).chain(s.low){out.write_all(&v.to_le_bytes())?;}if k==n{break;}let first=step(p,s,GAMMA*h,input(a,(k as f64+GAMMA)*h)).map_err(|e|format!("stage1 {k}:{e:?}"))?;
 let difference=first.advanced(s.high.map(|x|-x)).advanced(s.low.map(|x|-x));let alpha=(1.-GAMMA)/GAMMA;let hist=s.advanced(difference.high.map(|x|alpha*x)).advanced(difference.low.map(|x|alpha*x));s=step(p,hist,GAMMA*h,input(a,(k+1)as f64*h)).map_err(|e|format!("stage2 {k}:{e:?}"))?;
 }out.flush()?;Ok(())}
fn export()->Result<(),Box<dyn std::error::Error>>{let mut out=BufWriter::new(std::io::stdout().lock());for case in 0..2{let p=parameters(case);let s=initial(p).map_err(|e|format!("DC:{e:?}"))?;let a=chain_charge::linearize_compensated(p,[0.;5],s,State::from_nodes([0.;N]),1e-6).map_err(|e|format!("STAMP:{e:?}"))?;
 for(tag,values)in[("DC",s.high.into_iter().chain(s.low).collect::<Vec<_>>()),("G",a.dc_jacobian.into_iter().flatten().collect::<Vec<_>>()),("M",a.mass_over_h.into_iter().flatten().map(|v|v*1e-6).collect::<Vec<_>>())]{write!(out,"{tag},{case}")?;for v in values{write!(out,",{v:.17e}")?;}writeln!(out)?;}
 }out.flush()?;Ok(())}
fn main()->Result<(),Box<dyn std::error::Error>>{let a:Vec<_>=std::env::args().collect();if a.len()==2&&a[1]=="export"{export()}else if a.len()==4{walk(a[1].parse()?,a[2].parse()?,a[3].parse::<f64>()?*1e-9)}else{Err("export | case amplitude step_ns".into())}}
