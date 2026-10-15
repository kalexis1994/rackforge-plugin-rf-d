//! Offline voltage conversion, with explicit left DC and real right support.
#[path="j7_antialias_coefficients.rs"]pub mod coefficients;
use crate::StepError;
pub fn kernel(factor:usize)->Result<&'static[f64],StepError>{
    match factor{4=>Ok(&coefficients::H192000),8=>Ok(&coefficients::H384000),_=>Err(StepError::InvalidInput)}
}
/// Centred FIR followed by decimation. Units remain volts. No peak scaling.
/// All input/capacity checks precede writes; output includes an anchor if requested.
pub fn convert(input:&[f64],output:&mut[f64],factor:usize)->Result<(),StepError>{
    let h=kernel(factor)?;let middle=h.len()/2;
    let last=output.len().checked_sub(1).and_then(|n|n.checked_mul(factor))
        .and_then(|n|n.checked_add(middle)).ok_or(StepError::InvalidInput)?;
    if last>=input.len()||input.iter().any(|v|!v.is_finite()||v.abs()>=40.){return Err(StepError::InvalidInput);}
    for (n,out) in output.iter_mut().enumerate(){
        let centre=n*factor;let mut sum=0.;
        for (j,c) in h.iter().enumerate(){let a=centre+j;let x=if a<middle{input[0]}else{input[a-middle]};sum+=c*x;}
        *out=sum;
    }
    Ok(())
}
#[cfg(test)]mod tests{
    use super::*;
    #[test]fn rejects_without_partial_output_and_recovers(){
        let mut out=[7.;49];let x=[0.25;577];
        for factor in[0,1,3,5,9]{assert!(convert(&x,&mut out,factor).is_err());assert_eq!(out,[7.;49]);}
        assert!(convert(&x[..384],&mut out,4).is_err());assert_eq!(out,[7.;49]);
        for bad in[f64::NAN,f64::INFINITY,40.]{let mut broken=x;broken[570]=bad;assert!(convert(&broken,&mut out,4).is_err());assert_eq!(out,[7.;49]);}
        assert!(convert(&x,&mut[],4).is_err());convert(&x,&mut out,4).unwrap();let saved=out;
        assert!(out.iter().all(|v|(*v-0.25).abs()<1e-14));convert(&x,&mut out,4).unwrap();assert_eq!(out,saved);
    }
    #[test]fn centred_impulse_has_declared_support_and_phase(){
        for factor in[4,8]{let h=kernel(factor).unwrap();let middle=h.len()/2;let mut x=[0.;1537];x[768]=1.;let mut out=[0.;145];convert(&x,&mut out,factor).unwrap();
            for (n,v) in out.iter().enumerate(){let j=768isize+middle as isize-(n*factor)as isize;let expected=if(0..h.len()as isize).contains(&j){h[j as usize]}else{0.};assert_eq!(v.to_bits(),expected.to_bits());}
        }
    }
}
