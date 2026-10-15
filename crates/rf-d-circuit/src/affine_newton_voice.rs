//! Nonlinear ladder reconstruction inside the complete two-stage voice.
//! Experimental integration; admission is recorded in LADDER_VOZ_RESULTADOS.
use crate::StepError;
#[path="direct_hybrid_voice.rs"] pub mod full;
#[path="split_ladder_kernel.rs"] pub mod ladder;
#[path="split_parent_voice.rs"] pub mod parent;
#[path="split_ladder_binding.rs"] pub mod binding;
#[path="affine_newton_solver.rs"] pub mod solver;
#[path="affine_newton_frame.rs"] pub mod affine;
pub use full::{State,Controls,Parts,N,M,B,currents,Pair,Accepted};
pub const R:usize=111;
pub const RM:usize=2*R;
pub const LOCAL:[usize;16]=[56,57,58,59,60,55,61,62,63,64,65,66,67,68,69,70];
pub const Z:[usize;7]=[56,57,58,59,63,64,65];
pub const RETAINED:[usize;R]={let mut out=[0;R];let mut i=0;let mut a=0;while a<N{
    if !(a>=56&&a<=59||a>=63&&a<=65){out[i]=a;i+=1;}a+=1;}out};
pub const Y:[usize;9]={let physical=[67,68,69,60,55,61,62,66,70];let mut ids=[0;9];let mut k=0;
    while k<9{let mut i=0;while RETAINED[i]!=physical[k]{i+=1;}ids[k]=i;k+=1;}ids};
