//! Laboratory nominal phase VCO joined to the complete 118-node loaded chain.
//! HYBRID_VOZ_PROTOCOLO: branch at 40 ms, unchanged contour/filter/VCA charges.
//! Exact dynamic Schur variant: tools/prepare_hybrid_schur.py.
#[path="support_hybrid_solver.rs"] pub mod solver;
pub use solver::Workspace;
use crate::StepError;
use rf_d_circuit::chain_charge;
#[path="prepared_voice_chain.rs"] mod graph;
#[path="hybrid_phase_source.rs"] pub mod phase;
pub use graph::{Parameters,State,Controls,Parts,N,M,B,currents};
#[inline(always)]
pub fn parts<const FULL:bool>(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{
    let mut s=graph::parts::<FULL>(p,old,delta,c,h,t)?;
    // All old mixer branches are OFF. R6/R45 belong once to this VCO port.
    let port=phase::observe(t,s.now.high[116]).map_err(|_|StepError::InvalidInput)?;
    let y=port.admittance_s[3][3];
    s.dc[116]+=port.current_a[3]+y*s.now.low[116];
    if FULL{s.j[116][116]+=y;}
    Ok(s)
}
pub fn residual_parts(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<([f64;N],[f64;N]),StepError>{
    let s=parts::<false>(p,old,delta,c,h,t)?;Ok((s.dc,s.dq))
}
fn max<const S:usize>(x:[f64;S])->f64{x.into_iter().fold(0.,|a,v|a.max(v.abs()))}
fn gaussian(w:&mut Workspace,s:&[Parts;2],r:[f64;M])->Result<[f64;M],StepError>{
    w.solve([solver::Stage{dc:&s[0].j,mass:&s[0].mass},solver::Stage{dc:&s[1].j,mass:&s[1].mass}],B,r)
}
pub struct Pair {
    pub delta: [State; 2],
    pub stages: [State; 2],
    pub residual_a: f64,
    pub correction_v: f64,
    pub iterations: usize,
}
pub fn radau(w:&mut Workspace,p: Parameters, old: State, c: Controls, h: f64, budget: usize) -> Result<Pair, StepError> {
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
    let evaluate = |d:[State;2]|->Result<[Parts;2],StepError>{
        Ok([parts::<true>(p,old,d[0],c,h,p.time+h/3.)?,parts::<true>(p,old,d[1],c,h,p.time+h)?])
    };
    let residual = |s:&[Parts;2]|->[f64;M]{std::array::from_fn(|k|{
        let a=k%N;let i=k/N;s[i].dc[a]+B[i][0]*s[0].dq[a]+B[i][1]*s[1].dq[a]
    })};
    let evaluate_residual = |d:[State;2]|->Result<[f64;M],StepError>{
        let(a,qa)=residual_parts(p,old,d[0],c,h,p.time+h/3.)?;let(b,qb)=residual_parts(p,old,d[1],c,h,p.time+h)?;
        let mut r=[0.;M];for k in 0..N{r[k]=a[k]+B[0][0]*qa[k]+B[0][1]*qb[k];r[N+k]=b[k]+B[1][0]*qa[k]+B[1][1]*qb[k];}Ok(r)
    };
    for iteration in 1..=budget {
        let s=evaluate(d)?;let r=residual(&s);let stages=[s[0].now,s[1].now];
        let direction = gaussian(w,&s, r.map(|v| -v))?;
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
            let merit=if norm<=1e-12{
                if let Ok(ss)=evaluate(trial){let rr=residual(&ss);let weak=max(rr)<=1e-12&&max(gaussian(w,&ss,rr.map(|v|-v))?)<corr;Some((max(rr),weak))}else{None}
            }else{evaluate_residual(trial).ok().map(|rr|(max(rr),false))};
            if let Some((next,weak))=merit{if next<norm||weak{d=trial;found=true;break;}}
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
pub fn advance(w:&mut Workspace,p: Parameters, state: &mut State, c: Controls, mut h: f64) -> Result<Accepted, StepError> {
    let old = *state;
    if !h.is_finite() || h <= 0. || h > 1e-3 || !old.valid() {
        return Err(StepError::InvalidInput);
    }
    if old.optional != c.optional {
        return Err(StepError::InvalidInput);
    }
    for attempt in 1..=32 {
        let trial = (|| {
            let coarse = radau(w,p, old, c, h, 80)?;
            let a = radau(w,p, old, c, h / 2., 80)?;
            let b = radau(w,{let mut next=p;next.time+=h/2.;next}, a.stages[1], c, h / 2., 80)?;
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
