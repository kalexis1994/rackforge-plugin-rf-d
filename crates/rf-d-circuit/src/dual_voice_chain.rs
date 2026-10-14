//! Generated chain binding: OSC1 belongs to VCO; BUS is shared.
//! Laboratory simultaneous dual contour -> ladder/recovery/two VCAs/J7.
//! Fixed nominal scene and source boundary: CONTORNOS_CADENA_PROTOCOLO.
use crate::StepError;
use rf_d_circuit::{chain_charge, cutoff, mixer_on::OnMixer};
#[path="dual_contour_loaded.rs"] mod contour;
pub use contour::Controls;
pub const N:usize=118;
pub const M:usize=2*N;
pub const B:[[f64;2];2]=contour::B;
#[derive(Clone,Copy)]
pub struct Parameters {chain:chain_charge::Parameters,pub time:f64}
impl Parameters {
    pub fn new(mut chain:chain_charge::Parameters)->Result<Self,StepError>{
        // Q26/Q28 now belong to the contour graph, with its nominal cards.
        for q in [chain.circuit.cutoff.q26,chain.circuit.cutoff.q28] {
            if q.transistor_is_a!=1e-14 || q.beta_forward!=100. || q.beta_reverse!=5. || q.temperature_k!=298.15 {
                return Err(StepError::InvalidInput);
            }
        }
        chain.boundary.panel=cutoff::PanelBoundary::default();
        chain.boundary.recovery.vca.loudness_v=0.;
        chain.mixer=OnMixer::new([false;5],[0.5;4]).map_err(|_|StepError::InvalidInput)?;
        Ok(Self{chain,time:0.})
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
pub fn parts(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{
    if !old.valid() || !delta.valid() || old.optional!=delta.optional || !t.is_finite() || t<0. || !p.time.is_finite() || p.time<0. {return Err(StepError::InvalidInput);}
    let mut audio=chain_charge::linearize_compensated(p.chain,sources(t),old.chain(),delta.chain(),h)?;
    let dual=contour::parts(old.contour(),delta.contour(),c,h)?;
    let now=old.advanced(delta.high).advanced(delta.low);
    // Omit the old cutoff equations; subtract only their R60 load on ladder TAIL.
    let v=|k|now.high[k]+now.low[k];
    audio.dc[5]-=(v(55)-v(37))/680.;
    audio.dc_jacobian[5][5]-=1./680.;
    audio.dc_jacobian[5][65]+=1./680.;
    // The actual R59 is already in the contour, connected to the real VCA base.
    audio.dc[32]-=v(54)/68000.;
    audio.dc_jacobian[32][32]-=1./68000.;
    let mut s=Parts{dc:[0.;N],j:[[0.;N];N],dq:[0.;N],mass:[[0.;N];N],now};
    for a in 0..56 {s.dc[a]=dual.dc[a];s.dq[a]=dual.dq[a];for b in 0..56{s.j[a][b]=dual.j[a][b];s.mass[a][b]=dual.mass[a][b];}}
    for a in 0..68 {
        // C18 is carried once by the contour's node 34, not by old chain row 62.
        if (62..66).contains(&a){continue;}
        let i=chain_index(a);s.dc[i]+=audio.dc[a];s.dq[i]+=audio.charge_over_h[a];
        for b in 0..68 {let j=chain_index(b);s.j[i][j]+=audio.dc_jacobian[a][b];s.mass[i][j]+=audio.mass_over_h[a][b];}
    }
    if s.dc.iter().chain(s.dq.iter()).chain(s.j.iter().flatten()).chain(s.mass.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
    Ok(s)
}
pub fn dc(p:Parameters,x:State,c:Controls)->Result<Parts,StepError>{parts(p,x,State::new([0.;N],x.optional),c,1e-6,0.)}
pub fn currents(s:State)->[f64;2]{[(s.high[3]+s.low[3]-s.high[54]-s.low[54])/68000.,(s.high[55]+s.low[55]-s.high[37]-s.low[37])/680.]}
