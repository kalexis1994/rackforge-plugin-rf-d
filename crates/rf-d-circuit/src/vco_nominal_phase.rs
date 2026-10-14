//! Nominal periodic VCO approximation with exact loaded output resistor port.
//! VCO_FASE_NOMINAL_PROTOCOLO: settled scene only; no CV/startup/voice admission.
#[path="vco_phase_profile.rs"] pub mod profile;
#[path="vco_output_port.rs"] pub mod output;
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct InvalidInput;
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct State{phase:f64,low:f64}
fn two_sum(a:f64,b:f64)->(f64,f64){let s=a+b;let v=s-a;(s,(a-(s-v))+(b-v))}
fn cycle(value:f64)->f64{let p=value.rem_euclid(1.);if p>=1.{0.}else{p}}
pub fn sources(phase:f64)->Result<[f64;2],InvalidInput> {
    if !phase.is_finite()||!(0. ..1.).contains(&phase){return Err(InvalidInput);}
    let angle=std::f64::consts::TAU*phase;let(s,c)=angle.sin_cos();
    let mut wave=[profile::DRIVE[0][0],profile::TRIANGLE[0][0]];let(mut sn,mut cn)=(s,c);
    for n in 1..53 {
        for k in 0..2 {let q=if k==0{profile::DRIVE[n]}else{profile::TRIANGLE[n]};wave[k]+=2.*(q[0]*cn-q[1]*sn);}
        (sn,cn)=(sn*c+cn*s,cn*c-sn*s);
    }
    Ok(wave)
}
pub fn observe(time_s:f64,bus_v:f64)->Result<output::Port,InvalidInput> {
    if !time_s.is_finite()||!(0. ..=1000.).contains(&time_s)||!bus_v.is_finite()||bus_v.abs()>2. {return Err(InvalidInput);}
    let phase=cycle((time_s-profile::EPOCH_S)*profile::FREQUENCY_HZ);
    let v=sources(phase)?;output::evaluate(0.5,[v[0],v[1],0.,bus_v]).map_err(|_|InvalidInput)
}
impl State {
    pub fn at_time(time_s:f64)->Result<Self,InvalidInput> {
        if !time_s.is_finite()||!(0. ..=1000.).contains(&time_s){return Err(InvalidInput);}
        Ok(Self{phase:cycle((time_s-profile::EPOCH_S)*profile::FREQUENCY_HZ),low:0.})
    }
    pub fn phase(self)->f64{let p=self.phase+self.low;if p<0.||p>=1.{cycle(p)}else{p}}
    /// End-of-sample output; atomic phase publication after a valid loaded port.
    pub fn process(&mut self,rate_hz:f64,bus_v:f64)->Result<output::Port,InvalidInput> {
        if !rate_hz.is_finite()||!(48000. ..=192000.).contains(&rate_hz)||!bus_v.is_finite()||bus_v.abs()>2. {return Err(InvalidInput);}
        let(h,l)=two_sum(self.phase,profile::FREQUENCY_HZ/rate_hz);
        let(h,l)=two_sum(h,l+self.low);let(h,l)=if h>=1.{let(a,b)=two_sum(h,-1.);two_sum(a,b+l)}else{(h,l)};
        let candidate=Self{phase:h,low:l};let v=sources(candidate.phase())?;
        let p=output::evaluate(0.5,[v[0],v[1],0.,bus_v]).map_err(|_|InvalidInput)?;
        *self=candidate;Ok(p)
    }
}
