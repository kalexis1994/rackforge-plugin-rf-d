//! Board2 Q16/Q17/Q18/Q19 and C2 external branches, SVC-9 Fig9-7/p9.
//! Fixed source terminals: ground,9.3,-10,+10,Q25 collector,reset driver.
use rf_d_circuit::StepError;
pub const N:usize=12;
#[derive(Clone,Copy)] pub struct Controls {pub q25:f64,pub reset_driver:f64,pub final_decay:bool}
pub struct Stamp {pub dc:[f64;N],pub jacobian:[[f64;N];N],pub ports:[f64;6],pub port_jacobian:[[f64;N];6]}
fn voltage(x:&[f64;N],c:Controls,k:usize)->f64 {if k<N {x[k]} else {[0.,9.3,-10.,10.,c.q25,c.reset_driver][k-N]}}
fn row(s:&mut Stamp,k:usize,i:f64,derivatives:&[(usize,f64)]) {
 if k<N {s.dc[k]+=i;for &(j,g) in derivatives {if j<N {s.jacobian[k][j]+=g;}}}
 else {s.ports[k-N]+=i;for &(j,g) in derivatives {if j<N {s.port_jacobian[k-N][j]+=g;}}}
}
fn resistor(s:&mut Stamp,x:&[f64;N],c:Controls,a:usize,b:usize,r:f64) {let i=(voltage(x,c,a)-voltage(x,c,b))/r;row(s,a,i,&[(a,1./r),(b,-1./r)]);row(s,b,-i,&[(a,-1./r),(b,1./r)]);}
fn bjt(s:&mut Stamp,x:&[f64;N],c:Controls,sign:f64,b:usize,col:usize,e:usize)->Result<(),StepError> {
 let vt=1.380649e-23*298.15/1.602176634e-19;let be=sign*(voltage(x,c,b)-voltage(x,c,e))/vt;let bc=sign*(voltage(x,c,b)-voltage(x,c,col))/vt;
 if be>45.||bc>45. {return Err(StepError::ExponentialDomain);}
 let f=1e-14*be.exp_m1();let rev=1e-14*bc.exp_m1();let gf=1e-14*be.exp()/vt;let gr=1e-14*bc.exp()/vt;let ib=f/100.+rev/5.;let ic=f-rev*1.2;
 row(s,b,sign*ib,&[(b,gf/100.+gr/5.),(e,-gf/100.),(col,-gr/5.)]);row(s,col,sign*ic,&[(b,gf-1.2*gr),(e,-gf),(col,1.2*gr)]);row(s,e,-sign*(ib+ic),&[(b,-gf-gf/100.+gr),(e,gf+gf/100.),(col,-gr)]);Ok(())
}
fn diode(s:&mut Stamp,x:&[f64;N],c:Controls,a:usize,b:usize)->Result<(),StepError> {
 let scale=1.5*1.380649e-23*298.15/1.602176634e-19;let exponent=(voltage(x,c,a)-voltage(x,c,b))/scale;if exponent>45. {return Err(StepError::ExponentialDomain);}
 let i=1e-12*exponent.exp_m1();let g=1e-12*exponent.exp()/scale;row(s,a,i,&[(a,g),(b,-g)]);row(s,b,-i,&[(a,-g),(b,g)]);Ok(())
}
pub fn linearize(x:[f64;N],c:Controls)->Result<Stamp,StepError> {
 if x.iter().any(|v|!v.is_finite())||!c.q25.is_finite()||!c.reset_driver.is_finite() {return Err(StepError::InvalidInput);}
 let mut s=Stamp{dc:[0.;N],jacobian:[[0.;N];N],ports:[0.;6],port_jacobian:[[0.;N];6]};
 for(a,b,r) in [(1,13,560.),(1,16,3300.),(2,3,100.),(3,0,10000.),(6,0,100000.),(4,14,10000.),(4,5,4700.),(9,13,27000.),(7,12,2500.),(7,15,2500.),(7,8,4700.),(8,12,4700.),(10,12,100.),(11,17,1500.)] {resistor(&mut s,&x,c,a,b,r);}
 bjt(&mut s,&x,c,-1.,1,2,13)?;bjt(&mut s,&x,c,1.,16,13,4)?;bjt(&mut s,&x,c,1.,5,6,9)?;bjt(&mut s,&x,c,-1.,8,10,9)?;
 diode(&mut s,&x,c,9,17)?;if !c.final_decay {diode(&mut s,&x,c,0,11)?;}
 if s.dc.iter().chain(s.jacobian.iter().flatten()).chain(s.ports.iter()).any(|v|!v.is_finite()) {return Err(StepError::ExponentialDomain);}Ok(s)
}
