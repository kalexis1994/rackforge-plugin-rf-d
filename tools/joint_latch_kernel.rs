//! Conditional CA3046 VCO1 -> shared BUS -> ladder/VCAs/J7.
//! Explicit OSC1 panel remains in VCO. See VOZ_BUS_CONJUNTO_PROTOCOLO.
#[path="latch_charge_driver.rs"] pub mod latch_charge_driver;
#[path="contour_closed_driver.rs"] pub mod contour_closed_driver;
use rf_d_circuit::{vco1_stamp::{self,Controls,Mode},chain_charge::{self,Parameters as Chain},mixer_on::OnMixer,StepError};
pub const N:usize=229;
pub const M:usize=2*N;
pub const BUS:usize=12;
pub const MIN_DT_S:f64=chain_charge::MIN_DT_S;
pub const B:[[f64;2];2]=rf_d_circuit::vco1_radau::B;
pub const fn vco_index(k:usize)->Option<usize> {if k==108 {None} else if k<108 {Some(k)} else {Some(k-1)}}
pub const fn chain_index(k:usize)->usize {if k==66 {BUS} else if k==67 {199} else {133+k}}
#[derive(Clone,Copy)]
pub struct Parameters {pub controls:Controls,chain:Chain,pub sources:[f64;5],pub c2_v:f64,pub reset_v:f64,pub q25:f64,pub reset_driver:f64,pub final_decay:bool,pub keyboard:f64,pub short:bool,pub set_base:f64}
impl Parameters {
 /// OSC1 always belongs to the VCO panel; other branches retain imposed sources.
 pub fn new(controls:Controls,mut chain:Chain,other_on:[bool;4],alpha:[f64;4],sources:[f64;5])->Result<Self,StepError> {
  if sources.iter().any(|v|!v.is_finite()||v.abs()>40.) {return Err(StepError::InvalidInput);}
  chain.mixer=OnMixer::new([false,other_on[0],other_on[1],other_on[2],other_on[3]],alpha).map_err(|_|StepError::InvalidInput)?;
  chain.boundary.recovery.vca.loudness_v=0.;Ok(Self{controls,chain,sources,c2_v:3.2,reset_v:0.01,q25:8.3,reset_driver:9.,final_decay:true,keyboard:0.,short:false,set_base:0.01})
 }
 pub fn chain(self)->Chain {self.chain}
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct State {pub high:[f64;N],pub low:[f64;N]}
impl State {
 pub fn from_nodes(high:[f64;N])->Self {Self{high,low:[0.;N]}}
 pub fn advanced(self,d:[f64;N])->Self {
  let mut s=self;for k in 0..N {let(h,e)=fine::two_sum(s.high[k],d[k]);let(l,f)=fine::two_sum(s.low[k],e);let(h,l)=fine::two_sum(h,l);(s.high[k],s.low[k])=fine::two_sum(h,l+f);}s
 }
 /// Explicitly lift a conditioned history; the chain BUS is owned by VCO12.
 pub fn lift(vco_high:[f64;134],vco_low:[f64;134],chain:chain_charge::State)->Self {
  let mut s=Self::from_nodes([0.;N]);for k in 0..134 {if let Some(i)=vco_index(k) {s.high[i]=vco_high[k];s.low[i]=vco_low[k];}}
  for k in 0..68 {if k!=66 {let i=chain_index(k);s.high[i]=chain.high[k];s.low[i]=chain.low[k];}}s
 }

