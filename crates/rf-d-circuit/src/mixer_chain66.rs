//! Conditional imposed-source ON/C27 -> full 66-node chain, SVC-9 pp.19/13/10.
//! Immutable incoming history during every trial; atomic publication on success.
//! dt restricted to 0.5 us..1 ms for the fixed-C27 stamp replacement adapter.
use crate::{circuit66, mixer_c27::{C27OnPort, Response as MixerResponse}, mixer_on::OnMixer,
    output::main_load, output_conversion::{max_abs, solve_linear_sparse, Parameters as Conversion},
    Parameters as Headphone, SolverBudget, StepError};
use circuit66::{Boundary, Parameters, State};
const N:usize=66;

#[derive(Clone,Copy,Debug)]
pub struct ResultChain {
    pub chain:circuit66::Result66,
    pub mixer:MixerResponse,
    pub correction_v:f64,
}

fn dt(b:Boundary)->Result<f64,StepError> {
    let value=b.recovery.vca.second.output.output.dt_s;
    if !value.is_finite() || !(0.5e-6..=1e-3).contains(&value) {return Err(StepError::InvalidInput);}
    Ok(value)
}

pub fn initial_state(mixer:OnMixer,source_v:[f64;5],p:Parameters,c:Conversion,h:Headphone,
    mut b:Boundary,seed:[f64;16])->Result<State,StepError> {
    dt(b)?;
    b.bus_v=mixer.solve_imposed_current(source_v,0.0).map_err(|_|StepError::InvalidInput)?.bus_v;
    circuit66::initial_state(p,c,h,b,seed)
}

/// Natural node order, physical outgoing KCL except row49 voltage constraint.
pub fn linearize(previous:&State,mixer:OnMixer,source_v:[f64;5],p:Parameters,c:Conversion,h:Headphone,
    mut b:Boundary,x:&[f64;N])->Result<([f64;N],[[f64;N];N],MixerResponse),StepError> {
    let interval=dt(b)?;
    let port=C27OnPort::new(mixer).map_err(|_|StepError::InvalidInput)?
        .evaluate(source_v,x[6],previous.capacitor_v[5],interval).map_err(|_|StepError::InvalidInput)?;
    b.bus_v=port.bus_v;
    let (mut r,mut j)=circuit66::linearize(previous,p,c,h,b,x)?;
    let gc=10e-6/interval;
    r[6]+=port.current_a[5]-gc*(x[6]-b.bus_v-previous.capacitor_v[5]);
    j[6][6]+=port.jacobian_s[5][5]-gc;
    Ok((r,j,port))
}

fn root(previous:&State,mut x:[f64;N],mixer:OnMixer,source_v:[f64;5],p:Parameters,c:Conversion,h:Headphone,
    b:Boundary,budget:SolverBudget,evaluations:&mut usize)->Result<([f64;N],usize,f64,MixerResponse),StepError> {
    for iteration in 0..budget.iterations {
        let (r,j,port)=linearize(previous,mixer,source_v,p,c,h,b,&x)?;*evaluations+=1;
        let error=max_abs(&r);let direction=solve_linear_sparse(j,r.map(|v|-v))?;
        let correction=max_abs(&direction);
        if error<1e-11 && correction<1e-8 {return Ok((x,iteration,correction,port));}
        let mut accepted=None;
        for power in 0..budget.line_search_halvings {
            let scale=0.5_f64.powi(power as i32);
            let trial=std::array::from_fn(|i| x[i]+scale*direction[i]);
            *evaluations+=1;
            if let Ok((rr,jj,_))=linearize(previous,mixer,source_v,p,c,h,b,&trial) {
                let next_error=max_abs(&rr);
                if let Ok(dd)=solve_linear_sparse(jj,rr.map(|v|-v)) {
                    let decrease=if error<1e-11 { next_error<1e-11 && max_abs(&dd)<correction }
                        else {next_error<error};
                    if decrease {accepted=Some(trial);break;}
                }
            }
        }
        if let Some(trial)=accepted {x=trial;} else {return Err(StepError::NoDecrease);}
    }
    Err(StepError::IterationBudget)
}

pub fn step(state:&mut State,mixer:OnMixer,source_v:[f64;5],p:Parameters,c:Conversion,h:Headphone,
    mut b:Boundary,budget:SolverBudget)->Result<ResultChain,StepError> {
    dt(b)?;
    if !(1..=16).contains(&budget.iterations) || !(1..=16).contains(&budget.line_search_halvings)
        || state.node_v.iter().chain(state.previous_node_v.iter()).chain(state.capacitor_v.iter()).any(|v|!v.is_finite())
        || !state.c10_capacitor_v.is_finite() {return Err(StepError::InvalidInput);}
    let previous=*state;
    let predicted=std::array::from_fn(|i|2.0*state.node_v[i]-state.previous_node_v[i]);
    let mut evaluations=0;
    let (solution,fallback)=match root(&previous,predicted,mixer,source_v,p,c,h,b,budget,&mut evaluations) {
        Ok(v)=>(v,false),
        Err(_)=>(root(&previous,previous.node_v,mixer,source_v,p,c,h,b,budget,&mut evaluations)?,true),
    };
    let (x,iterations,correction,port)=solution;b.bus_v=port.bus_v;
    let (r,_,_)=linearize(&previous,mixer,source_v,p,c,h,b,&x)?;evaluations+=1;
    let lower=b.recovery.vca.second.output.output.r21_lower_ohm;
    let physical=r.iter().enumerate().filter(|(i,_)|*i!=49 || (lower>0.0 && lower<5000.0))
        .fold(0.0_f64,|a,(_,v)|a.max(v.abs()));
    let control=max_abs(&std::array::from_fn::<_,4,_>(|i|r[62+i]));
    let series=b.r14_ohm.unwrap_or(0.0)+1000.0-(p.r30_ohm-330.0);
    let gc=10e-6/dt(b)?;
    let i10=if b.r14_ohm.is_some() {gc/(1.0+gc*series)*(x[22]-x[7]-previous.c10_capacitor_v)} else {0.0};
    let main=main_load(b.recovery.vca.second.output.output)?;
    let mut candidate=previous;
    let mut chain=circuit66::publish_step(&mut candidate,p,b,main,(x,iterations,physical,i10,control),fallback,evaluations);
    candidate.capacitor_v[5]=port.next_capacitor_v;
    chain.output.board_input_current_a=-port.current_a[5];
    *state=candidate;
    Ok(ResultChain {chain,mixer:port,correction_v:correction})
}