pub type Reduced=ladder::PairState<R>;
fn sign(a:usize)->f64{if (67..=69).contains(&a){-1.}else{1.}}
#[derive(Clone,Copy)]
pub struct Parameters{parent:parent::Parameters,full:full::Parameters,model:ladder::Model,pub time:f64}
impl Parameters{
    pub fn new(p:rf_d_circuit::chain_charge::Parameters)->Result<Self,StepError>{
        Ok(Self{parent:parent::Parameters::new(p)?,model:ladder::Model::new(p.circuit)?,full:full::Parameters::new(p)?,time:0.})
    }
    fn physical(self)->full::Parameters{let mut p=self.full;p.time=self.time;p}
}
pub fn parts<const FULL:bool>(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{
    full::parts::<FULL>(p.physical(),old,delta,c,h,t)
}
pub fn coordinates(state:State)->Result<(ladder::Algebraic,Reduced),StepError>{
    if !state.valid(){return Err(StepError::InvalidInput);}
    let local=ladder::Nodes{high:LOCAL.map(|k|state.high[k]),low:LOCAL.map(|k|state.low[k])};
    let(z,y)=ladder::coordinates(local)?;
    let mut retained=Reduced{high:RETAINED.map(|k|state.high[k]),low:RETAINED.map(|k|state.low[k])};
    for k in 0..3{retained.high[Y[k]]=y.high[k];retained.low[Y[k]]=y.low[k];}Ok((z,retained))
}
pub fn increment(now:State,old:State)->Reduced{
    let mut d=Reduced{high:[0.;R],low:[0.;R]};
    let(_,a)=coordinates(now).unwrap();let(_,b)=coordinates(old).unwrap();
    for k in 0..R{let(h,l)=ladder::add_pair(a.high[k],a.low[k],-b.high[k]);(d.high[k],d.low[k])=ladder::add_pair(h,l,-b.low[k]);}d
}
pub struct Stage{pub physical:Parts,pub delta:State,pub local:ladder::Solution}
pub fn evaluate<const FULL:bool>(p:Parameters,old:State,d:Reduced,c:Controls,h:f64,t:f64)->Result<Stage,StepError>{
    if !d.valid(){return Err(StepError::InvalidInput);}
    let(seed,previous)=coordinates(old)?;let retained=previous.advanced(d.high).advanced(d.low);
    let y=ladder::Retained{high:Y.map(|k|retained.high[k]),low:Y.map(|k|retained.low[k])};
    let local=p.model.solve(y,seed,ladder::Budget::default())?;
    let mut delta=State::new([0.;N],old.optional);
    for k in 0..R{if !(67..=69).contains(&RETAINED[k]){delta.high[RETAINED[k]]=d.high[k];delta.low[RETAINED[k]]=d.low[k];}}
    for k in 0..7{let(h,l)=ladder::add_pair(local.z.high[k],local.z.low[k],-seed.high[k]);(delta.high[Z[k]],delta.low[Z[k]])=ladder::add_pair(h,l,-seed.low[k]);}
    for k in 0..3{let(h,l)=ladder::add_pair(delta.high[Z[4+k]],delta.low[Z[4+k]],-d.high[Y[k]]);
        (delta.high[67+k],delta.low[67+k])=ladder::add_pair(h,l,-d.low[Y[k]]);}
    let mut physical=binding::parent_parts::<FULL>(p.parent,p.time,old,delta,c,h,t)?;
    binding::validate_parent::<FULL>(&physical)?;
    binding::merge::<FULL>(&mut physical,&local)?;
    Ok(Stage{physical,delta,local})
}
pub fn project(r:[f64;M])->[f64;RM]{std::array::from_fn(|k|sign(RETAINED[k%R])*r[(k/R)*N+RETAINED[k%R]])}
fn norm<const S:usize>(a:[f64;S])->f64{a.into_iter().fold(0_f64,|m,v|m.max(v.abs()))}
pub fn residual(s:&[Stage;2])->[f64;M]{std::array::from_fn(|k|{let a=k%N;let i=k/N;
    s[i].physical.dc[a]+B[i][0]*s[0].physical.dq[a]+B[i][1]*s[1].physical.dq[a]})}
pub fn reconstruct_direction(s:&[Stage;2],d:[f64;RM])->[f64;M]{
    let mut result=[0.;M];for stage in 0..2{
        for k in 0..R{result[stage*N+RETAINED[k]]=sign(RETAINED[k])*d[stage*R+k];}
        for k in 0..7{let a=(0..9).map(|y|s[stage].local.dz_dy[k][y]*d[stage*R+Y[y]]).sum::<f64>();
            result[stage*N+Z[k]]=a;if k>=4{result[stage*N+67+k-4]+=a;}}
    }result
}
pub struct Workspace{
    pub reduced:solver::Workspace,pub statistics:solver::Statistics,pub affine_statistics:affine::Statistics,
    dc:[[[f64;R];R];2],mass:[[[f64;R];R];2],physical:affine::Sparse,
    #[cfg(laboratory)]pub original:full::Workspace,
}
impl Workspace{
    pub const fn new()->Self{Self{reduced:solver::Workspace::new(),statistics:solver::Statistics{solves:0,refinements:0,max_initial_backward:0.,max_final_backward:0.,max_nonzeros:0},affine_statistics:affine::Statistics::new(),dc:[[[0.;R];R];2],mass:[[[0.;R];R];2],physical:affine::Sparse::new(),#[cfg(laboratory)]original:full::Workspace::new()}}
    pub fn prepare<'w,'s>(&'w mut self,s:&'s[Stage;2])->Result<affine::Frame<'w,'s>,StepError>{
        self.physical.initialize(s,B)?;
        let local=[affine::Local::new(&s[0].physical.j,&s[0].physical.mass)?,affine::Local::new(&s[1].physical.j,&s[1].physical.mass)?];
        for i in 0..2{local[i].coefficients(&s[i].physical.j,&s[i].physical.mass,&mut self.dc[i],&mut self.mass[i])?;}
        let reduced=self.reduced.prepare([solver::Stage{dc:&self.dc[0],mass:&self.mass[0]},solver::Stage{dc:&self.dc[1],mass:&self.mass[1]}],B)?;
        Ok(affine::Frame::new(reduced,local,&self.physical,s,&mut self.affine_statistics))
    }
}
pub fn direction(w:&mut Workspace,s:&[Stage;2],rhs:[f64;M])->Result<([f64;RM],[f64;M]),StepError>{
    let result={let mut prepared=w.prepare(s)?;prepared.solve(rhs)};w.statistics=w.reduced.statistics;result
}
#[cfg(laboratory)]
pub fn original_direction(w:&mut Workspace,s:&[Stage;2],rhs:[f64;M])->Result<[f64;M],StepError>{
    w.original.solve([full::solver::Stage{dc:&s[0].physical.j,mass:&s[0].physical.mass},full::solver::Stage{dc:&s[1].physical.j,mass:&s[1].physical.mass}],B,rhs)
}
pub fn radau(w:&mut Workspace,p:Parameters,old:State,c:Controls,h:f64,budget:usize)->Result<Pair,StepError>{
    if budget==0||budget>80{return Err(StepError::InvalidInput);}
    let mut d=[Reduced{high:[0.;R],low:[0.;R]};2];
    if c.key-old.high[22]-old.low[22]>0.5{for stage in &mut d{stage.high[22]=c.key-0.5-old.high[22]-old.low[22];}}
    let evaluate_pair=|d:[Reduced;2]|->Result<[Stage;2],StepError>{Ok([evaluate::<true>(p,old,d[0],c,h,p.time+h/3.)?,evaluate::<true>(p,old,d[1],c,h,p.time+h)?])};
    let fast_residual=|d:[Reduced;2]|->Result<[f64;M],StepError>{let s=[evaluate::<false>(p,old,d[0],c,h,p.time+h/3.)?,evaluate::<false>(p,old,d[1],c,h,p.time+h)?];Ok(residual(&s))};
    for iteration in 1..=budget{
        let s=evaluate_pair(d)?;let r=residual(&s);let magnitude=norm(r);
        let(dy,dx)=direction(w,&s,r.map(|v|-v))?;let correction=norm(dx);
        if magnitude<=1e-12&&correction<=2e-9{return Ok(Pair{delta:[s[0].delta,s[1].delta],stages:[s[0].physical.now,s[1].physical.now],residual_a:magnitude,correction_v:correction,iterations:iteration});}
        let mut found=false;
        for backtrack in 0..24{
            let scale=2_f64.powi(-backtrack);let trial=std::array::from_fn(|i|d[i].advanced(std::array::from_fn(|k|scale*dy[i*R+k])));
            let merit=if magnitude<=1e-12{
                if let Ok(ss)=evaluate_pair(trial){let rr=residual(&ss);let next=norm(rr);let weak=next<=1e-12&&norm(direction(w,&ss,rr.map(|v|-v))?.1)<correction;Some((next,weak))}else{None}
            }else{fast_residual(trial).ok().map(|rr|(norm(rr),false))};
            if let Some((next,weak))=merit{if next<magnitude||weak{d=trial;found=true;break;}}
        }
        if !found{return Err(StepError::NoDecrease);}
    }Err(StepError::IterationBudget)
}
pub fn advance(w:&mut Workspace,p:Parameters,state:&mut State,c:Controls,mut h:f64)->Result<Accepted,StepError>{
    let old=*state;
    if !h.is_finite()||h<=0.||h>1e-3||!old.valid()||old.optional!=c.optional{return Err(StepError::InvalidInput);}
    for attempt in 1..=32{
        let trial=(||{
            let coarse=radau(w,p,old,c,h,80)?;let a=radau(w,p,old,c,h/2.,80)?;
            let mut next=p;next.time+=h/2.;let b=radau(w,next,a.stages[1],c,h/2.,80)?;let fine=b.stages[1];
            let error=(0..N).fold(0_f64,|m,k|m.max(((coarse.stages[1].high[k]-fine.high[k])+(coarse.stages[1].low[k]-fine.low[k])).abs()/(500e-6+1e-4*fine.high[k].abs())));
            Ok::<_,StepError>((coarse,[a,b],error))
        })();
        if let Ok((coarse,fine,error))=trial{if error<=1.{*state=fine[1].stages[1];return Ok(Accepted{coarse,fine,h,error,attempts:attempt});}}
        h*=0.5;if h/2.<rf_d_circuit::chain_charge::MIN_DT_S{return Err(StepError::IterationBudget);}
    }Err(StepError::IterationBudget)
}
