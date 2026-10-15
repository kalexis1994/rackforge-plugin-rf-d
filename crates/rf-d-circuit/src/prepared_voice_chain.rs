//! Generated chain binding: OSC1 belongs to VCO; BUS is shared.
//! Laboratory simultaneous dual contour -> ladder/recovery/two VCAs/J7.
//! Fixed nominal scene and source boundary: CONTORNOS_CADENA_PROTOCOLO.
use crate::StepError;
use rf_d_circuit::{cutoff,mixer_on::OnMixer};
#[path="prepared_chain_charge.rs"] mod chain_charge;
#[path="prepared_contour_residual.rs"] mod contour;
pub use contour::Controls;
pub const N:usize=118;
pub const M:usize=2*N;
pub const B:[[f64;2];2]=contour::B;
#[derive(Clone,Copy)]
pub struct Parameters {chain:chain_charge::Parameters,pub time:f64}
impl Parameters {
    pub fn new(mut chain:rf_d_circuit::chain_charge::Parameters)->Result<Self,StepError>{
        // Q26/Q28 now belong to the contour graph, with its nominal cards.
        for q in [chain.circuit.cutoff.q26,chain.circuit.cutoff.q28] {
            if q.transistor_is_a!=1e-14 || q.beta_forward!=100. || q.beta_reverse!=5. || q.temperature_k!=298.15 {
                return Err(StepError::InvalidInput);
            }
        }
        chain.boundary.panel=cutoff::PanelBoundary::default();
        chain.boundary.recovery.vca.loudness_v=0.;
        chain.mixer=OnMixer::new([false;5],[0.5;4]).map_err(|_|StepError::InvalidInput)?;
        Ok(Self{chain:chain_charge::Parameters::new(chain)?,time:0.})
    }
}
/// Shared Q26/Q28, VCA base and ladder TAIL. Remaining chain nodes retain order.
pub const fn chain_index(k:usize)->usize {
    match k {5=>55,32=>54,62..=65=>k-28,_=>56+k-(if k>5{1}else{0})-(if k>32{1}else{0})-(if k>65{4}else{0})}
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct State{pub high:[f64;N],pub low:[f64;N],pub optional:bool}
fn two_sum(a:f64,b:f64)->(f64,f64){let s=a+b;let v=s-a;(s,(a-(s-v))+(b-v))}
impl State {
    pub fn new(high:[f64;N],optional:bool)->Self{Self{high,low:[0.;N],optional}}
    pub fn advanced(self,d:[f64;N])->Self {
        let mut s=self;
        for k in 0..N {let(h,e)=two_sum(s.high[k],d[k]);let(l,f)=two_sum(s.low[k],e);let(h,l)=two_sum(h,l);(s.high[k],s.low[k])=two_sum(h,l+f);}
        s
    }
    pub fn valid(self)->bool{(0..N).all(|k|self.high[k].is_finite()&&self.low[k].is_finite()&&self.high[k].abs()<40.&&two_sum(self.high[k],self.low[k])==(self.high[k],self.low[k]))}
    fn contour(self)->contour::State{contour::State{high:std::array::from_fn(|k|self.high[k]),low:std::array::from_fn(|k|self.low[k]),optional:self.optional}}
    fn chain(self)->chain_charge::State{chain_charge::State{high:std::array::from_fn(|k|self.high[chain_index(k)]),low:std::array::from_fn(|k|self.low[chain_index(k)])}}
}
pub struct Parts{pub dc:[f64;N],pub j:[[f64;N];N],pub dq:[f64;N],pub mass:[[f64;N];N],pub now:State}
pub fn sources(_t:f64)->[f64;5]{[0.;5]}
#[inline(always)]
pub fn parts<const FULL:bool>(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{
    if !old.valid() || !delta.valid() || old.optional!=delta.optional || !t.is_finite() || t<0. || !p.time.is_finite() || p.time<0. {return Err(StepError::InvalidInput);}
    let now=old.advanced(delta.high).advanced(delta.low);
    if !now.valid(){return Err(StepError::InvalidInput);}
    let audio=chain_charge::linearize_prevalidated::<FULL>(p.chain,sources(t),old.chain(),delta.chain(),h,now.chain())?;
    let dual=contour::parts::<FULL>(old.contour(),delta.contour(),c,h,now.contour())?;
    let mut s=Parts{dc:[0.;N],j:[[0.;N];N],dq:[0.;N],mass:[[0.;N];N],now};
    for a in 0..56 {s.dc[a]=dual.dc[a];s.dq[a]=dual.dq[a];if FULL{for b in 0..56{let g=dual.j[a][b];let m=dual.mass[a][b];if !g.is_finite()||!m.is_finite(){return Err(StepError::ExponentialDomain);}s.j[a][b]=g;s.mass[a][b]=m;}}}
    for a in 0..68 {
        // C18 is carried once by the contour's node 34, not by old chain row 62.
        if (62..66).contains(&a){continue;}
        let i=chain_index(a);s.dc[i]+=audio.dc[a];s.dq[i]+=audio.charge_over_h[a];
        if FULL{for b in 0..68 {let j=chain_index(b);let g=audio.dc_jacobian[a][b];let m=audio.mass_over_h[a][b];if g!=0.{s.j[i][j]+=g;if !s.j[i][j].is_finite(){return Err(StepError::ExponentialDomain);}}if m!=0.{s.mass[i][j]+=m;if !s.mass[i][j].is_finite(){return Err(StepError::ExponentialDomain);}}}}
    }
    if s.dc.iter().chain(s.dq.iter()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
    Ok(s)
}
pub fn dc(p:Parameters,x:State,c:Controls)->Result<Parts,StepError>{parts::<true>(p,x,State::new([0.;N],x.optional),c,1e-6,0.)}
pub fn currents(s:State)->[f64;2]{[(s.high[3]+s.low[3]-s.high[54]-s.low[54])/68000.,(s.high[55]+s.low[55]-s.high[37]-s.low[37])/680.]}
