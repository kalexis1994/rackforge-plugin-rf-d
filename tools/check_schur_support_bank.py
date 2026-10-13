"""Same J/b, independent full-LU refinement, ports, storage and sparse exact trace."""
import struct
from decimal import Decimal,localcontext
from prepare_vco1_portable import ROOT
from prepare_dynamic_schur import maps
from joint_cycles_analysis import require
from schur_refined_native import experiment
from run_dynamic_schur_scaled_diagnostic import MAIN
PROXY='''use super::{StepError,solve_linear_extent};
#[path="SOLVER"] mod target;
fn metric(j:&[[f64;458];458],b:&[f64;458],d:&[f64;458])->([f64;458],f64){
 let mut out=[0.;458];let mut worst=0_f64;for i in 0..458{let mut sum=-b[i];let mut low=0.;let mut scale=b[i].abs();for k in 0..458{let a=j[i][k];if a==0.{continue;}let p=a*d[k];let next=sum+p;low+=if sum.abs()>=p.abs(){(sum-next)+p}else{(p-next)+sum};low+=a.mul_add(d[k],-p);sum=next;scale+=p.abs()+a.abs()*if(98..133).contains(&(k%229)){2e-12}else{2e-9};}out[i]=-(sum+low);let q=if scale==0.{assert_eq!(out[i],0.);0.}else{out[i].abs()/scale};assert!(q.is_finite());worst=worst.max(q);}(out,worst)
}
pub fn solve(j:[[f64;458];458],b:[f64;458])->Result<[f64;458],StepError>{
 let observed=target::solve_observed(j,b)?;let d=observed.correction;let raw=solve_linear_extent(j,b)?;let mut reference=raw;let(mut residual,mut error)=metric(&j,&b,&reference);let initial=error;let mut count=0;
 while error>1e-11{assert!(count<3,"reference refinement budget");let update=solve_linear_extent(j,residual)?;for k in 0..458{reference[k]+=update[k];}let(r,next)=metric(&j,&b,&reference);assert!(next<error||next<=1e-11,"reference refinement stagnation");residual=r;error=next;count+=1;}
 let(_,target_error)=metric(&j,&b,&d);assert!(target_error<=1e-11);let mut ratio=0_f64;for k in 0..458{ratio=ratio.max((d[k]-raw[k]).abs()/if(98..133).contains(&(k%229)){2e-12}else{2e-9});}assert!(ratio<=1.);
 println!("REFINED_LINEAR,{},{:.17e},{target_error:.17e},{ratio:.17e},{count},{initial:.17e},{error:.17e}",observed.refinements,observed.initial_backward);
 let mut bytes=Vec::new();let nnz=j.iter().flatten().filter(|&&x|x!=0.).count() as u32;bytes.extend(nnz.to_le_bytes());for i in 0..458{for k in 0..458{if j[i][k]!=0.{bytes.extend((i as u16).to_le_bytes());bytes.extend((k as u16).to_le_bytes());bytes.extend(j[i][k].to_le_bytes());}}}for a in [b,d,raw,reference]{for v in a{bytes.extend(v.to_le_bytes());}}
 use std::io::Write;let path=std::env::args().nth(2).unwrap();std::fs::OpenOptions::new().append(true).open(path).unwrap().write_all(&bytes).unwrap();Ok(d)
}
'''
def decimal_trace(path):
    data=path.read_bytes();require(data[:8]==b'RFSCLR01','sparse trace magic');p=8;cases=[]
    with localcontext() as ctx:
        ctx.prec=100;zero=Decimal(0);tau=[Decimal.from_float(2e-12 if 98<=k%229<133 else 2e-9) for k in range(458)]
        while p<len(data):
            nnz=struct.unpack_from('<I',data,p)[0];p+=4;require(nnz<=458*458,'nnz range');rows=[[] for _ in range(458)];previous=(-1,-1)
            for _ in range(nnz):
                i,k,a=struct.unpack_from('<HHd',data,p);p+=12;require(0<=i<458 and 0<=k<458 and (i,k)>previous and a!=0,'ordered exact sparse matrix');previous=(i,k);rows[i].append((k,Decimal.from_float(a)))
            values=struct.unpack_from('<1832d',data,p);p+=1832*8;b,d,raw,full=([Decimal.from_float(x) for x in values[j*458:(j+1)*458]] for j in range(4));metrics={}
            for label,correction in [('schur',d),('full_refined',full),('full_raw',raw)]:
                ratios=[]
                for i,row in enumerate(rows):
                    terms=[a*correction[k] for k,a in row];res=abs(sum(terms,zero)-b[i]);scale=abs(b[i])+sum(map(abs,terms),zero)+sum((abs(a)*tau[k] for k,a in row),zero);ratio=res/scale if scale else zero
                    if label!='full_raw':require(ratio<=Decimal('1e-11'),'exact refined residual gate '+label)
                    ratios.append(ratio)
                metrics[label+'_mixed_max']=str(max(ratios));metrics[label+'_failed_rows']=sum(q>Decimal('1e-11') for q in ratios)
            diff=max(abs(d[k]-raw[k])/tau[k] for k in range(458));require(diff<=1,'exact correction contrast');metrics['correction_max_ratio']=str(diff);metrics['nnz']=nnz;cases.append(metrics)
    require(p==len(data),'complete trace parse');return cases

