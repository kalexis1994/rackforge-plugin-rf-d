//! Full reviewed board2 graph; last unknown is the loaded VCA base port.
use rf_d_circuit::StepError;
pub const N:usize=30;
pub struct Stamp{pub dc:[f64;N],pub jacobian:[[f64;N];N],pub ports:[f64;5]}
fn v(x:&[f64;N],key:f64,k:usize)->f64{if k<N{x[k]}else{[0.,9.3,-10.,10.,key][k-N]}}
fn row(s:&mut Stamp,k:usize,i:f64,d:&[(usize,f64)]){if k<N{s.dc[k]+=i;for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}}}else{s.ports[k-N]+=i;}}
fn r(s:&mut Stamp,x:&[f64;N],key:f64,a:usize,b:usize,ohm:f64){let g=1./ohm;let i=(v(x,key,a)-v(x,key,b))*g;row(s,a,i,&[(a,g),(b,-g)]);row(s,b,-i,&[(a,-g),(b,g)]);}
fn diode(s:&mut Stamp,x:&[f64;N],key:f64,a:usize,b:usize,is:f64)->Result<(),StepError>{let vt=1.5*super::latch_charge_driver::VT;let z=(v(x,key,a)-v(x,key,b))/vt;if z>45.{return Err(StepError::ExponentialDomain);}let i=is*z.exp_m1();let g=is*z.exp()/vt;row(s,a,i,&[(a,g),(b,-g)]);row(s,b,-i,&[(a,-g),(b,g)]);Ok(())}
fn bjt(s:&mut Stamp,x:&[f64;N],key:f64,sign:f64,b:usize,c:usize,e:usize)->Result<(),StepError>{let vt=super::latch_charge_driver::VT;let be=sign*(v(x,key,b)-v(x,key,e))/vt;let bc=sign*(v(x,key,b)-v(x,key,c))/vt;if be>45.||bc>45.{return Err(StepError::ExponentialDomain);}let f=1e-14*be.exp_m1();let rr=1e-14*bc.exp_m1();let gf=1e-14*be.exp()/vt;let gr=1e-14*bc.exp()/vt;let ib=f/100.+rr/5.;let ic=f-1.2*rr;row(s,b,sign*ib,&[(b,gf/100.+gr/5.),(e,-gf/100.),(c,-gr/5.)]);row(s,c,sign*ic,&[(b,gf-1.2*gr),(e,-gf),(c,1.2*gr)]);row(s,e,-sign*(ib+ic),&[(b,-gf-gf/100.+gr),(e,gf+gf/100.),(c,-gr)]);Ok(())}
pub fn linearize(x:[f64;N],key:f64,on:bool,short:bool)->Result<Stamp,StepError>{
 if x.iter().any(|v|!v.is_finite())||!key.is_finite()||!(0. ..=10.).contains(&key){return Err(StepError::InvalidInput);}
 let mut s=Stamp{dc:[0.;N],jacobian:[[0.;N];N],ports:[0.;5]};
 r(&mut s,&x,key,31,18,3300.0); // R23
 r(&mut s,&x,key,31,17,3300.0); // R25_DRAWING
 r(&mut s,&x,key,18,19,10000.0); // R_TRIGGER_BASE_DRAWING
 if short{r(&mut s,&x,key,30,18,220.0);} // R49
 r(&mut s,&x,key,20,21,47000.0); // R55
 r(&mut s,&x,key,21,22,100000.0); // R60
 r(&mut s,&x,key,17,23,10000.0); // R28
 r(&mut s,&x,key,18,24,10000.0); // R36
 r(&mut s,&x,key,25,28,10000.0); // R38
 r(&mut s,&x,key,31,28,10000.0); // R39
 r(&mut s,&x,key,6,26,3300.0); // R40
 r(&mut s,&x,key,31,6,560.0); // R41
 r(&mut s,&x,key,7,8,100.0); // R42
 r(&mut s,&x,key,8,5,10000.0); // PANEL_R13
 r(&mut s,&x,key,11,5,100000.0); // PANEL_R16
 r(&mut s,&x,key,26,27,33000.0); // R56
 r(&mut s,&x,key,9,32,10000.0); // R43
 r(&mut s,&x,key,9,10,4700.0); // R44
 r(&mut s,&x,key,31,14,27000.0); // R45
 r(&mut s,&x,key,12,13,4700.0); // R51
 r(&mut s,&x,key,13,30,4700.0); // R47_POSITION
 r(&mut s,&x,key,15,30,100.0); // R46
 r(&mut s,&x,key,12,30,2500.0); // PANEL_R19_LOWER
 r(&mut s,&x,key,33,12,2500.0); // PANEL_R19_UPPER
 r(&mut s,&x,key,5,0,10000.0); // R16
 r(&mut s,&x,key,31,2,560.0); // R15
 r(&mut s,&x,key,4,32,16900.0); // R27
 r(&mut s,&x,key,4,3,6800.0); // R24
 r(&mut s,&x,key,16,17,1500.0); // LHC_FAST_DECAY
 r(&mut s,&x,key,3,29,68000.0); // R59
 bjt(&mut s,&x,key,1.0,25,26,30)?; // Q25
 bjt(&mut s,&x,key,1.0,27,28,30)?; // Q15
 bjt(&mut s,&x,key,-1.0,6,7,31)?; // Q16
 bjt(&mut s,&x,key,1.0,26,31,9)?; // Q17
 bjt(&mut s,&x,key,1.0,10,11,14)?; // Q18
 bjt(&mut s,&x,key,-1.0,13,15,14)?; // Q19
 bjt(&mut s,&x,key,1.0,0,2,1)?; // Q3
 bjt(&mut s,&x,key,1.0,1,2,3)?; // Q2
 bjt(&mut s,&x,key,1.0,19,17,30)?; // Q12
 bjt(&mut s,&x,key,1.0,20,18,30)?; // Q20
 diode(&mut s,&x,key,4,27,1e-08)?; // CR6
 diode(&mut s,&x,key,24,27,1e-08)?; // CR8
 diode(&mut s,&x,key,34,22,1e-08)?; // CR10
 diode(&mut s,&x,key,14,17,1e-12)?; // CR9
 if !on{diode(&mut s,&x,key,5,16,1e-12)?;} // CR4
 Ok(s)
}
