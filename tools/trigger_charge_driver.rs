//! SVC-9 Fig9-7/p9: Q12/Q20, CR8/CR10 and common trigger resistors.
use rf_d_circuit::StepError;
pub const N:usize=8;
#[derive(Clone,Copy)]pub struct Controls{pub keyboard:f64,pub reset_base:f64,pub short:bool}
pub struct Stamp{pub dc:[f64;N],pub jacobian:[[f64;N];N],pub ports:[f64;4]}
fn voltage(x:&[f64;N],c:Controls,k:usize)->f64{if k<N{x[k]}else{[0.,9.3,c.keyboard,c.reset_base][k-N]}}
fn row(s:&mut Stamp,k:usize,i:f64,d:&[(usize,f64)]){if k<N{s.dc[k]+=i;for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}}}else{s.ports[k-N]+=i;}}
fn resistor(s:&mut Stamp,x:&[f64;N],c:Controls,a:usize,b:usize,r:f64){let i=(voltage(x,c,a)-voltage(x,c,b))/r;row(s,a,i,&[(a,1./r),(b,-1./r)]);row(s,b,-i,&[(a,-1./r),(b,1./r)]);}
fn bjt(s:&mut Stamp,x:&[f64;N],c:Controls,b:usize,col:usize)->Result<(),StepError>{
 let vt=1.380649e-23*298.15/1.602176634e-19;let be=voltage(x,c,b)/vt;let bc=(voltage(x,c,b)-voltage(x,c,col))/vt;if be>45.||bc>45.{return Err(StepError::ExponentialDomain);}
 let f=1e-14*be.exp_m1();let r=1e-14*bc.exp_m1();let gf=1e-14*be.exp()/vt;let gr=1e-14*bc.exp()/vt;let ib=f/100.+r/5.;let ic=f-1.2*r;
 row(s,b,ib,&[(b,gf/100.+gr/5.),(col,-gr/5.)]);row(s,col,ic,&[(b,gf-1.2*gr),(col,1.2*gr)]);row(s,8,-ib-ic,&[]);Ok(())
}
fn diode(s:&mut Stamp,x:&[f64;N],c:Controls,a:usize,b:usize)->Result<(),StepError>{let vt=1.5*1.380649e-23*298.15/1.602176634e-19;let v=(voltage(x,c,a)-voltage(x,c,b))/vt;if v>45.{return Err(StepError::ExponentialDomain);}let i=1e-8*v.exp_m1();let g=1e-8*v.exp()/vt;row(s,a,i,&[(a,g),(b,-g)]);row(s,b,-i,&[(a,-g),(b,g)]);Ok(())}
pub fn linearize(x:[f64;N],c:Controls)->Result<Stamp,StepError>{
 if x.iter().any(|v|!v.is_finite())||!c.keyboard.is_finite()||!c.reset_base.is_finite(){return Err(StepError::InvalidInput);}
 let mut s=Stamp{dc:[0.;N],jacobian:[[0.;N];N],ports:[0.;4]};for(a,b,r)in[(0,9,3300.),(1,9,3300.),(1,2,10000.),(3,4,47000.),(4,5,100000.),(0,6,10000.),(1,7,10000.)]{resistor(&mut s,&x,c,a,b,r);}if c.short{resistor(&mut s,&x,c,1,8,220.);}
 bjt(&mut s,&x,c,2,0)?;bjt(&mut s,&x,c,3,1)?;diode(&mut s,&x,c,10,5)?;diode(&mut s,&x,c,7,11)?;Ok(s)
}
