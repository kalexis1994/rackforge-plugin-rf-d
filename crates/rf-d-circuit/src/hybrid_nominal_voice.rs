//! Laboratory nominal phase VCO joined to the complete 118-node loaded chain.
//! HYBRID_VOZ_PROTOCOLO: branch at 40 ms, unchanged contour/filter/VCA charges.
//! Derived solver substitutions: tools/prepare_hybrid_voice.py.
use crate::StepError;
use rf_d_circuit::chain_charge;
#[path="dual_voice_chain.rs"] mod graph;
#[path="hybrid_phase_source.rs"] pub mod phase;
pub use graph::{Parameters,State,Controls,Parts,N,M,B,currents};
pub fn parts(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{
    let mut s=graph::parts(p,old,delta,c,h,t)?;
    // All old mixer branches are OFF. R6/R45 belong once to this VCO port.
    let port=phase::observe(t,s.now.high[116]).map_err(|_|StepError::InvalidInput)?;
    let y=port.admittance_s[3][3];
    s.dc[116]+=port.current_a[3]+y*s.now.low[116];
    s.j[116][116]+=y;
    Ok(s)
}
fn max<const S:usize>(x:[f64;S])->f64{x.into_iter().fold(0.,|a,v|a.max(v.abs()))}
fn gaussian<const S:usize>(a:[[f64;S];S],r:[f64;S])->Result<[f64;S],StepError>{
    rf_d_circuit::block_decay_voice::solve_linear_extent(a,r)
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
            if let Ok((rr, jj, _)) = system(trial) {
                let weak = norm <= 1e-12 && max(rr) <= 1e-12
                    && max(gaussian(jj, rr.map(|v| -v))?) < corr;
                if max(rr) < norm || weak {
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
    if !h.is_finite() || h <= 0. || h > 1e-3 || !old.valid() {
        return Err(StepError::InvalidInput);
    }
    if old.optional != c.optional {
        return Err(StepError::InvalidInput);
    }
    for attempt in 1..=32 {
        let trial = (|| {
            let coarse = radau(p, old, c, h, 80)?;
            let a = radau(p, old, c, h / 2., 80)?;
            let b = radau({let mut next=p;next.time+=h/2.;next}, a.stages[1], c, h / 2., 80)?;
            let fine = b.stages[1];
            let error = (0..N).fold(0_f64, |m, k| {
                m.max(
                    ((coarse.stages[1].high[k] - fine.high[k])
                        + (coarse.stages[1].low[k] - fine.low[k]))
                        .abs()
                        / (500e-6 + 1e-4 * fine.high[k].abs()),
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
