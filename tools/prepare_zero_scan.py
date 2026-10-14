"""Isolate actual CSR zero-block traversal; preserve original LU completely."""
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import once
from prepare_zero_voice import kernel,probe
from joint_cycles_analysis import require
RUST=['tools/zero_scan_solver.rs','tools/zero_scan_kernel.rs','tools/zero_baseline_solver.rs','tools/zero_baseline_kernel.rs','tools/zero_scan_bench.rs']
ATTR=b'\n/tools/zero_scan_solver.rs text eol=lf\n/tools/zero_scan_kernel.rs text eol=lf\n/tools/zero_scan_bench.rs text eol=lf\n'
def solver():
 s=(ROOT/'crates/rf-d-circuit/src/block_decay_solver.rs').read_text(encoding='utf8')
 old='for i in 0..458{self.row[i]=n;for k in 0..458{let a=j[i][k];if !a.is_finite(){return Err(StepError::InvalidInput);}if a==0.{continue;}if n==CAPACITY{return Err(StepError::InvalidInput);}self.column[n]=k as u16;self.value[n]=a;self.floor[i]+=a.abs()*tau(k);n+=1;}}'
 new='for i in 0..458{self.row[i]=n;for(block,values)in j[i].chunks(8).enumerate(){if values.iter().fold(0_u64,|bits,v|bits|v.to_bits())&0x7fff_ffff_ffff_ffff==0{continue;}for(offset,&a)in values.iter().enumerate(){let k=8*block+offset;if !a.is_finite(){return Err(StepError::InvalidInput);}if a==0.{continue;}if n==CAPACITY{return Err(StepError::InvalidInput);}self.column[n]=k as u16;self.value[n]=a;self.floor[i]+=a.abs()*tau(k);n+=1;}}}'
 return once(s,old,new)
def main():
 import json
 first=json.loads((ROOT/'evidence/voice_zero_bench01.json').read_text(encoding='utf8'));require(first['passed'] and not first['cost_utility_passed'],'measured rejection preserved')
 names={RUST[0]:probe(solver(),False),RUST[1]:kernel('zero_scan_solver.rs'),RUST[4]:(ROOT/'tools/zero_voice_bench.rs').read_text(encoding='utf8').replace('zero_voice_kernel.rs','zero_scan_kernel.rs').replace('ZERO_BENCH_PASSED','ZERO_SCAN_BENCH_PASSED')}
 for n,s in names.items():require(not (ROOT/n).exists(),'exclusive scan source');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);write('evidence/voice_zero_scan_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_zero_scan.py','tools/prepare_zero_voice.py','docs/VOZ_CEROS_SCAN_PROTOCOLO.md','evidence/voice_zero_bench01.json',*names]},previous_variant_promoted=False,median_ratio_gate=.95,worst_round_ratio_gate=1.05));print('ZERO_SCAN_PREPARED')
if __name__=='__main__':main()
