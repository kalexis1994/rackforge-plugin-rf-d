//! Explicit BUS/C10 charge coordinates, conditional SVC-9 pp.19/13/10 chain.
//! Reference stamp; fixed boundary/source controls. See CADENA_CARGA_RADAU_PROTOCOLO.
use rf_d_circuit::{mixer_on::OnMixer, output_conversion::Parameters as Conversion,
    Parameters as Headphone, StepError, vco1_increment::two_sum};
#[path="prepared_audio_stamp.rs"] mod circuit66;
pub const N: usize=68;
pub const BUS: usize=66;
pub const C10_LEFT: usize=67;
pub const MIN_DT_S: f64=4.*rf_d_circuit::vco1_engine::TICK_S;
const GROUND: usize=N;
/// Sixteen audio incidences; shared C18 belongs to the contour; fixed terminal derivatives are zero.
pub const CAPACITORS:[(usize,usize,f64);16]=[
 (8,12,68e-9),(9,13,68e-9),(10,14,68e-9),(11,15,68e-9),
 (4,GROUND,220e-6),(6,BUS,10e-6),(16,11,0.22e-6),(17,15,0.22e-6),
 (23,GROUND,100e-6),(24,25,0.33e-6),(26,GROUND,220e-6),
 (40,GROUND,220e-6),(46,47,10e-6),(49,50,2.5e-6),
 (57,58,220e-12),(60,61,400e-6)];
