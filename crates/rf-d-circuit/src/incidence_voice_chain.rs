//! Generated chain binding: OSC1 belongs to VCO; BUS is shared.
//! Laboratory simultaneous dual contour -> ladder/recovery/two VCAs/J7.
//! Fixed nominal scene and source boundary: CONTORNOS_CADENA_PROTOCOLO.
use crate::StepError;
use super::incidence::{Row,Tangent};
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
pub struct Parts{pub dc:[f64;N],pub dq:[f64;N],pub now:State,pub tangent:Tangent}
pub fn sources(_t:f64)->[f64;5]{[0.;5]}
#[inline(always)]
pub fn parts<const FULL:bool>(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{
    if !old.valid() || !delta.valid() || old.optional!=delta.optional || !t.is_finite() || t<0. || !p.time.is_finite() || p.time<0. {return Err(StepError::InvalidInput);}
    let now=old.advanced(delta.high).advanced(delta.low);
    if !now.valid(){return Err(StepError::InvalidInput);}
    let audio=chain_charge::linearize_prevalidated::<FULL>(p.chain,sources(t),old.chain(),delta.chain(),h,now.chain())?;
    let dual=contour::parts::<FULL>(old.contour(),delta.contour(),c,h,now.contour())?;
    let mut s=Parts{dc:[0.;N],dq:[0.;N],now,tangent:Tangent::new()};
    for a in 0..56{s.dc[a]=dual.dc[a];s.dq[a]=dual.dq[a];}
    for a in 0..68{if(62..66).contains(&a){continue;}let i=chain_index(a);s.dc[i]+=audio.dc[a];s.dq[i]+=audio.charge_over_h[a];}
    if FULL{
        // Source map, not measured support. Every actual component entry is read.
        const AUDIO_ROW:[usize;N]={let mut ids=[68;N];let mut k=0;while k<68{if k<62||k>=66{ids[chain_index(k)]=k;}k+=1;}ids};
        for a in 0..N{let mut row=Row::new();
            if a<56{for b in 0..56{row.set(b,dual.j[a][b],dual.mass[a][b])?;}}
            let audio_row=AUDIO_ROW[a];if audio_row<68{for b in 0..68{row.add(chain_index(b),audio.dc_jacobian[audio_row][b],audio.mass_over_h[audio_row][b])?;}}
            s.tangent.push_row(a,&mut row)?;
        }
    }
    if s.dc.iter().chain(s.dq.iter()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
    Ok(s)
}
pub fn dc(p:Parameters,x:State,c:Controls)->Result<Parts,StepError>{parts::<true>(p,x,State::new([0.;N],x.optional),c,1e-6,0.)}
pub fn currents(s:State)->[f64;2]{[(s.high[3]+s.low[3]-s.high[54]-s.low[54])/68000.,(s.high[55]+s.low[55]-s.high[37]-s.low[37])/680.]}
