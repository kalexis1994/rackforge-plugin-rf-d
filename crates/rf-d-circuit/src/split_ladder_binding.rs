//! Bind the unmodified parent charges and the final local ladder stamp once.
use super::{full,ladder,parent,LOCAL,Z,N};
use crate::StepError;
pub fn parent_parts<const FULL:bool>(mut p:parent::Parameters,time:f64,old:full::State,delta:full::State,c:full::Controls,h:f64,t:f64)->Result<full::Parts,StepError>{
    p.time=time;
    let mut s=parent::parts::<FULL>(p,old,delta,c,h,t)?;
    let port=full::phase::observe(t,s.now.high[116]).map_err(|_|StepError::InvalidInput)?;
    let y=port.admittance_s[3][3];
    s.dc[116]+=port.current_a[3]+y*s.now.low[116];if FULL{s.j[116][116]+=y;}
    Ok(s)
}
/// Parent DC must not introduce a source or edge at an eliminated interior.
/// Inspect actual coefficients instead of silently dropping an unexpected link.
pub fn validate_parent<const FULL:bool>(p:&full::Parts)->Result<(),StepError>{
    for k in Z.into_iter().chain([67,68,69]){
        if p.dc[k]!=0.||!p.dc[k].is_finite(){return Err(StepError::InvalidInput);}
        if FULL{for a in 0..N{if p.j[a][k]!=0.||p.j[k][a]!=0.{return Err(StepError::InvalidInput);}}}
    }Ok(())
}
/// Reconcile only the DD rounding of the same reconstructed state. The linear
/// LOW correction preserves the already admitted first-order LOW junction law.
/// An offset beyond 128*epsilon^2*max(1,|V|) rejects; it is not a reusable cache.
pub fn merge<const FULL:bool>(p:&mut full::Parts,local:&ladder::Solution)->Result<f64,StepError>{
    if !p.now.valid()||!local.nodes.valid(){return Err(StepError::InvalidInput);}
    let mut offset=[0.;16];let mut largest=0_f64;
    for k in 0..16{
        let a=LOCAL[k];let(h,l)=ladder::add_pair(p.now.high[a],p.now.low[a],-local.nodes.high[k]);
        let(h,l)=ladder::add_pair(h,l,-local.nodes.low[k]);let v=h+l;
        let bound=128.*f64::EPSILON*f64::EPSILON*local.nodes.high[k].abs().max(1.);
        if !v.is_finite()||v.abs()>bound{return Err(StepError::InvalidInput);}
        offset[k]=v;largest=largest.max(v.abs());
    }
    if local.dc.iter().chain(local.physical_j.iter().flatten()).chain(p.dc.iter()).chain(p.j.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
    let mut dc=[0.;16];let mut j=[[0.;16];16];
    for a in 0..16{
        let correction=(0..16).map(|b|local.physical_j[a][b]*offset[b]).sum::<f64>();
        dc[a]=p.dc[LOCAL[a]]+local.dc[a]+correction;
        if FULL{for b in 0..16{j[a][b]=p.j[LOCAL[a]][LOCAL[b]]+local.physical_j[a][b];}}
    }
    if dc.iter().chain(j.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
    for a in 0..16{p.dc[LOCAL[a]]=dc[a];if FULL{for b in 0..16{p.j[LOCAL[a]][LOCAL[b]]=j[a][b];}}}Ok(largest)
}
