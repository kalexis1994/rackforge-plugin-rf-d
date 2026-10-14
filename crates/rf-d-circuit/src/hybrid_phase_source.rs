//! Nominal continuous-time circuit cycle for the hybrid laboratory solver.
//! Same frequency/epoch as the admitted phase VCO; retains the reset edge.
#[path="hybrid_phase_profile.rs"] pub mod profile;
#[path="vco_phase_profile.rs"] mod clock;
#[path="vco_output_port.rs"] pub mod output;
pub fn observe(time_s:f64,bus_v:f64)->Result<output::Port,crate::StepError>{
    if !time_s.is_finite()||!(0. ..=1000.).contains(&time_s)||!bus_v.is_finite()||bus_v.abs()>2. {return Err(crate::StepError::InvalidInput);}
    let phase=((time_s-clock::EPOCH_S)*clock::FREQUENCY_HZ).rem_euclid(1.);
    let a=&profile::KNOTS;let mut lo=0;let mut hi=a.len()-1;
    while hi-lo>1{let mid=(lo+hi)/2;if a[mid][0]<=phase{lo=mid;}else{hi=mid;}}
    let q=(phase-a[lo][0])/(a[hi][0]-a[lo][0]);
    let v=std::array::from_fn::<_,2,_>(|k|a[lo][k+1]+q*(a[hi][k+1]-a[lo][k+1]));
    output::evaluate(0.5,[v[0],v[1],0.,bus_v]).map_err(|_|crate::StepError::InvalidInput)
}
