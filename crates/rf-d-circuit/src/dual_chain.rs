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
        chain.mixer=OnMixer::new([true,false,false,false,false],[0.5;4]).map_err(|_|StepError::InvalidInput)?;
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
pub fn sources(t:f64)->[f64;5]{[if t>=0.001{0.2*(2.*std::f64::consts::PI*100.*(t-0.001)).sin()}else{0.},0.,0.,0.,0.]}
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
pub fn gaussian<const S: usize>(
    mut a: [[f64; S]; S],
    mut rhs: [f64; S],
) -> Result<[f64; S], StepError> {
    for k in 0..S {
        let mut p = k;
        for i in k + 1..S {
            if a[i][k].abs() > a[p][k].abs() {
                p = i;
            }
        }
        if a[p][k] == 0. || !a[p][k].is_finite() {
            return Err(StepError::SingularJacobian);
        }
        a.swap(k, p);
        rhs.swap(k, p);
        for i in k + 1..S {
            if a[i][k] == 0. {
                continue;
            }
            let f = a[i][k] / a[k][k];
            a[i][k] = 0.;
            for j in k + 1..S {
                a[i][j] -= f * a[k][j];
            }
            rhs[i] -= f * rhs[k];
        }
    }
    let mut x = [0.; S];
    for k in (0..S).rev() {
        x[k] = (rhs[k] - (k + 1..S).map(|j| a[k][j] * x[j]).sum::<f64>()) / a[k][k];
    }
    if x.iter().any(|v| !v.is_finite()) {
        return Err(StepError::SingularJacobian);
    }
    Ok(x)
}
fn max<const S: usize>(x: [f64; S]) -> f64 {
    x.into_iter().fold(0., |a, v| a.max(v.abs()))
}
pub fn initial(p: Parameters, seed: [f64; N], optional: bool) -> Result<State, StepError> {
    let c = Controls {
        optional,
        ..Controls::default()
    };
    let mut x = State::new(seed, optional);
    for _ in 0..80 {
        let s = dc(p, x, c)?;
        let d = gaussian(s.j, s.dc.map(|v| -v))?;
        let norm = max(s.dc);
        if norm <= 1e-12 && max(d) <= 2e-9 {
            return Ok(x);
        }
        let mut found = false;
        for power in 0..24 {
            let trial = x.advanced(d.map(|v| v * 2_f64.powi(-power)));
            if let Ok(t) = dc(p, trial, c) {
                let improves_weak_nodes = norm <= 1e-12 && max(t.dc) <= 1e-12
                    && max(gaussian(t.j, t.dc.map(|v| -v))?) < max(d);
                if max(t.dc) < norm || improves_weak_nodes {
                    x = trial;
                    found = true;
                    break;
                }
            }
        }
        if !found {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}
pub struct Pair {
    pub delta: [State; 2],
    pub stages: [State; 2],
    pub residual_a: f64,
    pub correction_v: f64,
    pub iterations: usize,
}
pub fn radau(p: Parameters, old: State, c: Controls, h: f64, budget: usize) -> Result<Pair, StepError> {
    if budget == 0 || budget > 80 {
        return Err(StepError::InvalidInput);
    }
    let zero = State::new([0.; N], old.optional);
    let mut d = [zero; 2];
    if c.key - old.high[22] - old.low[22] > 0.5 {
        for stage in &mut d {
            stage.high[22] = c.key - 0.5 - old.high[22] - old.low[22];
        }
    }
    let system = |d: [State; 2]| -> Result<([f64; M], [[f64; M]; M], [State; 2]), StepError> {
        let s = [parts(p, old, d[0], c, h, p.time+h/3.)?, parts(p, old, d[1], c, h, p.time+h)?];
        let r = std::array::from_fn(|k| {
            let a = k % N;
            let i = k / N;
            s[i].dc[a] + B[i][0] * s[0].dq[a] + B[i][1] * s[1].dq[a]
        });
        let j = std::array::from_fn(|k| {
            std::array::from_fn(|l| {
                let i = k / N;
                let a = k % N;
                let jj = l / N;
                let b = l % N;
                B[i][jj] * s[jj].mass[a][b] + if i == jj { s[i].j[a][b] } else { 0. }
            })
        });
        Ok((r, j, [s[0].now, s[1].now]))
    };
    for iteration in 1..=budget {
        let (r, j, stages) = system(d)?;
        let direction = gaussian(j, r.map(|v| -v))?;
        let norm = max(r);
        let corr = max(direction);
        if norm <= 1e-12 && corr <= 2e-9 {
            return Ok(Pair {
                delta: d,
                stages,
                residual_a: norm,
                correction_v: corr,
                iterations: iteration,
            });
        }
        let mut found = false;
        for p in 0..24 {
            let scale = 2_f64.powi(-p);
            let trial = std::array::from_fn(|i| {
                d[i].advanced(std::array::from_fn(|k| scale * direction[i * N + k]))
            });
            if let Ok((rr, _, _)) = system(trial) {
                if max(rr) < norm {
                    d = trial;
                    found = true;
                    break;
                }
            }
        }
        if !found {
            return Err(StepError::NoDecrease);
        }
    }
    Err(StepError::IterationBudget)
}
pub struct Accepted {
    pub coarse: Pair,
    pub fine: [Pair; 2],
    pub h: f64,
    pub error: f64,
    pub attempts: usize,
}
pub fn advance(p: Parameters, state: &mut State, c: Controls, mut h: f64) -> Result<Accepted, StepError> {
    let old = *state;
    if !h.is_finite() || h <= 0. || !old.valid() {
        return Err(StepError::InvalidInput);
    }
    if old.optional != c.optional {
        return Err(StepError::InvalidInput);
    }
    for attempt in 1..=32 {
        let trial = (|| {
            let coarse = radau(p, old, c, h, 80)?;
            let a = radau(p, old, c, h / 2., 80)?;
            let b = radau(Parameters{time:p.time+h/2.,..p}, a.stages[1], c, h / 2., 80)?;
            let fine = b.stages[1];
            let error = (0..N).fold(0_f64, |m, k| {
                m.max(
                    ((coarse.stages[1].high[k] - fine.high[k])
                        + (coarse.stages[1].low[k] - fine.low[k]))
                        .abs()
                        / (2e-7 + 2e-7 * fine.high[k].abs()),
                )
            });
            Ok::<_, StepError>((coarse, [a, b], error))
        })();
        if let Ok((coarse, fine, error)) = trial {
            if error <= 1. {
                *state = fine[1].stages[1];
                return Ok(Accepted {
                    coarse,
                    fine,
                    h,
                    error,
                    attempts: attempt,
                });
            }
        }
        h *= 0.5;
        if h / 2. < chain_charge::MIN_DT_S {
            return Err(StepError::IterationBudget);
        }
    }
    Err(StepError::IterationBudget)
}
