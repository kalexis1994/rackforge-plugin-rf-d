//! Discrete cutoff-point laboratory family. No large-signal or whole-voice claim.
//! State is A*x (V), including its DC; fixed rail offsets do not change here.
#[path="charge_control_exp_data.rs"]mod data;
pub const N:usize=18;
#[derive(Clone,Copy,Debug,PartialEq)]pub struct State{pub high:[f64;N],pub low:[f64;N],pub input_v:f64,pub index:usize}
#[derive(Clone,Copy,Debug,PartialEq,Eq)]pub enum Error{InvalidInput}
#[derive(Clone,Copy,Debug)]pub struct Output{pub bus_v:f64,pub base_v:f64,pub j7_v:f64,pub panel_a:f64}
fn sum(a:f64,b:f64)->(f64,f64){let s=a+b;let v=s-a;(s,(a-(s-v))+(b-v))}
fn add(h:f64,l:f64,x:f64)->(f64,f64){let(h,e)=sum(h,x);let(l,f)=sum(l,e);let(h,l)=sum(h,l);sum(h,l+f)}
impl State{
 pub fn dc(index:usize)->Result<Self,Error>{if index>=3{return Err(Error::InvalidInput);}Ok(Self{high:data::CAP_HIGH[index],low:data::CAP_LOW[index],input_v:0.,index})}
 pub fn at_index(self,index:usize)->Result<Self,Error>{if index>=3{return Err(Error::InvalidInput);}Ok(Self{index,..self})}
 fn valid(self)->bool{self.index<3&&self.input_v.is_finite()&&self.input_v.abs()<=0.013&&(0..N).all(|i|self.high[i].is_finite()&&self.low[i].is_finite()&&sum(self.high[i],self.low[i])==(self.high[i],self.low[i]))}
 fn delta(self,index:usize)->([f64;N],[f64;N]){let mut hi=[0.;N];let mut lo=[0.;N];for k in 0..N{let(h,l)=add(self.high[k],self.low[k],-data::CAP_HIGH[index][k]);(hi[k],lo[k])=add(h,l,-data::CAP_LOW[index][k]);}(hi,lo)}
}
pub fn nodes(s:State)->Result<[f64;68],Error>{if !s.valid(){return Err(Error::InvalidInput);}let(h,l)=s.delta(s.index);Ok(std::array::from_fn(|i|{let mut v=data::XU[s.index][i]*s.input_v;for k in 0..N{v+=data::XQ[s.index][i][k]*(h[k]+l[k]);}data::DC[s.index][i]+v}))}
pub fn step(s:&mut State,index:usize,u:f64)->Result<Output,Error>{
 if index>=3||!u.is_finite()||u.abs()>0.013||!s.valid(){return Err(Error::InvalidInput);}let(h,l)=s.delta(index);let mut high=[0.;N];let mut low=[0.;N];
 for i in 0..N{let mut v=0.;for k in 0..N{v+=data::F[index][i][k]*(h[k]+l[k]);}v+=data::U0[index][i]*s.input_v+data::U1[index][i]*u;let(a,b)=add(data::CAP_HIGH[index][i],data::CAP_LOW[index][i],v);high[i]=a;low[i]=b;}
 let candidate=State{high,low,input_v:u,index};if !candidate.valid(){return Err(Error::InvalidInput);}let(h,l)=candidate.delta(index);let value=|i:usize|{let mut v=data::XU[index][i]*u;for k in 0..N{v+=data::XQ[index][i][k]*(h[k]+l[k]);}data::DC[index][i]+v};let bus=value(66);let o=Output{bus_v:bus,base_v:value(6),j7_v:value(61),panel_a:(bus-0.5*u)/39250.};
 if [o.bus_v,o.base_v,o.j7_v,o.panel_a].iter().any(|v|!v.is_finite()){return Err(Error::InvalidInput);}*s=candidate;Ok(o)
}
