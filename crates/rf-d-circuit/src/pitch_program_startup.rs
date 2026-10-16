//! Derived pitch variant; PITCH_PROGRAM_PROTOCOLO.md.
//! Cold DC for the nominal chain with the existing periodic driver frozen at t=0.
//! Does not initialize the physical VCO or continue an incoming capacitor history.
#[path="pitch_program_voice.rs"]pub mod voice;
pub use voice::{State,Parameters,Controls,Workspace,Accepted,Pair,N,M,B};
use crate::StepError;
pub struct Initial{pub state:State,pub iterations:usize,pub residual_a:f64,pub correction_v:f64}
fn max<const K:usize>(v:[f64;K])->f64{v.into_iter().fold(0_f64,|a,b|a.max(b.abs()))}
fn direction(p:Parameters,x:State)->Result<([f64;N],[f64;N]),StepError>{
    let zero=State::new([0.;N],false);let s=voice::parts::<true>(p,x,zero,Controls::default(),1e-6,0.)?;
    if s.dq.iter().any(|v|*v!=0.){return Err(StepError::InvalidInput);}
    let mut j=[[0.;N];N];for a in 0..N{for(b,g,_)in s.tangent.entries(a){j[a][b]=g;}}
    let d=rf_d_circuit::block_decay_voice::solve_linear_extent(j,s.dc.map(|v|-v))?;Ok((s.dc,d))
}
pub fn initialize(p:Parameters,guess:State,budget:usize)->Result<Initial,StepError>{
    if p.time!=0.||!guess.valid()||guess.optional||budget==0||budget>100{return Err(StepError::InvalidInput);}
    let mut x=guess;
    for iteration in 1..=budget{
        let(r,d)=direction(p,x)?;let residual=max(r);let correction=max(d);
        if residual<=1e-12&&correction<=2e-9{return Ok(Initial{state:x,iterations:iteration,residual_a:residual,correction_v:correction});}
        let mut accepted=false;
        for power in 0..28{let trial=x.advanced(d.map(|v|v*2_f64.powi(-power)));
            if let Ok((rr,dd))=direction(p,trial){let next=max(rr);if next<residual||(residual<=1e-12&&next<=1e-12&&max(dd)<correction){x=trial;accepted=true;break;}}
        }if !accepted{return Err(StepError::NoDecrease);}
    }Err(StepError::IterationBudget)
}

/// Numerical guesses only, never a capacitor reset policy or an audible recipe.
/// Sources: mixer_chain_lab::SEED; loudness_contour_reference::initial_state;
/// c5_trigger_reference::dc_seed. The complete root is solved again jointly.
pub fn numerical_guess(p:rf_d_circuit::chain_charge::Parameters,variant:usize)->Result<State,StepError>{
    if variant>1{return Err(StepError::InvalidInput);}Parameters::new(p)?;
    let ladder=[7.8431017460109675,6.372499040594479,4.9019061730679665,3.43132324181033,1.9607503461842566,1.4561733893906676,1.9607344627142946,1.9607223099167141,2.9270178181494293,4.397856399069791,5.868704916259031,7.339563271338244,2.927029970947009,4.397868551867372,5.868717069056611,7.339575424135825];
    let audio=rf_d_circuit::circuit66::initial_state(p.circuit,p.conversion,p.headphone,p.boundary,ladder)?;
    let vol=[0.1,-0.5,9.3,-1.,-3.6,0.7,9.2,0.,0.,8.,1.3,0.7,5.,4.,0.6,0.01,0.05,0.05,9.,0.7,0.,0.,0.,0.,0.9,0.,8.7,0.7,0.05];
    let filter=[0.3,8.75,9.25,0.,-2.,0.005,0.52,-9.998,1.39];let timer=[0.85,0.01,8.3,0.7,0.03,9.15,0.85,7.6,1.,0.85,0.7,4.8,0.001,5.,0.03,1.1];
    let mut x=[0.;N];x[..29].copy_from_slice(&vol);x[29..38].copy_from_slice(&filter);x[38..54].copy_from_slice(&timer);
    for k in 0..66{if(62..66).contains(&k){continue;}let i=match k{5=>55,32=>54,_=>56+k-(k>5)as usize-(k>32)as usize};x[i]=audio.node_v[k];}
    x[116]=0.;x[117]=audio.node_v[22];if variant==1{for k in 0..54{x[k]+=if k%2==0{0.005}else{-0.005};}}
    Ok(State::new(x,false))
}
/// Self-contained nominal setup. No file, reserved trajectory or caller seed.
pub fn cold_start(raw:rf_d_circuit::chain_charge::Parameters)->Result<Initial,StepError>{
    let p=Parameters::new(raw)?;initialize(p,numerical_guess(raw,0)?,100)
}
