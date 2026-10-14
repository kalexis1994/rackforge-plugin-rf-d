//! Simultaneous nominal VCO1 -> BUS -> dual contours/ladder/VCAs/J7.
//! Experimental fixed scene; VOZ_DOS_CONTORNOS_PROTOCOLO.
use crate::StepError;
use rf_d_circuit::{vco1_stamp::{self,Controls,Mode},chain_charge};
#[path="dual_voice_chain.rs"] mod chain;
#[path="dual_voice_solver.rs"] pub mod solver;
#[path="../../../tools/assembly_vco_helper.rs"] mod fine;
pub const N:usize=250;
pub const M:usize=500;
pub const B:[[f64;2];2]=rf_d_circuit::vco1_radau::B;
pub const MIN_DT_S:f64=chain_charge::MIN_DT_S;
pub const fn vi(k:usize)->Option<usize>{if k==108{None}else if k<108{Some(k)}else{Some(k-1)}}
pub const fn di(k:usize)->usize{if k==116{12}else if k<116{133+k}else{249}}
pub const fn ci(k:usize)->usize{di(chain::chain_index(k))}
#[derive(Clone,Copy)]
pub struct Parameters{pub controls:Controls,chain:chain::Parameters,pub key:f64}
impl Parameters{
    pub fn new(p:chain_charge::Parameters)->Result<Self,StepError>{Ok(Self{controls:Controls::default(),chain:chain::Parameters::new(p)?,key:0.})}
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct State{pub high:[f64;N],pub low:[f64;N]}
impl State{
    pub fn new(high:[f64;N])->Self{Self{high,low:[0.;N]}}
    pub fn advanced(self,d:[f64;N])->Self{let mut s=self;for k in 0..N{let(h,e)=fine::two_sum(s.high[k],d[k]);let(l,f)=fine::two_sum(s.low[k],e);let(h,l)=fine::two_sum(h,l);(s.high[k],s.low[k])=fine::two_sum(h,l+f);}s}
    fn vco(self)->fine::State{fine::State{high:std::array::from_fn(|k|vi(k).map_or(0.,|i|self.high[i])),low:std::array::from_fn(|k|vi(k).map_or(0.,|i|self.low[i]))}}
    fn dual(self)->chain::State{chain::State{high:std::array::from_fn(|k|self.high[di(k)]),low:std::array::from_fn(|k|self.low[di(k)]),optional:false}}
}
pub struct Parts{pub dc:[f64;N],pub charge_over_h:[f64;N],pub dc_jacobian:[[f64;N];N],pub mass_over_h:[[f64;N];N],pub candidate:State}
pub fn parts(p:Parameters,old:State,delta:State,h:f64)->Result<Parts,StepError>{
    if !p.key.is_finite()||!(0. ..=10.).contains(&p.key){return Err(StepError::InvalidInput);}
    let e=fine::linearize_compensated(old.vco(),delta.vco(),p.controls,h).map_err(|_|StepError::InvalidInput)?;
    let d=vco1_stamp::linearize(e.candidate.high,p.controls,Mode::Dc).map_err(|_|StepError::InvalidInput)?;
    let c=chain::parts(p.chain,old.dual(),delta.dual(),chain::Controls{key:p.key,short:false,optional:false},h,0.)?;
    let now=old.advanced(delta.high).advanced(delta.low);
    let mut s=Parts{dc:[0.;N],charge_over_h:[0.;N],dc_jacobian:[[0.;N];N],mass_over_h:[[0.;N];N],candidate:now};
    for a in 0..134{if let Some(i)=vi(a){
        let f=d.residual[a]+(0..134).map(|b|d.jacobian[a][b]*e.candidate.low[b]).sum::<f64>();
        s.dc[i]+=f;s.charge_over_h[i]+=e.residual[a]-f;
        for b in 0..134{if let Some(j)=vi(b){s.dc_jacobian[i][j]+=d.jacobian[a][b];s.mass_over_h[i][j]+=e.jacobian[a][b]-d.jacobian[a][b];}}
    }}
    for a in 0..118{let i=di(a);s.dc[i]+=c.dc[a];s.charge_over_h[i]+=c.dq[a];for b in 0..118{let j=di(b);s.dc_jacobian[i][j]+=c.j[a][b];s.mass_over_h[i][j]+=c.mass[a][b];}}
    if s.dc.iter().chain(s.charge_over_h.iter()).chain(s.dc_jacobian.iter().flatten()).chain(s.mass_over_h.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}Ok(s)
}
fn current_unknown(k:usize)->bool{(98..133).contains(&k)}
fn merit(r:&[f64],dc:bool)->f64{r.iter().enumerate().fold(0_f64,|a,(i,v)|a.max(v.abs()/if current_unknown(i%N)||(dc&&i==43){1e-11}else{1e-13}))}
fn correction(d:&[f64])->f64{d.iter().enumerate().fold(0_f64,|a,(k,v)|a.max(v.abs()/if current_unknown(k%N){2e-12}else{2e-9}))}
pub struct Initial{pub state:State,pub forcing_a:f64,pub iterations:usize,pub residual_ratio:f64,pub correction_ratio:f64}
pub fn initial(p:Parameters,seed:State)->Result<Initial,StepError>{
    let system=|x:State|->Result<([f64;N],[[f64;N];N],f64),StepError>{let s=parts(p,x,State::new([0.;N]),125e-9)?;let mut r=s.dc;let mut j=s.dc_jacobian;let forcing=-r[43];r[43]=x.high[43]+x.low[43];j[43]=[0.;N];j[43][43]=1.;Ok((r,j,forcing))};
    let mut x=seed;
    for iteration in 1..=80{
        let(r,j,forcing)=system(x)?;let d=rf_d_circuit::block_decay_voice::solve_linear_sparse(j,r.map(|v|-v))?;let norm=merit(&r,true);let corr=correction(&d);
        if norm<=1.&&corr<=1.{return Ok(Initial{state:x,forcing_a:forcing,iterations:iteration,residual_ratio:norm,correction_ratio:corr});}
        let mut found=false;
        for power in 0..24{let trial=x.advanced(d.map(|v|v*2_f64.powi(-power)));if let Ok((rr,jj,_))=system(trial){let nd=rf_d_circuit::block_decay_voice::solve_linear_sparse(jj,rr.map(|v|-v))?;let next=merit(&rr,true);if next<norm || (norm<=1.&&next<=1.&&correction(&nd)<corr){x=trial;found=true;break;}}}
        if !found{return Err(StepError::NoDecrease);}
    }Err(StepError::IterationBudget)
}
pub struct Stamp{pub residual:[f64;M],pub jacobian:[[f64;M];M],pub stages:[State;2]}
impl Stamp{
    const fn blank()->Self{Self{residual:[0.;M],jacobian:[[0.;M];M],stages:[State{high:[0.;N],low:[0.;N]};2]}}
    fn initialize(&mut self,p:Parameters,old:State,delta:[State;2],h:f64)->Result<(),StepError>{
        let q=[parts(p,old,delta[0],h)?,parts(p,old,delta[1],h)?];
        for i in 0..2{for a in 0..N{self.residual[i*N+a]=q[i].dc[a]+B[i][0]*q[0].charge_over_h[a]+B[i][1]*q[1].charge_over_h[a];for j in 0..2{for b in 0..N{self.jacobian[i*N+a][j*N+b]=B[i][j]*q[j].mass_over_h[a][b]+if i==j{q[i].dc_jacobian[a][b]}else{0.};}}}}
        self.stages=[q[0].candidate,q[1].candidate];Ok(())
    }
}
pub struct Pair{pub delta:[State;2],pub stages:[State;2],pub residual_ratio:f64,pub correction_ratio:f64,pub iterations:usize}
pub struct Workspace{first:Stamp,second:Stamp}
impl Workspace{
    pub const fn new()->Self{Self{first:Stamp::blank(),second:Stamp::blank()}}
    pub fn step(&mut self,p:Parameters,old:State,h:f64)->Result<Pair,StepError>{
        let mut seed=[0.;N];let key_node=di(22);if p.key-old.high[key_node]-old.low[key_node]>0.5{seed[key_node]=p.key-0.5-old.high[key_node]-old.low[key_node];}
        let mut delta=[State::new(seed);2];let(mut s,mut t)=(&mut self.first,&mut self.second);
        s.initialize(p,old,delta,h)?;let mut d=solver::solve(s.jacobian,s.residual.map(|v|-v))?;
        for iteration in 1..=80{
            let norm=merit(&s.residual,false);let corr=correction(&d);
            if norm<=1.&&corr<=1.{return Ok(Pair{delta,stages:s.stages,residual_ratio:norm,correction_ratio:corr,iterations:iteration});}
            let mut found=None;
            for power in 0..24{let alpha=2_f64.powi(-power);let trial=std::array::from_fn(|i|delta[i].advanced(std::array::from_fn(|k|alpha*d[i*N+k])));
                if t.initialize(p,old,trial,h).is_ok(){if let Ok(nd)=solver::solve(t.jacobian,t.residual.map(|v|-v)){let next=merit(&t.residual,false);if next<norm*(1.-1e-4*alpha)||(norm<=1.&&next<=1.&&correction(&nd)<corr){found=Some((trial,nd));break;}}}
            }
            match found{Some((trial,nd))=>{delta=trial;std::mem::swap(&mut s,&mut t);d=nd;},None=>return Err(StepError::NoDecrease)}
        }Err(StepError::IterationBudget)
    }
}
pub struct Accepted{pub coarse:Pair,pub fine:[Pair;2],pub full_ticks:u32,pub error:f64}
pub fn advance(w:&mut Workspace,p:Parameters,state:&mut State,mut ticks:u32)->Result<Accepted,StepError>{
    if ticks<8||!ticks.is_power_of_two(){return Err(StepError::InvalidInput);}
    let old=*state;
    for _ in 0..20{
        let h=ticks as f64*rf_d_circuit::vco1_engine::TICK_S;
        let trial=(||{let coarse=w.step(p,old,h)?;let a=w.step(p,old,h/2.)?;let b=w.step(p,a.stages[1],h/2.)?;let end=b.stages[1];
            let error=(0..N).fold(0_f64,|m,k|m.max(((coarse.stages[1].high[k]-end.high[k])+(coarse.stages[1].low[k]-end.low[k])).abs()/if current_unknown(k){2e-9}else if k<133{2e-6}else{2e-7+2e-7*end.high[k].abs()}));
            Ok::<_,StepError>((coarse,[a,b],error))})();
        if let Ok((coarse,fine,error))=trial{if error<=1.{*state=fine[1].stages[1];return Ok(Accepted{coarse,fine,full_ticks:ticks,error});}}
        if ticks==8{return Err(StepError::IterationBudget);}ticks/=2;
    }Err(StepError::IterationBudget)
}
pub fn loads(s:State)->[f64;2]{chain::currents(s.dual())}
pub fn bus_balance(q:&Pair,h:f64)->f64{
    let s=q.stages[1];let series=(s.high[12]+s.low[12]-s.high[39]-s.low[39])/33000.;
    let cap=10e-6/h*(B[1][0]*(q.delta[0].high[12]+q.delta[0].low[12]-q.delta[0].high[ci(6)]-q.delta[0].low[ci(6)])+B[1][1]*(q.delta[1].high[12]+q.delta[1].low[12]-q.delta[1].high[ci(6)]-q.delta[1].low[ci(6)]));series+cap
}
