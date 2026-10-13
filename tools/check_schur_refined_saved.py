"""Exact saved J/b replay followed by Decimal100 with exact binary64 operands."""
import struct
from decimal import Decimal,localcontext
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
from schur_refined_native import experiment
MAIN='''#[path="KERNEL"] mod kernel;
fn main(){let args:Vec<_>=std::env::args().collect();let bytes=std::fs::read(&args[1]).unwrap();assert_eq!(&bytes[..8],b"RFSCHJ01");assert_eq!(bytes.len(),8+8*(458*458+3*458));let v:Vec<f64>=bytes[8..].chunks_exact(8).map(|b|f64::from_le_bytes(b.try_into().unwrap())).collect();let j=std::array::from_fn(|i|std::array::from_fn(|k|v[i*458+k]));let b=std::array::from_fn(|i|v[458*458+i]);let q=kernel::dynamic_schur::solve_observed(j,b).unwrap();let mut ratio=0_f64;for k in 0..458{ratio=ratio.max((q.correction[k]-v[458*458+916+k]).abs()/if(98..133).contains(&(k%229)){2e-12}else{2e-9});}assert!(ratio<=1.);println!("REFINED,{},{:.17e},{:.17e},{ratio:.17e}",q.refinements,q.initial_backward,q.final_backward);let mut out=b"RFSCOR01".to_vec();for x in q.correction{out.extend(x.to_le_bytes());}std::fs::write(&args[2],out).unwrap();}
'''
def validate(work,q):
    raw=(ROOT/'references-local/dynamic-schur-scaled-inspection01/failed-system.bin').read_bytes();v=struct.unpack('<'+str((len(raw)-8)//8)+'d',raw[8:]);out=(work/'correction.bin').read_bytes();require(out[:8]==b'RFSCOR01' and len(out)==8+458*8,'correction format');d=struct.unpack('<458d',out[8:]);metrics=[]
    with localcontext() as c:
        c.prec=100;a=[Decimal.from_float(x) for x in v];x=[Decimal.from_float(t) for t in d];n=458*458;b=a[n:n+458];tau=[Decimal.from_float(2e-12 if 98<=k%229<133 else 2e-9) for k in range(458)]
        for i in range(458):
            coeff=a[i*458:(i+1)*458];terms=[j*y for j,y in zip(coeff,x)];error=abs(sum(terms,Decimal(0))-b[i]);scale=abs(b[i])+sum(map(abs,terms),Decimal(0))+sum((abs(j)*t for j,t in zip(coeff,tau)),Decimal(0));ratio=error/scale if scale else Decimal(0);require(ratio<=Decimal('1e-11'),'exact mixed backward');metrics.append((ratio,i))
        diff=max(abs(x[k]-a[n+916+k])/tau[k] for k in range(458));require(diff<=1,'exact raw-reference correction gate')
    fields=q['stdout'].strip().split(',');require(fields[0]=='REFINED' and 0<int(fields[1])<=3,'bounded refinement used');return dict(precision=100,independent_linear_rows=458,decimal_mixed_backward_max=str(max(metrics)[0]),decimal_worst_row=max(metrics)[1],decimal_correction_max_ratio=str(diff),refinements=int(fields[1]),initial_backward=float(fields[2]),final_backward=float(fields[3]),full_trajectory_admitted=False)
def main():
    experiment('saved01',MAIN.replace('KERNEL',(ROOT/'tools/joint_schur_refined_kernel.rs').as_posix()),[ROOT/'references-local/dynamic-schur-scaled-inspection01/failed-system.bin','WORK/correction.bin'],['tools/check_schur_refined_saved.py','tools/dynamic_schur_refined_solver.rs','tools/joint_schur_refined_kernel.rs','docs/SCHUR_REFINADO_PROTOCOLO.md','evidence/voice_schur_refined_inputs01.json'],['references-local/dynamic-schur-scaled-inspection01/failed-system.bin','references-local/joint-startup01/librf_d_circuit.rlib'],validate,replay=True,timeout=120)
if __name__=='__main__':main()
