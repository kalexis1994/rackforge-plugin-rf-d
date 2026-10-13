//! Two-stage LM741 interior elimination; full state and original stamp stay owned outside.
use super::{StepError,solve_linear_extent};
const INNER:[[usize;64];2]=[[56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,108,109,110,111,112,113,114,115,116,117,118,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,337,338,339,340,341,342,343,344,345,346,347],[77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,119,120,121,122,123,124,125,126,127,128,129,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,348,349,350,351,352,353,354,355,356,357,358]];
const PORTS:[[usize;10];2]=[[8,9,usize::MAX,14,7,237,238,usize::MAX,243,236],[35,15,19,14,10,264,244,248,243,239]];
const EXTERNAL:[usize;330]=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,98,99,100,101,102,103,104,105,106,107,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,327,328,329,330,331,332,333,334,335,336,359,360,361,362,363,364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457];
fn many(mut a:[[f64;64];64],mut b:[[f64;11];64])->Result<[[f64;11];64],StepError>{
 let mut scale=[0.;64];for i in 0..64{scale[i]=a[i].iter().fold(0_f64,|x,v|x.max(v.abs()));if scale[i]==0.{return Err(StepError::SingularJacobian);}}
 for col in 0..64{let mut pivot=col;let mut best=0.;for row in col..64{let score=a[row][col].abs()/scale[row];if score>best{best=score;pivot=row;}}if best<1e-12{return Err(StepError::SingularJacobian);}a.swap(col,pivot);b.swap(col,pivot);scale.swap(col,pivot);let diagonal=a[col][col];
  for row in col+1..64{if a[row][col]==0.{continue;}let factor=a[row][col]/diagonal;a[row][col]=0.;for k in col+1..64{a[row][k]-=factor*a[col][k];}for k in 0..11{b[row][k]-=factor*b[col][k];}}
 }
 let mut out=[[0.;11];64];for row in(0..64).rev(){for k in 0..11{let mut value=b[row][k];for col in row+1..64{value-=a[row][col]*out[col][k];}out[row][k]=value/a[row][row];}}
 if out.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(out)
}
pub fn solve(j:[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{
 let mut s=std::array::from_fn(|a|std::array::from_fn(|c|j[EXTERNAL[a]][EXTERNAL[c]]));let mut rhs=EXTERNAL.map(|k|b[k]);let mut response=[[[0.;11];64];2];
 for block in 0..2{
  let nodes=INNER[block];let ports=PORTS[block];
  // Only documented terminals may couple to an eliminated interior, in either direction.
  for &i in &nodes{for k in 0..458{if !nodes.contains(&k)&&!ports.contains(&k)&&(j[i][k]!=0.||j[k][i]!=0.){return Err(StepError::SingularJacobian);}}}
  let a=std::array::from_fn(|r|std::array::from_fn(|c|j[nodes[r]][nodes[c]]));let r=std::array::from_fn(|i|std::array::from_fn(|k|if k==10{b[nodes[i]]}else if ports[k]==usize::MAX{0.}else{j[nodes[i]][ports[k]]}));let w=many(a,r)?;
  for &p in &ports{if p==usize::MAX{continue;}let row=EXTERNAL.iter().position(|k|*k==p).ok_or(StepError::SingularJacobian)?;
   for i in 0..64{let factor=j[p][nodes[i]];if factor==0.{continue;}rhs[row]-=factor*w[i][10];for k in 0..10{let q=ports[k];if q==usize::MAX{continue;}let col=EXTERNAL.iter().position(|v|*v==q).ok_or(StepError::SingularJacobian)?;s[row][col]-=factor*w[i][k];}}
  }response[block]=w;
 }
 let de=solve_linear_extent(s,rhs)?;let mut d=[0.;458];for(i,&k)in EXTERNAL.iter().enumerate(){d[k]=de[i];}
 for block in 0..2{for i in 0..64{let mut value=response[block][i][10];for k in 0..10{let p=PORTS[block][k];if p!=usize::MAX{value-=response[block][i][k]*d[p];}}d[INNER[block][i]]=value;}}
 if d.iter().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(d)
}