 fn chain(self)->chain_charge::State {chain_charge::State{high:std::array::from_fn(|k|self.high[chain_index(k)]),low:std::array::from_fn(|k|self.low[chain_index(k)])}}
}
pub struct Parts {pub dc:[f64;N],pub charge_over_h:[f64;N],pub dc_jacobian:[[f64;N];N],pub mass_over_h:[[f64;N];N],pub candidate:State}
pub fn parts(p:Parameters,old:State,delta:State,h:f64)->Result<Parts,StepError> {

 let pp=rf_d_circuit::joint_voice::Parameters::new(p.controls,p.chain,[false;4],[0.5;4],p.sources)?;
 let project=|s:State|rf_d_circuit::joint_voice::State{high:std::array::from_fn(|k|s.high[k]),low:std::array::from_fn(|k|s.low[k])};
 let base=rf_d_circuit::joint_voice::parts(pp,project(old),project(delta),h)?;
 let mut s=Parts{dc:[0.;N],charge_over_h:[0.;N],dc_jacobian:[[0.;N];N],mass_over_h:[[0.;N];N],candidate:State::from_nodes([0.;N])};
 for a in 0..200 {
  s.dc[a]=base.dc[a];s.charge_over_h[a]=base.charge_over_h[a];s.candidate.high[a]=base.candidate.high[a];s.candidate.low[a]=base.candidate.low[a];
  for b in 0..200 {s.dc_jacobian[a][b]=base.dc_jacobian[a][b];s.mass_over_h[a][b]=base.mass_over_h[a][b];}
 }

 let now=old.advanced(delta.high).advanced(delta.low);

 s.dc[165]-=(now.high[165]+now.low[165])/68000.;s.dc_jacobian[165][165]-=1./68000.;
 let map=|k:usize|if k<29{200+k}else{165};
 let tr=contour_closed_driver::linearize(std::array::from_fn(|k|now.high[map(k)]),p.keyboard,p.final_decay,p.short)?;
 for a in 0..30{let i=map(a);s.candidate.high[i]=now.high[i];s.candidate.low[i]=now.low[i];s.dc[i]+=tr.dc[a]+(0..30).map(|b|tr.jacobian[a][b]*now.low[map(b)]).sum::<f64>();for b in 0..30{s.dc_jacobian[i][map(b)]+=tr.jacobian[a][b];}}
 for (a,b,c) in [(205,None,1e-5),(221,None,1e-7),(223,Some(225),1e-8)]{
  let d=c/h*(delta.high[a]+delta.low[a]-b.map_or(0.,|k|delta.high[k]+delta.low[k]));s.charge_over_h[a]+=d;s.mass_over_h[a][a]+=c/h;
  if let Some(b)=b{s.charge_over_h[b]-=d;s.mass_over_h[a][b]-=c/h;s.mass_over_h[b][a]-=c/h;s.mass_over_h[b][b]+=c/h;}
 }
 for(b,c)in[(225,226),(227,228)]{
  let(q,m)=latch_charge_driver::terminal([(old.high[b],old.low[b]),(old.high[c],old.low[c])],[(now.high[b],now.low[b]),(now.high[c],now.low[c])])?;
  for(a,i)in[b,c].into_iter().enumerate(){s.charge_over_h[i]+=q[a]/h;for(k,j)in[b,c].into_iter().enumerate(){s.mass_over_h[i][j]+=m[a][k]/h;}}
 }
 if s.dc.iter().chain(s.charge_over_h.iter()).chain(s.dc_jacobian.iter().flatten()).chain(s.mass_over_h.iter().flatten()).any(|v|!v.is_finite()) {return Err(StepError::ExponentialDomain);}Ok(s)
}
pub fn constraint_row(p:Parameters,k:usize)->bool { (98..133).contains(&k) || (k>=133&&k<200&&chain_charge::constraint_row(p.chain,if k==199 {67} else {k-133})) }
fn current_unknown(k:usize)->bool {(98..133).contains(&k)}
pub struct Stamp {pub residual:[f64;M],pub jacobian:[[f64;M];M],pub candidates:[State;2]}
pub fn linearize(p:Parameters,old:State,delta:[State;2],h:f64)->Result<Stamp,StepError> {
 let q=[parts(p,old,delta[0],h)?,parts(p,old,delta[1],h)?];
 Ok(Stamp {residual:std::array::from_fn(|k|{let i=k/N;let a=k%N;q[i].dc[a]+B[i][0]*q[0].charge_over_h[a]+B[i][1]*q[1].charge_over_h[a]}),
  jacobian:std::array::from_fn(|k|std::array::from_fn(|l|{let i=k/N;let j=l/N;let a=k%N;let b=l%N;B[i][j]*q[j].mass_over_h[a][b]+if i==j {q[i].dc_jacobian[a][b]} else {0.}})),candidates:[q[0].candidate,q[1].candidate]})
}
fn merit(p:Parameters,r:&[f64;M])->f64 {r.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if constraint_row(p,k%N) {1e-11} else {1e-13}))}
fn correction(d:&[f64;M])->f64 {d.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if current_unknown(k%N) {2e-12} else {2e-9}))}
pub struct Pair {pub candidates:[State;2],pub increments:[State;2],pub residual_ratio:f64,pub correction_ratio:f64,pub iterations:usize,pub trials:usize}
/// Pure candidate solve. The caller publishes both block histories together.
pub fn step(p:Parameters,old:State,h:f64)->Result<Pair,StepError> {
 let mut seed=[0.;N];
 if p.keyboard-(old.high[222]+old.low[222])>0.5{seed[222]=p.keyboard-0.5-old.high[222]-old.low[222];}
 if p.short && old.high[218]+old.low[218]>1. {
  let v=|k|old.high[k]+old.low[k];
  for(k,target)in [(217,7.),(218,0.5),(219,0.45),(214,3.1),(210,3.7_f64.min(v(205)+0.6)),(211,v(205)),(216,7.),(224,v(227)+0.4)] {seed[k]=target-old.high[k]-old.low[k];}
 } else if !p.short && old.high[218]+old.low[218]<1. {
  let v=|k|old.high[k]+old.low[k];
  for(k,target)in [(217,0.03),(218,6.),(219,0.7),(214,0.7),(210,1.3),(211,0.7),(216,if p.final_decay {0.03} else {v(205)-0.6}),(224,v(227)+0.4)] {seed[k]=target-old.high[k]-old.low[k];}
 }
 let mut delta=[State::from_nodes(seed);2];let mut trials=0;
 for iteration in 1..=64 {
  let s=linearize(p,old,delta,h)?;let norm=merit(p,&s.residual);let d=solve_linear_sparse(s.jacobian,std::array::from_fn(|k|-s.residual[k]))?;let ratio=correction(&d);
  if norm<=1.&&ratio<=1. {return Ok(Pair{candidates:s.candidates,increments:delta,residual_ratio:norm,correction_ratio:ratio,iterations:iteration,trials});}
  let mut accepted=false;
  for power in 0..24 {let alpha=2_f64.powi(-power);let trial=std::array::from_fn(|i|delta[i].advanced(std::array::from_fn(|a|alpha*d[i*N+a])));trials+=1;
   if let Ok(t)=linearize(p,old,trial,h) {if let Ok(dd)=solve_linear_sparse(t.jacobian,std::array::from_fn(|k|-t.residual[k])) {let next=correction(&dd);
    if (merit(p,&t.residual)<=1.&&next<=1.)||merit(p,&t.residual)<norm*(1.-1e-4*alpha) {delta=trial;accepted=true;break;}
   }}
  }
  if !accepted {return Err(StepError::NoDecrease);}
 }Err(StepError::IterationBudget)
}

