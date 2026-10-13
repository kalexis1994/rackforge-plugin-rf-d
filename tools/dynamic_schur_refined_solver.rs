//! Reuse dynamic interior/exterior factors; bounded compensated iterative refinement.
use super::StepError;
const INNER:[[usize;64];2]=[[56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,108,109,110,111,112,113,114,115,116,117,118,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,337,338,339,340,341,342,343,344,345,346,347],[77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,119,120,121,122,123,124,125,126,127,128,129,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,348,349,350,351,352,353,354,355,356,357,358]];
const PORTS:[[usize;10];2]=[[8,9,usize::MAX,14,7,237,238,usize::MAX,243,236],[35,15,19,14,10,264,244,248,243,239]];
const EXTERNAL:[usize;330]=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,98,99,100,101,102,103,104,105,106,107,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,327,328,329,330,331,332,333,334,335,336,359,360,361,362,363,364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457];
pub const MAX_REFINEMENTS:usize=3;
pub const BACKWARD_GATE:f64=1e-11;
struct Lu<const N:usize>{a:[[f64;N];N],perm:[usize;N]}
impl<const N:usize> Lu<N>{
 fn factor(mut a:[[f64;N];N])->Result<Self,StepError>{
  let mut perm=std::array::from_fn(|k|k);let mut scale=[0.;N];
  for i in 0..N{scale[i]=a[i].iter().fold(0_f64,|v,x|v.max(x.abs()));if scale[i]==0.{return Err(StepError::SingularJacobian);}}
  for col in 0..N{let mut pivot=col;let mut best=0.;for row in col..N{let score=a[row][col].abs()/scale[row];if score>best{best=score;pivot=row;}}if best<1e-12{return Err(StepError::SingularJacobian);}a.swap(col,pivot);scale.swap(col,pivot);perm.swap(col,pivot);
   let diagonal=a[col][col];let end=a[col].iter().rposition(|v|*v!=0.).unwrap()+1;let(prefix,suffix)=a.split_at_mut(col+1);let pivot_row=&prefix[col];
   for current in suffix{if current[col]==0.{continue;}let factor=current[col]/diagonal;current[col]=factor;for(target,coefficient)in current[col+1..end].iter_mut().zip(&pivot_row[col+1..end]){*target-=factor*coefficient;}}
  }
  if a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(Self{a,perm})
 }
 fn solve(&self,b:[f64;N])->Result<[f64;N],StepError>{
  let mut x=[0.;N];for row in 0..N{let mut v=b[self.perm[row]];for col in 0..row{v-=self.a[row][col]*x[col];}x[row]=v;}
  for row in(0..N).rev(){let mut v=x[row];for col in row+1..N{v-=self.a[row][col]*x[col];}x[row]=v/self.a[row][row];}
  if x.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(x)
 }
}
struct Prepared{inner:[Lu<64>;2],outer:Lu<330>,response:[[[f64;10];64];2],position:[usize;458],floor:[f64;458]}
impl Prepared{
 fn new(j:&[[f64;458];458])->Result<Self,StepError>{
  if j.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
  let mut position=[usize::MAX;458];for(i,&k)in EXTERNAL.iter().enumerate(){position[k]=i;}
  for block in 0..2{let mut allowed=[false;458];for &k in INNER[block].iter().chain(PORTS[block].iter()){if k!=usize::MAX{allowed[k]=true;}}for &i in &INNER[block]{for k in 0..458{if !allowed[k]&&(j[i][k]!=0.||j[k][i]!=0.){return Err(StepError::SingularJacobian);}}}}
  let a=|block:usize|std::array::from_fn(|r|std::array::from_fn(|c|j[INNER[block][r]][INNER[block][c]]));let inner=[Lu::factor(a(0))?,Lu::factor(a(1))?];let mut response=[[[0.;10];64];2];
  for block in 0..2{for k in 0..10{let p=PORTS[block][k];let b=std::array::from_fn(|i|if p==usize::MAX{0.}else{j[INNER[block][i]][p]});let w=inner[block].solve(b)?;for i in 0..64{response[block][i][k]=w[i];}}}
  let mut s=std::array::from_fn(|r|std::array::from_fn(|c|j[EXTERNAL[r]][EXTERNAL[c]]));
  for block in 0..2{for &p in &PORTS[block]{if p==usize::MAX{continue;}let row=position[p];for i in 0..64{let factor=j[p][INNER[block][i]];if factor==0.{continue;}for k in 0..10{let q=PORTS[block][k];if q!=usize::MAX{s[row][position[q]]-=factor*response[block][i][k];}}}}}
  let floor=std::array::from_fn(|i|(0..458).map(|k|j[i][k].abs()*tau(k)).sum());Ok(Self{inner,outer:Lu::factor(s)?,response,position,floor})
 }
 fn correction(&self,j:&[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{
  let u=[self.inner[0].solve(INNER[0].map(|k|b[k]))?,self.inner[1].solve(INNER[1].map(|k|b[k]))?];let mut rhs=EXTERNAL.map(|k|b[k]);
  for block in 0..2{for &p in &PORTS[block]{if p==usize::MAX{continue;}for i in 0..64{let factor=j[p][INNER[block][i]];if factor!=0.{rhs[self.position[p]]-=factor*u[block][i];}}}}
  let de=self.outer.solve(rhs)?;let mut d=[0.;458];for(i,&k)in EXTERNAL.iter().enumerate(){d[k]=de[i];}
  for block in 0..2{for i in 0..64{let mut v=u[block][i];for k in 0..10{let p=PORTS[block][k];if p!=usize::MAX{v-=self.response[block][i][k]*d[p];}}d[INNER[block][i]]=v;}}
  if d.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(d)
 }
}
fn tau(k:usize)->f64{if(98..133).contains(&(k%229)){2e-12}else{2e-9}}
fn residual(j:&[[f64;458];458],b:&[f64;458],d:&[f64;458],floor:&[f64;458])->Result<([f64;458],f64),StepError>{
 let mut r=[0.;458];let mut worst=0_f64;
 for i in 0..458{let mut sum=-b[i];let mut low=0.;let mut scale=b[i].abs()+floor[i];for k in 0..458{let a=j[i][k];if a==0.{continue;}let p=a*d[k];let t=sum+p;low+=if sum.abs()>=p.abs(){(sum-t)+p}else{(p-t)+sum};low+=a.mul_add(d[k],-p);sum=t;scale+=p.abs();}r[i]=-(sum+low);let q=if scale==0.{if r[i]!=0.{return Err(StepError::NoDecrease);}0.}else{r[i].abs()/scale};if !q.is_finite()||!r[i].is_finite(){return Err(StepError::InvalidInput);}worst=worst.max(q);}
 Ok((r,worst))
}
pub struct Observation{pub correction:[f64;458],pub refinements:usize,pub initial_backward:f64,pub final_backward:f64}
pub fn solve_observed(j:[[f64;458];458],b:[f64;458])->Result<Observation,StepError>{
 if b.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}let p=Prepared::new(&j)?;let mut d=p.correction(&j,b)?;let(mut r,mut metric)=residual(&j,&b,&d,&p.floor)?;let initial=metric;
 for n in 0..=MAX_REFINEMENTS{if metric<=BACKWARD_GATE{return Ok(Observation{correction:d,refinements:n,initial_backward:initial,final_backward:metric});}if n==MAX_REFINEMENTS{return Err(StepError::IterationBudget);}let e=p.correction(&j,r)?;for k in 0..458{d[k]+=e[k];}let(next,new)=residual(&j,&b,&d,&p.floor)?;if new>=metric&&new>BACKWARD_GATE{return Err(StepError::NoDecrease);}r=next;metric=new;}
 unreachable!()
}
pub fn solve(j:[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{Ok(solve_observed(j,b)?.correction)}