def validate(work,q):
    require((work/'linear.bin').read_bytes()==(ROOT/'references-local/schur-refined-bank01/linear.bin').read_bytes(),'entire dense/sparse linear trace identity')
    lines=q['stdout'].splitlines();linear=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('REFINED_LINEAR,')];port=[list(map(float,x.split(',')[1:])) for x in lines if x.startswith('PORT,')];require(len(port)==336 and lines[-1]=='DIAGNOSTIC_PASSED,84,336,1680,2016','complete ports and storage');require(max(x[2] for x in port)<=1 and max(x[3] for x in port)<=2e-11,'original memory/current gates');exact=__import__('json').loads((ROOT/'evidence/voice_schur_refined_bank02.json').read_text(encoding='utf8'))['exact_linear_checks'];require(len(exact)==len(linear),'all exact matrices');return dict(linear_solves=len(linear),independent_linear_rows=0,inherited_independent_linear_rows=len(exact)*458,independent_linear_checks_reexecuted=False,decimal_precision=100,exact_linear_checks=exact,refinement_histogram={str(i):sum(int(x[0])==i for x in linear) for i in range(4)},full_refinement_histogram={str(i):sum(int(x[4])==i for x in linear) for i in range(4)},target_initial_backward_max=max(x[1] for x in linear),target_final_backward_max=max(x[2] for x in linear),raw_correction_max_ratio=max(x[3] for x in linear),full_initial_backward_max=max(x[5] for x in linear),full_final_backward_max=max(x[6] for x in linear),memory_max_ratio=max(x[2] for x in port),port_current_max_a=max(x[3] for x in port),memory_observations=1680,terminal_and_ground_currents=2016,full_trajectory_admitted=False)

def main():
    work=ROOT/'references-local/schur-refined-supportbank01';proxy=work/'proxy.rs';kernel=work/'kernel.rs'
    # Extra adapter files are prepared within the owned experiment directory by Rust include paths.
    # Use one generated source containing the unchanged original kernel plus a nested target proxy.
    text=(ROOT/'tools/schur_support_bench.rs').read_text(encoding='utf8').split('fn main(){')[0]
    kp=(ROOT/'tools/joint_schur_support_kernel.rs').read_text(encoding='utf8')
    kp=kp.replace('#[path="dynamic_schur_support_solver.rs"] pub mod dynamic_schur;','pub mod dynamic_schur{'+PROXY.replace('SOLVER',(ROOT/'tools/dynamic_schur_support_solver.rs').as_posix())+'}')
    for n in ['latch_charge_driver.rs','contour_closed_driver.rs']:kp=kp.replace('path="'+n+'"','path="'+(ROOT/'tools'/n).as_posix()+'"')
    require(kp.startswith('//!'),'kernel document header');kp='\n'.join(x for x in kp.splitlines() if not x.startswith('//!'))
    text=text.replace('#[path="joint_schur_support_kernel.rs"] mod reuse;','mod reuse{'+kp+'}').replace('path="joint_lu_extent_kernel.rs"','path="'+(ROOT/'tools/joint_lu_extent_kernel.rs').as_posix()+'"').replace('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix())
    _,_,_,raw=maps();node=lambda k:'usize::MAX' if k==134 else str(k if k<108 else k-1);m='['+','.join('['+','.join(node(k) for k in row)+']' for row in raw)+']';main=MAIN.replace('MAPS',m).replace(' let args:Vec<_>=std::env::args().collect();',' let args:Vec<_>=std::env::args().collect();std::fs::write(&args[2],b"RFSCLR01").unwrap();',1)
    experiment('supportbank01',text+main,[ROOT/'references-local/newton-reuse-inputs01/pairs.bin','WORK/linear.bin'],['tools/check_schur_support_bank.py','tools/schur_support_bench.rs','tools/dynamic_schur_support_solver.rs','tools/joint_schur_support_kernel.rs','tools/joint_lu_extent_kernel.rs','tools/run_dynamic_schur_scaled_diagnostic.py','docs/SCHUR_SOPORTE_FRONTERAS.md','evidence/voice_schur_refined_bank02.json'],['references-local/newton-reuse-inputs01/pairs.bin','references-local/joint-startup01/librf_d_circuit.rlib','references-local/schur-refined-bank01/linear.bin'],validate,replay=True)
if __name__=='__main__':main()
