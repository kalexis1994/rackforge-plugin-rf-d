"""Derive the exact same structural policy from current CSR nonzeros."""
from prepare_vco1_portable import ROOT
from prepare_release_voice import once
from prepare_voice_pivot import SOLVER

def source():
 s=(ROOT/SOLVER).read_text(encoding='utf8');a=s.index('  for block in 0..2{let mut allowed=');b=s.index('  for r in 0..132',a)
 replacement='''  for i in 0..458{for entry in self.sparse.row[i]..self.sparse.row[i+1]{let k=self.sparse.column[entry] as usize;if OWNER[i]&!ALLOWED[k]!=0||OWNER[k]&!ALLOWED[i]!=0{return Err(StepError::SingularJacobian);}}}
'''
 s=s[:a]+replacement+s[b:]
 definitions='''
const fn structural_masks()->([u8;458],[u8;458]){let mut owner=[0_u8;458];let mut allowed=[0_u8;458];let mut group=0;while group<2{let bit=1<<group;let mut i=0;while i<64{let k=INNER[group][i];owner[k]|=bit;allowed[k]|=bit;i+=1;}i=0;while i<10{let k=PORTS[group][i];if k!=usize::MAX{allowed[k]|=bit;}i+=1;}group+=1;}let mut i=0;while i<58{let k=CONTOUR[i];owner[k]|=4;allowed[k]|=4;i+=1;}i=0;while i<2{allowed[CONTOUR_PORTS[i]]|=4;i+=1;}i=0;while i<132{let k=CHAIN[i];owner[k]|=8;allowed[k]|=8;i+=1;}i=0;while i<4{allowed[CHAIN_PORTS[i]]|=8;i+=1;}(owner,allowed)}
const OWNER:[u8;458]=structural_masks().0;const ALLOWED:[u8;458]=structural_masks().1;
/// Offline exhaustive comparison of predicates, not an extra solve.
pub fn structural_policy_audit()->usize{let mut count=0;for i in 0..458{for k in 0..458{let mut original=true;for group in 0..2{if INNER[group].contains(&i)&&!INNER[group].contains(&k)&&!PORTS[group].contains(&k){original=false;}if INNER[group].contains(&k)&&!INNER[group].contains(&i)&&!PORTS[group].contains(&i){original=false;}}if CONTOUR.contains(&i)&&!CONTOUR.contains(&k)&&!CONTOUR_PORTS.contains(&k){original=false;}if CONTOUR.contains(&k)&&!CONTOUR.contains(&i)&&!CONTOUR_PORTS.contains(&i){original=false;}if CHAIN.contains(&i)&&!CHAIN.contains(&k)&&!CHAIN_PORTS.contains(&k){original=false;}if CHAIN.contains(&k)&&!CHAIN.contains(&i)&&!CHAIN_PORTS.contains(&i){original=false;}assert_eq!(original,OWNER[i]&!ALLOWED[k]==0&&OWNER[k]&!ALLOWED[i]==0);count+=1;}}count}
'''
 return s+definitions
