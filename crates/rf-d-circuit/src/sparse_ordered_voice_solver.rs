//! Generated two LM741 blocks plus complete loaded dual chain; no coefficient drop.
use super::StepError;
const INNER:[[usize;64];2]=[[56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,108,109,110,111,112,113,114,115,116,117,118,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,358,359,360,361,362,363,364,365,366,367,368],[77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,119,120,121,122,123,124,125,126,127,128,129,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,369,370,371,372,373,374,375,376,377,378,379]];
const PORTS:[[usize;10];2]=[[8,9,usize::MAX,14,7,258,259,usize::MAX,264,257],[35,15,19,14,10,285,265,269,264,260]];
const CHAIN:[usize;234]=[145,149,155,184,223,222,395,399,405,434,473,472,137,139,140,141,142,146,148,154,157,164,163,162,166,169,168,170,176,177,178,182,183,186,207,211,217,187,216,228,232,230,235,239,240,242,241,243,387,389,390,391,392,396,398,404,407,414,413,412,416,419,418,420,426,427,428,432,433,436,457,461,467,437,466,478,482,480,485,489,490,492,491,493,133,134,135,136,143,144,147,153,403,165,179,180,189,206,208,210,227,231,238,246,248,498,383,384,385,386,393,394,397,415,429,430,439,456,458,479,488,496,151,156,161,167,175,181,185,193,212,220,221,234,245,244,247,495,494,497,237,487,486,236,484,233,402,406,411,425,435,444,459,470,471,481,499,249,138,152,190,204,224,225,229,226,219,218,214,421,440,401,409,438,442,455,463,469,476,474,475,477,483,213,464,468,465,158,408,159,160,172,422,173,188,191,423,431,448,452,150,400,424,215,388,410,171,174,205,454,445,197,201,441,417,194,195,209,460,462,192,196,198,199,200,202,203,443,446,447,449,450,451,453];
const CHAIN_PORTS:[usize;2]=[12,262];
const EXTERNAL:[usize;138]=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,98,99,100,101,102,103,104,105,106,107,130,131,132,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,348,349,350,351,352,353,354,355,356,357,380,381,382];
pub const MAX_REFINEMENTS:usize=3;
pub const BACKWARD_GATE:f64=1e-11;
struct Lu<const N:usize>{a:[[f64;N];N],perm:[usize;N],lower:[[u16;N];N],upper:[[u16;N];N],nl:[usize;N],nu:[usize;N]}
impl<const N:usize> Lu<N>{
 fn factor_in_place(&mut self)->Result<(),StepError>{
  let a=&mut self.a;self.perm=std::array::from_fn(|k|k);let perm=&mut self.perm;let mut scale=[0.;N];
  for i in 0..N{scale[i]=a[i].iter().fold(0_f64,|v,x|v.max(x.abs()));if scale[i]==0.{return Err(StepError::SingularJacobian);}}
  for col in 0..N{let mut pivot=col;let mut best=0.;for row in col..N{let score=a[row][col].abs()/scale[row];if score>best{best=score;pivot=row;}}if best<1e-12{return Err(StepError::SingularJacobian);}a.swap(col,pivot);scale.swap(col,pivot);perm.swap(col,pivot);
   let diagonal=a[col][col];let end=a[col].iter().rposition(|v|*v!=0.).unwrap()+1;let(prefix,suffix)=a.split_at_mut(col+1);let pivot_row=&prefix[col];
   for current in suffix{if current[col]==0.{continue;}let factor=current[col]/diagonal;current[col]=factor;for(target,coefficient)in current[col+1..end].iter_mut().zip(&pivot_row[col+1..end]){*target-=factor*coefficient;}}
  }
  if a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}
  self.nl.fill(0);self.nu.fill(0);
  for row in 0..N{for col in 0..row{if a[row][col]!=0.{self.lower[row][self.nl[row]]=col as u16;self.nl[row]+=1;}}for col in row+1..N{if a[row][col]!=0.{self.upper[row][self.nu[row]]=col as u16;self.nu[row]+=1;}}}Ok(())
 }
 fn solve(&self,b:[f64;N])->Result<[f64;N],StepError>{
  let mut x=[0.;N];for row in 0..N{let mut v=b[self.perm[row]];for entry in 0..self.nl[row]{let col=self.lower[row][entry] as usize;v-=self.a[row][col]*x[col];}x[row]=v;}
  for row in(0..N).rev(){let mut v=x[row];for entry in 0..self.nu[row]{let col=self.upper[row][entry] as usize;v-=self.a[row][col]*x[col];}x[row]=v/self.a[row][row];}
  if x.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(x)
 }
}
struct Prepared{inner:[Lu<64>;2],outer:Lu<138>,chain:Lu<234>,chain_response:[[f64;2];234],response:[[[f64;10];64];2],position:[usize;500],sparse:Sparse}
impl Prepared{
 const fn blank()->Self{Self{inner:[Lu{a:[[0.;64];64],perm:[0;64],lower:[[0;64];64],upper:[[0;64];64],nl:[0;64],nu:[0;64]},Lu{a:[[0.;64];64],perm:[0;64],lower:[[0;64];64],upper:[[0;64];64],nl:[0;64],nu:[0;64]}],outer:Lu{a:[[0.;138];138],perm:[0;138],lower:[[0;138];138],upper:[[0;138];138],nl:[0;138],nu:[0;138]},chain:Lu{a:[[0.;234];234],perm:[0;234],lower:[[0;234];234],upper:[[0;234];234],nl:[0;234],nu:[0;234]},chain_response:[[0.;2];234],response:[[[0.;10];64];2],position:[usize::MAX;500],sparse:Sparse{row:[0;501],column:[0;CAPACITY],value:[0.;CAPACITY],floor:[0.;500]}}}
 fn initialize(&mut self,j:&[[f64;500];500])->Result<(),StepError>{
  self.sparse.initialize(j)?;self.position.fill(usize::MAX);for(i,&k)in EXTERNAL.iter().enumerate(){self.position[k]=i;}
  for i in 0..500{for entry in self.sparse.row[i]..self.sparse.row[i+1]{let k=self.sparse.column[entry] as usize;if OWNER[i]&!ALLOWED[k]!=0||OWNER[k]&!ALLOWED[i]!=0{return Err(StepError::SingularJacobian);}}}
  for r in 0..234{for c in 0..234{self.chain.a[r][c]=j[CHAIN[r]][CHAIN[c]];}}self.chain.factor_in_place()?;
  for k in 0..2{let p=CHAIN_PORTS[k];let w=self.chain.solve(CHAIN.map(|i|j[i][p]))?;for i in 0..234{self.chain_response[i][k]=w[i];}}
  for block in 0..2{for r in 0..64{for c in 0..64{self.inner[block].a[r][c]=j[INNER[block][r]][INNER[block][c]];}}self.inner[block].factor_in_place()?;}
  for block in 0..2{for k in 0..10{let p=PORTS[block][k];let b=std::array::from_fn(|i|if p==usize::MAX{0.}else{j[INNER[block][i]][p]});let w=self.inner[block].solve(b)?;for i in 0..64{self.response[block][i][k]=w[i];}}}
  for r in 0..138{for c in 0..138{self.outer.a[r][c]=j[EXTERNAL[r]][EXTERNAL[c]];}}
  for block in 0..2{for &p in &PORTS[block]{if p==usize::MAX{continue;}let row=self.position[p];for i in 0..64{let factor=j[p][INNER[block][i]];if factor==0.{continue;}for k in 0..10{let q=PORTS[block][k];if q!=usize::MAX{self.outer.a[row][self.position[q]]-=factor*self.response[block][i][k];}}}}}
  for &p in &CHAIN_PORTS{let row=self.position[p];for i in 0..234{let factor=j[p][CHAIN[i]];if factor==0.{continue;}for k in 0..2{self.outer.a[row][self.position[CHAIN_PORTS[k]]]-=factor*self.chain_response[i][k];}}}
  self.outer.factor_in_place()?;Ok(())
 }
 fn correction(&self,j:&[[f64;500];500],b:[f64;500])->Result<[f64;500],StepError>{
  let u=[self.inner[0].solve(INNER[0].map(|k|b[k]))?,self.inner[1].solve(INNER[1].map(|k|b[k]))?];let ua=self.chain.solve(CHAIN.map(|k|b[k]))?;let mut rhs=EXTERNAL.map(|k|b[k]);
  for block in 0..2{for &p in &PORTS[block]{if p==usize::MAX{continue;}for i in 0..64{let factor=j[p][INNER[block][i]];if factor!=0.{rhs[self.position[p]]-=factor*u[block][i];}}}}
  for &p in &CHAIN_PORTS{for i in 0..234{let factor=j[p][CHAIN[i]];if factor!=0.{rhs[self.position[p]]-=factor*ua[i];}}}
  let de=self.outer.solve(rhs)?;let mut d=[0.;500];for(i,&k)in EXTERNAL.iter().enumerate(){d[k]=de[i];}
  for block in 0..2{for i in 0..64{let mut v=u[block][i];for k in 0..10{let p=PORTS[block][k];if p!=usize::MAX{v-=self.response[block][i][k]*d[p];}}d[INNER[block][i]]=v;}}
  for i in 0..234{let mut v=ua[i];for k in 0..2{v-=self.chain_response[i][k]*d[CHAIN_PORTS[k]];}d[CHAIN[i]]=v;}
  if d.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(d)
 }
}
fn tau(k:usize)->f64{if(98..133).contains(&(k%250)){2e-12}else{2e-9}}
const CAPACITY:usize=8192;
struct Sparse{row:[usize;501],column:[u16;CAPACITY],value:[f64;CAPACITY],floor:[f64;500]}
impl Sparse{
 fn initialize(&mut self,j:&[[f64;500];500])->Result<(),StepError>{
  self.floor.fill(0.);let mut n=0;
  for i in 0..500{self.row[i]=n;for k in 0..500{let a=j[i][k];if !a.is_finite(){return Err(StepError::InvalidInput);}if a==0.{continue;}if n==CAPACITY{return Err(StepError::InvalidInput);}self.column[n]=k as u16;self.value[n]=a;self.floor[i]+=a.abs()*tau(k);n+=1;}}self.row[500]=n;Ok(())
 }
}
fn residual(s:&Sparse,b:&[f64;500],d:&[f64;500])->Result<([f64;500],f64),StepError>{
 let mut r=[0.;500];let mut worst=0_f64;
 for i in 0..500{let mut sum=-b[i];let mut low=0.;let mut scale=b[i].abs()+s.floor[i];for entry in s.row[i]..s.row[i+1]{let k=s.column[entry] as usize;let a=s.value[entry];let p=a*d[k];let t=sum+p;low+=if sum.abs()>=p.abs(){(sum-t)+p}else{(p-t)+sum};low+=a.mul_add(d[k],-p);sum=t;scale+=p.abs();}r[i]=-(sum+low);let q=if scale==0.{if r[i]!=0.{return Err(StepError::NoDecrease);}0.}else{r[i].abs()/scale};if !q.is_finite()||!r[i].is_finite(){return Err(StepError::InvalidInput);}worst=worst.max(q);}
 Ok((r,worst))
}
pub struct Observation{pub correction:[f64;500],pub refinements:usize,pub initial_backward:f64,pub final_backward:f64}
pub struct Workspace{prepared:Prepared}
impl Workspace{
 pub const fn new()->Self{Self{prepared:Prepared::blank()}}
 pub fn solve_observed(&mut self,j:&[[f64;500];500],b:[f64;500])->Result<Observation,StepError>{
 if b.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}let p=&mut self.prepared;p.initialize(j)?;let mut d=p.correction(j,b)?;let(mut r,mut metric)=residual(&p.sparse,&b,&d)?;let initial=metric;
 for n in 0..=MAX_REFINEMENTS{if metric<=BACKWARD_GATE{return Ok(Observation{correction:d,refinements:n,initial_backward:initial,final_backward:metric});}if n==MAX_REFINEMENTS{return Err(StepError::IterationBudget);}let e=p.correction(j,r)?;for k in 0..500{d[k]+=e[k];}let(next,new)=residual(&p.sparse,&b,&d)?;if new>=metric&&new>BACKWARD_GATE{return Err(StepError::NoDecrease);}r=next;metric=new;}
 unreachable!()
}
pub fn solve(&mut self,j:&[[f64;500];500],b:[f64;500])->Result<[f64;500],StepError>{Ok(self.solve_observed(j,b)?.correction)}
}


const fn structural_masks()->([u8;500],[u8;500]){let mut owner=[0_u8;500];let mut allowed=[0_u8;500];let mut group=0;while group<2{let bit=1<<group;let mut i=0;while i<64{let k=INNER[group][i];owner[k]|=bit;allowed[k]|=bit;i+=1;}i=0;while i<10{let k=PORTS[group][i];if k!=usize::MAX{allowed[k]|=bit;}i+=1;}group+=1;}let mut i=0;while i<234{let k=CHAIN[i];owner[k]|=4;allowed[k]|=4;i+=1;}i=0;while i<2{allowed[CHAIN_PORTS[i]]|=4;i+=1;}(owner,allowed)}
const OWNER:[u8;500]=structural_masks().0;const ALLOWED:[u8;500]=structural_masks().1;