mod fine { pub fn two_sum(a:f64,b:f64)->(f64,f64) {let s=a+b;let v=s-a;let e=(a-(s-v))+(b-v);(s,e)} }
pub fn max_abs<const M: usize>(x: &[f64; M]) -> f64 {
    x.iter().fold(0.0_f64, |a, v| a.max(v.abs()))
}

pub fn solve_linear<const M: usize>(
    j: [[f64; M]; M],
    rhs: [f64; M],
) -> Result<[f64; M], StepError> {
    solve_linear_internal::<M, false>(j, rhs)
}

/// Same scaled pivots and elimination, skipping only an exactly zero entry.
/// No small coefficient is dropped; finite matrices have the same solution.
pub fn solve_linear_sparse<const M: usize>(
    j: [[f64; M]; M],
    rhs: [f64; M],
) -> Result<[f64; M], StepError> {
    solve_linear_internal::<M, true>(j, rhs)
}

fn solve_linear_internal<const M: usize, const SKIP_ZERO: bool>(
    mut j: [[f64; M]; M],
    mut rhs: [f64; M],
) -> Result<[f64; M], StepError> {
    let mut scale = [0.0; M];
    for i in 0..M {
        scale[i] = max_abs(&j[i]);
        if scale[i] == 0.0 {
            return Err(StepError::SingularJacobian);
        }
    }
    for col in 0..M {
        let mut pivot = col;
        let mut best = 0.0;
        for row in col..M {
            if SKIP_ZERO && j[row][col] == 0.0 {
                continue;
            }
            let score = j[row][col].abs() / scale[row];
            if score > best {
                best = score;
                pivot = row;
            }
        }
        if best < 1e-12 {
            return Err(StepError::SingularJacobian);
        }
        j.swap(col, pivot);
        rhs.swap(col, pivot);
        scale.swap(col, pivot);
        let diagonal = j[col][col];
        for row in (col + 1)..M {
            if SKIP_ZERO && j[row][col] == 0.0 {
                continue;
            }
            let factor = j[row][col] / diagonal;
            j[row][col] = 0.0;
            #[allow(clippy::needless_range_loop)]
            for k in (col + 1)..M {
                j[row][k] -= factor * j[col][k];
            }
            rhs[row] -= factor * rhs[col];
        }
    }
    let mut out = [0.0; M];
    for row in (0..M).rev() {
        let mut value = rhs[row];
        for k in (row + 1)..M {
            value -= j[row][k] * out[k];
        }
        out[row] = value / j[row][row];
    }
    if out.iter().any(|v| !v.is_finite()) {
        return Err(StepError::SingularJacobian);
    }
    Ok(out)
}

