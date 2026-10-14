//! Signal/charge controlled time approximation of the complete coupled circuit.
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
    for k in [12,15,39,43,44,46,54] {
        error=error.max(difference(a,b,k).abs()/(200e-6+1e-4*b.high[k].abs()));
    }
    // Protect actual charge differences with a 2-pC floor for small caps.
    // Large coupling/timing caps retain the same 500-uV voltage budget.
    let mut cap=|u:usize,v:Option<usize>,c:f64| {
        let d=difference(a,b,u)-v.map_or(0.,|k|difference(a,b,k));
        let voltage=b.high[u]-v.map_or(0.,|k|b.high[k]);
        let tolerance=(500e-6+1e-4*voltage.abs()).max(2e-12/c);
        error=error.max(d.abs()/tolerance);
    };
    for (u,v,c) in [(43,None,1e-8),(33,Some(34),1e-10),(2,Some(48),1e-10),(3,Some(48),1e-11),(15,None,1.2e-7),(40,Some(14),1e-8)] {cap(u,v,c);}
    for (u,v,c) in rf_d_circuit::chain_charge::CAPACITORS {
        cap(ci(u),if v==68{None}else{Some(ci(v))},c);
    }
    // C2, C7, C4, C5, C1, C8, C18; source terminals are fixed.
    for (u,v,c) in [(5,None,1e-5),(21,None,1e-7),(23,Some(25),1e-8),(38,None,1e-5),(52,Some(39),1e-8),(48,None,1e-10),(34,None,1e-10)] {
        cap(di(u),v.map(di),c);
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