#[derive(Clone,Copy)]
pub struct Parameters {
 audio:circuit66::Prepared,
 pub circuit:circuit66::Parameters,pub conversion:Conversion,pub headphone:Headphone,
 pub boundary:circuit66::Boundary,pub mixer:OnMixer,
}
impl Parameters{
 pub fn new(p:rf_d_circuit::chain_charge::Parameters)->Result<Self,StepError>{
  Ok(Self{audio:circuit66::Prepared::new(p.circuit,p.conversion,p.headphone,p.boundary)?,circuit:p.circuit,conversion:p.conversion,headphone:p.headphone,boundary:p.boundary,mixer:p.mixer})
 }
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct State {pub high:[f64;N],pub low:[f64;N]}
fn add_pair(h:f64,l:f64,d:f64)->(f64,f64) {
 let(s,e)=two_sum(h,d);let(t,f)=two_sum(l,e);let(u,v)=two_sum(s,t);two_sum(u,v+f)
}
impl State {
 pub fn from_nodes(high:[f64;N])->Self {Self{high,low:[0.;N]}}
 pub fn advanced(self,delta:[f64;N])->Self {let mut q=self;for k in 0..N {(q.high[k],q.low[k])=add_pair(self.high[k],self.low[k],delta[k]);}q}
 pub fn difference(self,other:Self)->[f64;N] {std::array::from_fn(|k|{let(h,l)=add_pair(self.high[k],self.low[k],-other.high[k]);let(h,l)=add_pair(h,l,-other.low[k]);h+l})}
 fn valid(self)->bool {(0..N).all(|k| {let(h,l)=(self.high[k],self.low[k]);h.is_finite()&&l.is_finite()&&h.abs()<=40.&&(h.abs()!=40.||h*l<=0.)&&two_sum(h,l)==(h,l)})}
}
pub struct Parts {
 pub dc:[f64;N],pub dc_jacobian:[[f64;N];N],
 pub charge_over_h:[f64;N],pub mass_over_h:[[f64;N];N],
 pub source_gradient_s:[[f64;5];N],pub candidate:State,
}
pub fn constraint_row(p:Parameters,row:usize)->bool {
 let lower=p.boundary.recovery.vca.second.output.output.r21_lower_ohm;
 row==49&&(lower==0.||lower==5000.) || row==C10_LEFT&&
  (p.boundary.r14_ohm.is_none()||p.boundary.r14_ohm==Some(p.circuit.r30_ohm-1330.))
}
fn value(a:&[f64;N],k:usize)->f64 {if k==GROUND {0.} else {a[k]}}
#[inline(always)]
pub fn linearize_prevalidated<const FULL:bool>(p:Parameters,sources:[f64;5],old:State,delta:State,h:f64,now:State)->Result<Parts,StepError> {
 // State/LOW canonicality belongs to the checked full-graph boundary.
 if !h.is_finite()||!(MIN_DT_S..=1e-3).contains(&h){return Err(StepError::InvalidInput);}
 let x:[f64;66]=std::array::from_fn(|k|now.high[k]);
 let low=std::array::from_fn(|k|now.low[k]);let(r,j)=p.audio.linearize::<FULL>(&x,&low)?;
 let port=p.mixer.evaluate([sources[0],sources[1],sources[2],sources[3],sources[4],now.high[BUS]]).map_err(|_|StepError::InvalidInput)?;
 let mut dc=[0.;N];dc[..66].copy_from_slice(&r);dc[BUS]=port.current_a[5];
 let mut jac=[[0.;N];N];if FULL{for a in 0..66 {jac[a][..66].copy_from_slice(&j[a]);}}
 let y=p.mixer.admittance_s();jac[BUS][BUS]=y[5][5];dc[BUS]+=y[5][5]*now.low[BUS];
 let mut source_gradient_s=[[0.;5];N];source_gradient_s[BUS].copy_from_slice(&y[5][..5]);
 let series=p.boundary.r14_ohm.map(|r14|r14+(1330.-p.circuit.r30_ohm));
 match series {
  Some(r) if r>0.=>{let g=1./r;let i=g*(now.high[22]-now.high[C10_LEFT])+g*(now.low[22]-now.low[C10_LEFT]);
   dc[22]+=i;dc[C10_LEFT]-=i;jac[22][22]+=g;jac[22][C10_LEFT]-=g;
   jac[C10_LEFT][22]-=g;jac[C10_LEFT][C10_LEFT]+=g;},
  Some(0.)=>{dc[C10_LEFT]=now.high[C10_LEFT]-now.high[22]+(now.low[C10_LEFT]-now.low[22]);jac[C10_LEFT][C10_LEFT]=1.;jac[C10_LEFT][22]=-1.;},
  None=>{dc[C10_LEFT]=now.high[C10_LEFT]-now.high[7]+(now.low[C10_LEFT]-now.low[7]);jac[C10_LEFT][C10_LEFT]=1.;jac[C10_LEFT][7]=-1.;},
  _=>return Err(StepError::InvalidInput),
 }
 // Every DC incidence already includes its analytic LOW direction.

 let lower=p.boundary.recovery.vca.second.output.output.r21_lower_ohm;
 let row=|k|if k==49 {if lower==0. {GROUND} else if lower==5000. {48} else {k}} else {k};
 let mut q=[0.;N];let mut mass=[[0.;N];N];
 let mut capacitor=|a:usize,b:usize,c:f64| {
  let g=c/h;let(hh,ll)=add_pair(value(&delta.high,a),value(&delta.low,a),-value(&delta.high,b));
  let(hh,ll)=add_pair(hh,ll,-value(&delta.low,b));let i=g*(hh+ll);
  for (r,sign) in [(row(a),1.),(row(b),-1.)] {if r!=GROUND {
   q[r]+=sign*i;if FULL{for (col,slope) in [(a,g),(b,-g)] {if col!=GROUND {mass[r][col]+=sign*slope;}}}
  }}
 };
 for(a,b,c) in CAPACITORS {capacitor(a,b,c);}
 match series {Some(0.)=>capacitor(22,7,10e-6),Some(_)=>capacitor(C10_LEFT,7,10e-6),None=>()}
 if dc.iter().chain(q.iter()).any(|v|!v.is_finite()) {return Err(StepError::ExponentialDomain);}
 Ok(Parts{dc,dc_jacobian:jac,charge_over_h:q,mass_over_h:mass,source_gradient_s,candidate:now})
}
/// Source current is resistive; all dynamic BUS loading is already in its solved voltage.
pub fn source_currents(p:Parameters,sources:[f64;5],state:State)->Result<[f64;5],StepError> {
 if !state.valid() {return Err(StepError::InvalidInput);}
 let r=p.mixer.evaluate([sources[0],sources[1],sources[2],sources[3],sources[4],state.high[BUS]]).map_err(|_|StepError::InvalidInput)?;
 let y=p.mixer.admittance_s();Ok(std::array::from_fn(|i|r.current_a[i]+y[i][5]*state.low[BUS]))
}
