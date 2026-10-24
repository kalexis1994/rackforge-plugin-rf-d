//! Conditional fixed-CV mixer/C27 coupling. BASE_Q29=0; no full-filter claim.
#[path="vco_family_kernel.rs"]mod family;
pub const C:f64=10e-6;
#[derive(Clone,Copy,Debug,PartialEq)]pub struct State{pub phase:[f64;2],pub bus:[f64;2]}
#[derive(Clone,Copy,Debug,PartialEq)]pub enum Error{Domain,Budget,Newton}
#[derive(Clone,Copy,Debug)]pub struct Observation{pub value:[f64;19],pub other_a:f64,pub board_a:f64}
#[derive(Clone,Copy,Debug)]pub struct Accepted{pub state:State,pub observation:Observation,pub residual_ratio:f64,pub correction_ratio:f64,pub charge_residual_c:f64,pub iterations:usize}
fn sum(a:f64,b:f64)->[f64;2]{let s=a+b;let v=s-a;[s,(a-(s-v))+(b-v)]}
fn advance(old:[f64;2],d:f64)->[f64;2]{let a=sum(old[0],d);let b=sum(old[1],a[1]);let c=sum(a[0],b[0]);sum(c[0],c[1]+b[1])}
pub fn other_g(load:usize)->Result<f64,Error>{match load{0=>Ok(1./33000.),1=>Ok(1./33000.+2./39250.+1./17250.),_=>Err(Error::Domain)}}
pub fn initialize(bus:f64)->Result<State,Error>{if !bus.is_finite()||!(-0.125..=0.125).contains(&bus){return Err(Error::Domain);}Ok(State{phase:[0.,0.],bus:[bus,0.]})}
pub fn observe(cv:f64,load:usize,s:State)->Result<Observation,Error>{
    let b=s.bus[0]+s.bus[1];let p=(s.phase[0]+s.phase[1]).rem_euclid(1.);
    let q=family::evaluate(cv,b,p).map_err(|_|Error::Domain)?;let other=other_g(load)?*b;
    Ok(Observation{value:q.values,other_a:other,board_a:-q.values[11]-other})
}
fn weights(cv:f64)->[f64;4]{std::array::from_fn(|i|{let mut x=1.;for j in 0..4{if i!=j{x*=(cv-family::CV[j])/(family::CV[i]-family::CV[j]);}}x})}
fn frequency(cv:f64,bus:f64)->f64{let w=weights(cv);let u=(bus+0.125)/0.25;let mut log=0.;for i in 0..4{log+=w[i]*((1.-u)*crate::data::LOG_FREQUENCY[i][0]+u*crate::data::LOG_FREQUENCY[i][1]);}log.exp2()}
fn saw_phase_slope(cv:f64,bus:f64,phase:f64)->f64{
    let w=weights(cv);let u=(bus+0.125)/0.25;let mut out=0.;
    for n in 1..=64{let(s,c)=(std::f64::consts::TAU*n as f64*phase).sin_cos();for i in 0..4{for j in 0..2{let q=crate::data::COEFFICIENTS[i][j][0][n];out+=w[i]*if j==0{1.-u}else{u}*2.*std::f64::consts::TAU*n as f64*(-q[0]*s-q[1]*c);}}}out
}
pub fn step(cv:f64,load:usize,old:State,h:f64,budget:usize)->Result<Accepted,Error>{
    if !h.is_finite()||!(1e-9..=1e-6).contains(&h)||!old.phase.iter().chain(old.bus.iter()).all(|x|x.is_finite())||old.phase[0]<0.||old.phase[0]>3.||sum(old.phase[0],old.phase[1])!=old.phase||sum(old.bus[0],old.bus[1])!=old.bus{return Err(Error::Domain);}
    if budget==0||budget>32{return Err(Error::Budget);}
    let previous=observe(cv,load,old)?;let g=other_g(load)?;let mut delta=h*previous.board_a/C;
    for iteration in 1..=budget{
        let b=advance(old.bus,delta);let bus=b[0]+b[1];if !(-0.125..=0.125).contains(&bus){return Err(Error::Domain);}
        let f=frequency(cv,bus);let phase=advance(old.phase,h*0.5*(previous.value[0]+f));let p=(phase[0]+phase[1]).rem_euclid(1.);
        let q=family::evaluate(cv,bus,p).map_err(|_|Error::Domain)?;let current=q.values[11]+g*bus;let residual=delta+h*0.5/C*(-previous.board_a+current);
        let ip=-0.5/39250.*saw_phase_slope(cv,bus,p);let j=1.+h*0.5/C*(q.dbus[11]+g+ip*h*0.5*q.dbus[0]);
        let correction=-residual/j;let rr=(residual*C/h).abs()/1e-13;let cr=correction.abs()/1e-12;
        if !rr.is_finite()||!cr.is_finite()||!j.is_finite()||j<=0.{return Err(Error::Newton);}
        if rr<=1.&&cr<=1.{let state=State{phase,bus:b};return Ok(Accepted{state,observation:Observation{value:q.values,other_a:g*bus,board_a:-current},residual_ratio:rr,correction_ratio:cr,charge_residual_c:residual*C,iterations:iteration});}
        delta+=correction;
    }Err(Error::Newton)
}
/// Atomic publication; failures leave all HIGH/LOW memories unchanged.
pub fn process(cv:f64,load:usize,s:&mut State,h:f64,budget:usize)->Result<Accepted,Error>{let q=step(cv,load,*s,h,budget)?;*s=q.state;Ok(q)}
