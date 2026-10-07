//! Nominal TI LM741 full MNA stamp; see VCO_741_NATIVO_PROTOCOLO.md.
//! External nodes [+, -, V+, V-, output]; node 49 and all ideal branches retained.
pub const NV: usize = 26;
pub const N: usize = 37;
pub const NODES: [u16; NV] = [1,2,99,50,28,3,4,5,6,7,8,9,10,98,49,15,16,17,23,24,26,22,25,27,21,20];
pub const SOURCES: [&str;9] = ["EOS","V2","V3","EH","E1","V6","V7","V5","V4"];
pub const VT: f64 = (1.38064852e-23 / 1.6021766208e-19) * 298.15;
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Memory { pub capacitor_v: [f64;3], pub inductor_i_a: [f64;2] }
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Mode { Dc, Euler {dt_s:f64, previous:Memory} }
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Error { InvalidInput, JunctionDomain, NonFinite }
#[derive(Debug)]
pub struct Stamp { pub residual:[f64;N], pub jacobian:[[f64;N];N], pub candidate:Memory, pub ground_current_a:f64 }
fn ix(node:u16)->usize { NODES.iter().position(|n|*n==node).unwrap() }
impl Stamp {
 fn branch(&mut self,a:usize,b:usize,i:f64,gradient:&[(usize,f64)]) {
  self.residual[a]+=i; self.residual[b]-=i;
  for &(c,g) in gradient {self.jacobian[a][c]+=g;self.jacobian[b][c]-=g;}
 }
 fn resistor(&mut self,x:&[f64;N],a:u16,b:u16,r:f64) {let (a,b)=(ix(a),ix(b));let g=1./r;self.branch(a,b,(x[a]-x[b])*g,&[(a,g),(b,-g)]);}
 fn controlled(&mut self,x:&[f64;N],a:u16,b:u16,c:u16,d:u16,g:f64) {let (c,d)=(ix(c),ix(d));self.branch(ix(a),ix(b),g*(x[c]-x[d]),&[(c,g),(d,-g)]);}
 fn voltage(&mut self,x:&[f64;N],k:usize,a:u16,b:u16,offset:f64,control:Option<(u16,u16)>) {
  let (a,b)=(ix(a),ix(b));let row=NV+k;self.branch(a,b,x[row],&[(row,1.)]);
  self.residual[row]=x[a]-x[b]-offset;self.jacobian[row][a]+=1.;self.jacobian[row][b]-=1.;
  if let Some((c,d))=control {let (c,d)=(ix(c),ix(d));self.residual[row]-=x[c]-x[d];self.jacobian[row][c]-=1.;self.jacobian[row][d]+=1.;}
 }
}
fn junction(v:f64,is_a:f64)->Result<(f64,f64),Error> {
 if !(-40. ..=0.9).contains(&v) {return Err(Error::JunctionDomain);}
 if v>=-3.*VT {let z=v/VT;Ok((is_a*z.exp_m1(),is_a*z.exp()/VT))}
 else {let a=(3.*VT/(std::f64::consts::E*v)).powi(3);Ok((-is_a*(1.+a),is_a*3.*a/v))}
}
pub fn memory(x:&[f64;N])->Memory {Memory {capacitor_v:[x[ix(5)]-x[ix(6)],x[ix(98)]-x[ix(9)],x[ix(98)]-x[ix(15)]],inductor_i_a:[x[35],x[36]]}}
pub fn linearize(x:[f64;N],mode:Mode)->Result<Stamp,Error> {
 if x[..NV].iter().any(|v|!v.is_finite()||v.abs()>40.) || x[NV..].iter().any(|v|!v.is_finite()||v.abs()>1.) {return Err(Error::InvalidInput);}
 if let Mode::Euler{dt_s,previous}=mode {
  if !dt_s.is_finite()||!(125e-9..=1e-3).contains(&dt_s)||previous.capacitor_v.iter().any(|v|!v.is_finite()||v.abs()>80.)||previous.inductor_i_a.iter().any(|v|!v.is_finite()||v.abs()>1.) {return Err(Error::InvalidInput);}
 }
 let mut s=Stamp{residual:[0.;N],jacobian:[[0.;N];N],candidate:memory(&x),ground_current_a:0.};
 for (a,b,r) in [(1,3,250e3),(3,2,250e3),(5,99,517.),(6,99,517.),(99,49,40e3),(49,50,40e3),(98,9,95.493e6),(98,15,1e6),(17,16,1e3),(24,23,25.),(23,25,25.),(22,28,100e3)] {s.resistor(&x,a,b,r);}
 for (a,b,i) in [(2,1,20e-9),(4,50,100e-6),(99,50,1.6e-3)] {s.branch(ix(a),ix(b),i,&[]);}
 for (c,b,e) in [(5,2,4),(6,7,4)] {
  let (c,b,e)=(ix(c),ix(b),ix(e));let be=x[b]-x[e];let bc=x[b]-x[c];
  let (ibe,gbe)=junction(be,1e-16)?;let (ibc,gbc)=junction(bc,1e-16)?;
  s.branch(c,e,ibe-ibc,&[(b,gbe-gbc),(e,-gbe),(c,gbc)]);
  s.branch(b,e,ibe/625.+1e-12*be,&[(b,gbe/625.+1e-12),(e,-gbe/625.-1e-12)]);
  s.branch(b,c,ibc+1e-12*bc,&[(b,gbc+1e-12),(c,-gbc-1e-12)]);
  s.residual[c]+=1e-12*x[c];s.jacobian[c][c]+=1e-12;s.ground_current_a-=1e-12*x[c];
 }
 for (a,b) in [(9,8),(10,9),(26,24),(25,27),(21,15),(15,20)] {
  let (a,b)=(ix(a),ix(b));let v=x[a]-x[b];let (i,g)=junction(v,1e-15)?;s.branch(a,b,i+1e-12*v,&[(a,g+1e-12),(b,-g-1e-12)]);
 }
 for (a,b,c,d,g) in [(98,9,5,6,0.0021),(98,15,9,49,1e-6),(98,16,3,49,3.1623e-8)] {s.controlled(&x,a,b,c,d,g);}
 s.branch(ix(50),ix(99),450e-6+x[NV+5],&[(NV+5,1.)]);
 for (k,a,b,o,control) in [(0,7,1,0.001,Some((16,49))),(1,99,8,1.63,None),(2,10,50,1.63,None),(3,99,98,0.,Some((99,49))),(4,99,23,0.,Some((99,15))),(5,26,22,0.65,None),(6,22,27,0.65,None),(7,22,21,0.18,None),(8,20,22,0.18,None)] {s.voltage(&x,k,a,b,o,control);}
 if let Mode::Euler{dt_s,previous}=mode {
  for (k,a,b,c) in [(0,5,6,60.3614e-12),(1,98,9,333.33e-12),(2,98,15,5.3052e-15)] {
   let (a,b)=(ix(a),ix(b));let g=c/dt_s;s.branch(a,b,g*((x[a]-x[b])-previous.capacitor_v[k]),&[(a,g),(b,-g)]);
  }
 }
 for (k,a,b,l) in [(0,98,17,0.5305),(1,22,28,100e-12)] {
  let (a,b)=(ix(a),ix(b));let row=35+k;s.branch(a,b,x[row],&[(row,1.)]);s.residual[row]=x[a]-x[b];s.jacobian[row][a]=1.;s.jacobian[row][b]=-1.;
  if let Mode::Euler{dt_s,previous}=mode {let z=l/dt_s;s.residual[row]-=z*(x[row]-previous.inductor_i_a[k]);s.jacobian[row][row]=-z;}
 }
 if s.residual.iter().chain(s.jacobian.iter().flatten()).any(|v|!v.is_finite()) {return Err(Error::NonFinite);}
 Ok(s)
}
