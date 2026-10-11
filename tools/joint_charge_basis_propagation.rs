//! Multiple RHS laboratory adapter; same elimination as the admitted scalar.
use rf_d_circuit::{joint_voice as j,StepError};
use crate::joint_history_tangent::{old_mass};
pub const R:usize=18;
pub type Sensitivity=[[f64;R];j::M];
pub fn propagate(p:j::Parameters,x:j::State,d:[j::State;2],h:f64,u:[[f64;R];j::N])->Result<Sensitivity,StepError> {
 let m=old_mass(p,x,h)?;let a=j::linearize(p,x,d,h)?;
 let rhs=std::array::from_fn(|k|std::array::from_fn(|r| {
  let mut v=0.;for b in 0..j::N {v+=m[k%j::N][b]*u[b][r];}
  (j::B[k/j::N][0]+j::B[k/j::N][1])*v
 }));solve(a.jacobian,rhs)
}
fn solve<const M:usize>(mut a:[[f64;M];M],mut rhs:[[f64;R];M])->Result<[[f64;R];M],StepError> {
 let mut scale=[0.;M];
 for i in 0..M {scale[i]=a[i].iter().fold(0_f64,|v,x|v.max(x.abs()));if scale[i]==0. {return Err(StepError::SingularJacobian);}}
 for col in 0..M {
  let mut pivot=col;let mut best=0.;
  for row in col..M {if a[row][col]==0. {continue;}let score=a[row][col].abs()/scale[row];if score>best {best=score;pivot=row;}}
  if best<1e-12 {return Err(StepError::SingularJacobian);}
  a.swap(col,pivot);rhs.swap(col,pivot);scale.swap(col,pivot);let diagonal=a[col][col];
  for row in col+1..M {
   if a[row][col]==0. {continue;}let factor=a[row][col]/diagonal;a[row][col]=0.;
   for k in col+1..M {a[row][k]-=factor*a[col][k];}
   for r in 0..R {rhs[row][r]-=factor*rhs[col][r];}
  }
 }
 let mut out=[[0.;R];M];
 for row in (0..M).rev() {for r in 0..R {let mut value=rhs[row][r];for k in row+1..M {value-=a[row][k]*out[k][r];}out[row][r]=value/a[row][row];}}
 if out.iter().flatten().any(|v|!v.is_finite()) {return Err(StepError::SingularJacobian);}Ok(out)
}
