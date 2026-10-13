"""Keep the failed diagnostic intact; generate the explicitly rescaled next attempt."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require

PROXY='''use super::{StepError,solve_linear_extent};
#[path="SOLVER_PATH"] mod original;
fn errors(j:&[[f64;458];458],b:&[f64;458],d:&[f64;458])->(f64,f64,usize,f64){
 let(mut pure,mut mixed,mut failed,mut absolute)=(0_f64,0_f64,0_usize,0_f64);
 for i in 0..458{let mut sum=0.;let mut low=0.;let mut denom=b[i].abs();let mut floor=0.;
  for k in 0..458{let term=j[i][k]*d[k];let t=sum+term;low+=if sum.abs()>=term.abs(){(sum-t)+term}else{(term-t)+sum};sum=t;denom+=term.abs();floor+=j[i][k].abs()*if(98..133).contains(&(k%229)){2e-12}else{2e-9};}
  let error=((sum-b[i])+low).abs();let q=if denom==0.{assert_eq!(error,0.);0.}else{error/denom};let m=if denom+floor==0.{assert_eq!(error,0.);0.}else{error/(denom+floor)};
  assert!(q.is_finite()&&m.is_finite()&&error.is_finite());pure=pure.max(q);mixed=mixed.max(m);failed+=usize::from(q>1e-11);absolute=absolute.max(error);
 }(pure,mixed,failed,absolute)
}
pub fn solve(j:[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{
 let d=original::solve(j,b)?;let full=solve_linear_extent(j,b)?;let mut ratio=0_f64;
 for i in 0..458{ratio=ratio.max((d[i]-full[i]).abs()/if(98..133).contains(&(i%229)){2e-12}else{2e-9});}
 let a=errors(&j,&b,&d);let c=errors(&j,&b,&full);
 assert!(ratio<=1.,"correction difference {ratio}");assert!(a.1<=1e-11&&c.1<=1e-11,"scaled backward {a:?} {c:?}");
 println!("LINEAR,{ratio:.17e},{:.17e},{:.17e},{},{:.17e},{:.17e},{:.17e},{},{:.17e}",a.0,a.1,a.2,a.3,c.0,c.1,c.2,c.3);Ok(d)
}
'''

def main():
    s=(ROOT/'tools/run_dynamic_schur_diagnostic.py').read_text(encoding='utf8')
    start=s.index("PROXY='''");end=s.index("MAIN='''",start)
    s=s[:start]+"PROXY="+repr(PROXY)+"\n"+s[end:]
    s=s.replace('dynamic-schur-diagnostic01','dynamic-schur-diagnostic02').replace('voice_dynamic_schur_diagnostic_command01','voice_dynamic_schur_diagnostic_command02').replace('voice_dynamic_schur_diagnostic01.json','voice_dynamic_schur_diagnostic02.json')
    s=s.replace("names=['tools/run_dynamic_schur_diagnostic.py',","names=['docs/SCHUR_DINAMICO_ESCALA_RESIDUAL.md','tools/prepare_dynamic_schur_scaled_diagnostic.py','tools/run_dynamic_schur_scaled_diagnostic.py',")
    p=ROOT/'tools/run_dynamic_schur_scaled_diagnostic.py';require(not p.exists(),'exclusive diagnostic source');p.write_text(s,encoding='utf8',newline='\n')

if __name__=='__main__':main()
