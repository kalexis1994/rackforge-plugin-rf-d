//! Experimental time approximation of the complete coupled circuit.
//! Gates apply to physical nodes/charge differences, not the 741 interiors.
//! See VOZ_PASO_OBSERVABLE_PROTOCOLO.md; no spatial equation is removed.
#[path="sparse_ordered_voice.rs"] mod full;
pub use full::{Parameters, State, Workspace, Accepted, Pair, N, M, B, vi, di, ci,
    initial, parts, loads, bus_balance, solver};
use crate::StepError;

fn difference(a:State,b:State,k:usize)->f64 {
    (a.high[k]-b.high[k])+(a.low[k]-b.low[k])
}
pub fn estimate(a:State,b:State)->f64 {
    let mut error=0_f64;
    // Physical VCO nodes, including both ends of C1/C2/C3/C4/C5/C6.
    // The interior macromodel states and ideal-source currents are excluded
    // only from this temporal estimator, never from Newton or the history.
    for k in 0..56 {
        error=error.max(difference(a,b,k).abs()/(200e-6+1e-4*b.high[k].abs()));
    }
    // Preserve charge-oriented comparisons where common-mode shifts cancel.
    for (u,v) in [(33,34),(2,48),(3,48),(40,14)] {
        let dv=difference(a,b,u)-difference(a,b,v);
        error=error.max(dv.abs()/(200e-6+1e-4*(b.high[u]-b.high[v]).abs()));
    }
    // Both contours, ladder, recovery, two VCAs and output coupling memories.
    for k in 0..118 {
        let i=di(k);
        error=error.max(difference(a,b,i).abs()/(500e-6+1e-4*b.high[i].abs()));
    }
    error
}
/// Publish only the two fine endpoints after a bounded coupled solve.
/// Invalid/rejected steps leave every HIGH/LOW value unchanged.
pub fn advance(w:&mut Workspace,p:Parameters,state:&mut State,mut ticks:u32)
    ->Result<Accepted,StepError> {
    if ticks<8 || !ticks.is_power_of_two() ||
        ticks as f64*rf_d_circuit::vco1_engine::TICK_S>1e-3 {
        return Err(StepError::InvalidInput);
    }
    let old=*state;
    for _ in 0..24 {
        let h=ticks as f64*rf_d_circuit::vco1_engine::TICK_S;
        let trial=(|| {
            let coarse=w.step(p,old,h)?;
            let a=w.step(p,old,h/2.)?;
            let b=w.step(p,a.stages[1],h/2.)?;
            let error=estimate(coarse.stages[1],b.stages[1]);
            Ok::<_,StepError>((coarse,[a,b],error))
        })();
        if let Ok((coarse,fine,error))=trial {
            if error<=1. {
                *state=fine[1].stages[1];
                return Ok(Accepted{coarse,fine,full_ticks:ticks,error});
            }
        }
        if ticks==8 {return Err(StepError::IterationBudget);}
        ticks/=2;
    }
    Err(StepError::IterationBudget)
}
