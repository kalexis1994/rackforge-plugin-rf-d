"""Change only the traversal of the exact Radau stage Jacobian entries."""
from prepare_voice_pivot import kernel
from prepare_release_voice import once
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
RUST=['tools/voice_block_kernel.rs','tools/voice_block_bench.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in RUST)).encode()

def block_kernel():
 s=kernel('../crates/rf-d-circuit/src/conditioned_voice_solver.rs')
 old='  for k in 0..M{let i=k/N;let a=k%N;for l in 0..M{let j=l/N;let b=l%N;self.jacobian[k][l]=B[i][j]*q[j].mass_over_h[a][b]+if i==j{q[i].dc_jacobian[a][b]}else{0.};}}'
 new='  for i in 0..2{for a in 0..N{for j in 0..2{for b in 0..N{self.jacobian[i*N+a][j*N+b]=B[i][j]*q[j].mass_over_h[a][b]+if i==j{q[i].dc_jacobian[a][b]}else{0.};}}}}'
 return once(s,old,new)

def block_bench():
 s=(ROOT/'tools/voice_pivot_bench.rs').read_text(encoding='utf8').replace('voice_pivot_kernel.rs','voice_block_kernel.rs').replace('PIVOT_BENCH_PASSED','BLOCK_BENCH_PASSED')
 marker='fn main(){'
 extra='''fn stamps(cs:&[Case]){
 for c in cs{let mut p=baseline::Parameters::from_nominal(scene());p.decay_ohm=c.ohm;let mut cp=candidate::Parameters::from_nominal(scene());cp.decay_ohm=c.ohm;
 let old=baseline::State{high:std::array::from_fn(|k|c.old[k]),low:std::array::from_fn(|k|c.old[k+229])};let co=candidate::State{high:old.high,low:old.low};
 let d=std::array::from_fn(|i|baseline::State{high:std::array::from_fn(|k|f64::from_bits(c.expected[i*458+k])),low:std::array::from_fn(|k|f64::from_bits(c.expected[i*458+229+k]))});let cd=std::array::from_fn(|i|candidate::State{high:d[i].high,low:d[i].low});
 let a=baseline::linearize(p,old,d,c.h).unwrap();let b=candidate::linearize(cp,co,cd,c.h).unwrap();
 assert!(a.residual.iter().chain(a.jacobian.iter().flatten()).chain(a.candidates.iter().flat_map(|s|s.high.iter().chain(s.low.iter()))).zip(b.residual.iter().chain(b.jacobian.iter().flatten()).chain(b.candidates.iter().flat_map(|s|s.high.iter().chain(s.low.iter())))).all(|(a,b)|a.to_bits()==b.to_bits()),"complete stamp by bits");
 }println!("STAMPS_PASSED,78,211138");
}
'''
 s=once(s,marker,extra+marker);return once(s,'assert_eq!(cs.len(),78);','assert_eq!(cs.len(),78);stamps(&cs);')

def main():
 for n,s in [(RUST[0],block_kernel()),(RUST[1],block_bench())]:require(not (ROOT/n).exists(),'exclusive block source');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);print('BLOCK_SOURCES_PREPARED')
if __name__=='__main__':main()
