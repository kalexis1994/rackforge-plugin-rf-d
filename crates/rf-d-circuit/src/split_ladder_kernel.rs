//! Local, charge-preserving ladder reconstruction. Not yet wired into the voice.
//! Units, ownership and gates: docs/LADDER_ALGEBRAICO_PROTOCOLO.md.
use rf_d_circuit::{StepError, vco1_increment::two_sum};
#[path="ladder_algebraic_stamp.rs"] pub mod stamp;
pub const NZ:usize=7;
pub const NY:usize=9;
pub const OWNED_CAPACITORS:[(usize,usize,f64);5]=[
    (8,12,68e-9),(9,13,68e-9),(10,14,68e-9),(11,15,68e-9),(4,16,220e-6)];
pub const Z_NODES:[usize;NZ]=[0,1,2,3,8,9,10];
pub const PORT_NODES:[usize;5]=[5,6,7,11,15];
pub const MIN_DT_S:f64=4.*rf_d_circuit::vco1_engine::TICK_S;
pub fn add_pair(h:f64,l:f64,d:f64)->(f64,f64){
    let(s,e)=two_sum(h,d);let(t,f)=two_sum(l,e);let(u,v)=two_sum(s,t);two_sum(u,v+f)
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct PairState<const N:usize>{pub high:[f64;N],pub low:[f64;N]}
impl<const N:usize> PairState<N>{
    pub fn valid(self)->bool{(0..N).all(|k|self.high[k].is_finite()&&self.low[k].is_finite()
        &&two_sum(self.high[k],self.low[k])==(self.high[k],self.low[k]))}
    pub fn advanced(self,d:[f64;N])->Self{
        let mut out=self;for k in 0..N{(out.high[k],out.low[k])=add_pair(self.high[k],self.low[k],d[k]);}out
    }
}
pub type Nodes=PairState<16>;
pub type Algebraic=PairState<NZ>;
pub type Retained=PairState<NY>;
fn difference(x:Nodes,a:usize,b:usize)->(f64,f64){
    let(h,l)=add_pair(x.high[a],x.low[a],-x.high[b]);add_pair(h,l,-x.low[b])
}
fn physical(x:Nodes)->bool{x.valid()&&(0..16).all(|k|x.high[k].abs()<=40.
    &&(x.high[k].abs()!=40.||x.high[k]*x.low[k]<=0.))}
pub fn coordinates(x:Nodes)->Result<(Algebraic,Retained),StepError>{
    if !physical(x){return Err(StepError::InvalidInput);}
    let z=Algebraic{high:Z_NODES.map(|k|x.high[k]),low:Z_NODES.map(|k|x.low[k])};
    let mut y=Retained{high:[0.;NY],low:[0.;NY]};
    for k in 0..3{(y.high[k],y.low[k])=difference(x,8+k,12+k);}
    for(k,n)in[4,5,6,7,11,15].into_iter().enumerate(){y.high[3+k]=x.high[n];y.low[3+k]=x.low[n];}
    Ok((z,y))
}
pub fn reconstruct(z:Algebraic,y:Retained)->Result<Nodes,StepError>{
    if !z.valid()||!y.valid(){return Err(StepError::InvalidInput);}
    let mut x=Nodes{high:[0.;16],low:[0.;16]};
    for(k,n)in Z_NODES.into_iter().enumerate(){x.high[n]=z.high[k];x.low[n]=z.low[k];}
    for(k,n)in[4,5,6,7,11,15].into_iter().enumerate(){x.high[n]=y.high[3+k];x.low[n]=y.low[3+k];}
    for k in 0..3{
        let(h,l)=add_pair(z.high[4+k],z.low[4+k],-y.high[k]);
        (x.high[12+k],x.low[12+k])=add_pair(h,l,-y.low[k]);
    }
    if !physical(x){return Err(StepError::InvalidInput);}Ok(x)
}
/// x=T*[z,y]. The congruence T^t*J*T preserves physical work and charge.
pub const T:[[f64;16];16]={
    let mut t=[[0.;16];16];let mut k=0;
    while k<7{t[Z_NODES[k]][k]=1.;k+=1;}
    t[4][10]=1.;t[5][11]=1.;t[6][12]=1.;t[7][13]=1.;t[11][14]=1.;t[15][15]=1.;
    k=0;while k<3{t[12+k][4+k]=1.;t[12+k][7+k]=-1.;k+=1;}t
};
// Immutable support of the declared coordinate transformation, never learned from a scene.
const SUPPORT:[[(usize,f64);2];16]={let mut out=[[(16,0.);2];16];let mut i=0;
    while i<16{let mut a=0;let mut n=0;while a<16{if T[a][i]!=0.{out[i][n]=(a,T[a][i]);n+=1;}a+=1;}i+=1;}out};
pub fn covector(f:&[f64;16])->[f64;16]{std::array::from_fn(|i|{
    let mut v=0.;for(a,s)in SUPPORT[i]{if a<16{v+=s*f[a];}}v
})}
pub fn congruence(j:&[[f64;16];16])->[[f64;16];16]{
    let right:[[f64;16];16]=std::array::from_fn(|a|std::array::from_fn(|i|{
        let mut v=0.;for(b,s)in SUPPORT[i]{if b<16{v+=j[a][b]*s;}}v
    }));
    std::array::from_fn(|i|std::array::from_fn(|k|{
        let mut v=0.;for(a,s)in SUPPORT[i]{if a<16{v+=s*right[a][k];}}v
    }))
}
#[derive(Clone,Copy)]
pub struct Model{parameters:stamp::Parameters}
impl Model{
    pub fn new(p:stamp::Parameters)->Result<Self,StepError>{
        let b=p.ladder_transistor;
        if [b.transistor_is_a,b.beta_forward,b.beta_reverse,b.temperature_k].iter().any(|v|!v.is_finite()||*v<=0.)
            ||![200.,200000.].contains(&p.r61_ohm)||!p.r30_ohm.is_finite()||!(330. ..=1330.).contains(&p.r30_ohm){return Err(StepError::InvalidInput);}
        Ok(Self{parameters:p})
    }
    pub fn evaluate(self,z:Algebraic,y:Retained)->Result<Evaluation,StepError>{
        let nodes=reconstruct(z,y)?;let s=stamp::linearize(self.parameters,&nodes.high,&nodes.low)?;
        let f=covector(&s.dc);let j=congruence(&s.j);
        Ok(Evaluation{nodes,f,j,dc:s.dc,physical_j:s.j,source:s.fixed,source_j:std::array::from_fn(|r|std::array::from_fn(|i|(0..16).map(|a|s.fixed_j[r][a]*T[a][i]).sum()))})
    }
    /// Transactional: all inputs are values; failure publishes no state or factor.
    pub fn solve(self,y:Retained,seed:Algebraic,budget:Budget)->Result<Solution,StepError>{
        if budget.iterations==0||budget.iterations>80||budget.backtracks==0||budget.backtracks>24{return Err(StepError::InvalidInput);}
        let mut z=seed;
        for iteration in 0..budget.iterations{
            let e=self.evaluate(z,y)?;let factor=Factor::new(std::array::from_fn(|i|std::array::from_fn(|k|e.j[i][k])))?;
            let d=factor.solve(std::array::from_fn(|i|-e.f[i]))?;
            let residual=e.f[..NZ].iter().fold(0_f64,|a,v|a.max(v.abs()));
            let correction=d.iter().fold(0_f64,|a,v|a.max(v.abs()));
            if residual<=1e-12&&correction<=2e-9{return finish(z,e,factor,iteration+1,residual,correction);}
            let mut alpha=1.;let mut accepted=None;
            for _ in 0..budget.backtracks{
                let trial=z.advanced(d.map(|v|alpha*v));
                if let Ok(next)=self.evaluate(trial,y){
                    let r=next.f[..NZ].iter().fold(0_f64,|a,v|a.max(v.abs()));
                    if r<residual||r<=1e-12{accepted=Some(trial);break;}
                }
                alpha*=0.5;
            }
            z=accepted.ok_or(StepError::NoDecrease)?;
        }
        Err(StepError::IterationBudget)
    }
}
pub struct Evaluation{pub dc:[f64;16],pub physical_j:[[f64;16];16],pub nodes:Nodes,pub f:[f64;16],pub j:[[f64;16];16],pub source:[f64;2],pub source_j:[[f64;16];2]}
#[derive(Clone,Copy)]pub struct Budget{pub iterations:usize,pub backtracks:usize}
impl Default for Budget{fn default()->Self{Self{iterations:80,backtracks:24}}}
pub struct Solution{
    pub dc:[f64;16],pub physical_j:[[f64;16];16],
    pub z:Algebraic,pub nodes:Nodes,pub reaction:[f64;NY],pub reaction_j:[[f64;NY];NY],
    pub source:[f64;2],pub source_j:[[f64;NY];2],pub dz_dy:[[f64;NY];NZ],
    pub iterations:usize,pub residual_a:f64,pub correction_v:f64,
}
fn finish(z:Algebraic,e:Evaluation,factor:Factor,iterations:usize,residual_a:f64,correction_v:f64)->Result<Solution,StepError>{
    let mut dz_dy=[[0.;NY];NZ];
    for y in 0..NY{let d=factor.solve(std::array::from_fn(|k|-e.j[k][NZ+y]))?;for k in 0..NZ{dz_dy[k][y]=d[k];}}
    let reaction_j=std::array::from_fn(|i|std::array::from_fn(|y|e.j[NZ+i][NZ+y]+(0..NZ).map(|k|e.j[NZ+i][k]*dz_dy[k][y]).sum::<f64>()));
    let source_j=std::array::from_fn(|i|std::array::from_fn(|y|e.source_j[i][NZ+y]+(0..NZ).map(|k|e.source_j[i][k]*dz_dy[k][y]).sum::<f64>()));
    if dz_dy.iter().flatten().chain(reaction_j.iter().flatten()).chain(source_j.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}
    Ok(Solution{dc:e.dc,physical_j:e.physical_j,z,nodes:e.nodes,reaction:std::array::from_fn(|i|e.f[NZ+i]),reaction_j,source:e.source,source_j,dz_dy,iterations,residual_a,correction_v})
}
/// Fixed storage, scaled partial pivoting; local to this Jacobian and recipe.
pub struct Factor{a:[[f64;NZ];NZ],permutation:[usize;NZ]}
impl Factor{
    pub fn new(mut a:[[f64;NZ];NZ])->Result<Self,StepError>{
        if a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
        let mut scale=a.map(|r|r.iter().fold(0_f64,|s,v|s.max(v.abs())));
        if scale.contains(&0.){return Err(StepError::SingularJacobian);}
        let mut permutation=std::array::from_fn(|k|k);
        for k in 0..NZ{
            let mut pivot=k;let mut best=0.;for i in k..NZ{let r=a[i][k].abs()/scale[i];if r>best{best=r;pivot=i;}}
            if best<1e-12{return Err(StepError::SingularJacobian);}
            a.swap(k,pivot);scale.swap(k,pivot);permutation.swap(k,pivot);
            for i in k+1..NZ{a[i][k]/=a[k][k];for j in k+1..NZ{a[i][j]-=a[i][k]*a[k][j];}}
        }
        if a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(Self{a,permutation})
    }
    pub fn solve(&self,b:[f64;NZ])->Result<[f64;NZ],StepError>{
        if b.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
        let mut x=self.permutation.map(|k|b[k]);
        for i in 0..NZ{for j in 0..i{x[i]-=self.a[i][j]*x[j];}}
        for i in(0..NZ).rev(){for j in i+1..NZ{x[i]-=self.a[i][j]*x[j];}x[i]/=self.a[i][i];}
        if x.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(x)
    }
}
pub struct Charge{pub current_a:[f64;NY],pub mass_s:[[f64;NY];NY],pub ground_a:f64}
/// Original, compensated physical increment. Never subtract rounded endpoints.
pub fn charge(delta:Nodes,h:f64)->Result<Charge,StepError>{
    if !delta.valid()||!h.is_finite()||!(MIN_DT_S..=1e-3).contains(&h){return Err(StepError::InvalidInput);}
    let mut current_a=[0.;NY];let mut mass_s=[[0.;NY];NY];
    for k in 0..3{let(a,b)=difference(delta,8+k,12+k);let g=68e-9/h;current_a[k]=g*(a+b);mass_s[k][k]=g;}
    let bias=220e-6/h;current_a[3]=bias*(delta.high[4]+delta.low[4]);mass_s[3][3]=bias;
    let(a,b)=difference(delta,11,15);let g=68e-9/h;let i=g*(a+b);current_a[7]=i;current_a[8]=-i;
    for(a,sa)in[(7,1.),(8,-1.)]{for(b,sb)in[(7,1.),(8,-1.)]{mass_s[a][b]=sa*sb*g;}}
    if current_a.iter().chain(mass_s.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
    Ok(Charge{current_a,mass_s,ground_a:-current_a[3]})
}
