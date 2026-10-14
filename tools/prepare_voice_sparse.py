"""Sparse triangular substitutions from freshly factored exact coefficients."""
from prepare_dual_chain import ROOT,sha,write
def main():
    n='crates/rf-d-circuit/src/ordered_voice_solver.rs';s=(ROOT/n).read_text(encoding='utf8')
    s=s.replace('struct Lu<const N:usize>{a:[[f64;N];N],perm:[usize;N]}','struct Lu<const N:usize>{a:[[f64;N];N],perm:[usize;N],lower:[[u16;N];N],upper:[[u16;N];N],nl:[usize;N],nu:[usize;N]}')
    old='if a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(())'
    assert s.count(old)==1
    s=s.replace(old,'''if a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}
  self.nl.fill(0);self.nu.fill(0);
  for row in 0..N{for col in 0..row{if a[row][col]!=0.{self.lower[row][self.nl[row]]=col as u16;self.nl[row]+=1;}}for col in row+1..N{if a[row][col]!=0.{self.upper[row][self.nu[row]]=col as u16;self.nu[row]+=1;}}}Ok(())''')
    s=s.replace('for col in 0..row{v-=self.a[row][col]*x[col];}', 'for entry in 0..self.nl[row]{let col=self.lower[row][entry] as usize;v-=self.a[row][col]*x[col];}')
    s=s.replace('for col in row+1..N{v-=self.a[row][col]*x[col];}', 'for entry in 0..self.nu[row]{let col=self.upper[row][entry] as usize;v-=self.a[row][col]*x[col];}')
    for size in [64,138,234]:
        old=f'Lu{{a:[[0.;{size}];{size}],perm:[0;{size}]}}';new=f'Lu{{a:[[0.;{size}];{size}],perm:[0;{size}],lower:[[0;{size}];{size}],upper:[[0;{size}];{size}],nl:[0;{size}],nu:[0;{size}]}}';assert old in s;s=s.replace(old,new)
    new='crates/rf-d-circuit/src/sparse_ordered_voice_solver.rs';p=ROOT/new;assert not p.exists();p.write_text(s,encoding='utf8',newline='\n')
    voice='crates/rf-d-circuit/src/sparse_ordered_voice.rs';v=(ROOT/'crates/rf-d-circuit/src/ordered_voice.rs').read_text(encoding='utf8').replace('ordered_voice_solver.rs','sparse_ordered_voice_solver.rs');p=ROOT/voice;assert not p.exists();p.write_text(v,encoding='utf8',newline='\n')
    bench='tools/voice_sparse_bench.rs';v=(ROOT/'tools/voice_order_bench.rs').read_text(encoding='utf8').replace('src/ordered_voice.rs','src/sparse_ordered_voice.rs');p=ROOT/bench;assert not p.exists();p.write_text(v,encoding='utf8',newline='\n')
    write(ROOT/'evidence/voice_sparse_recipe01.json',dict(passed=True,source_sha256={k:sha(ROOT/k) for k in ['tools/prepare_voice_sparse.py',n,new,voice,bench]},exact_zero_only=True,rebuild_indices_after_every_factor=True,increasing_column_order_preserved=True,observed_pattern_not_used_to_drop_values=True,physical_circuit_changed=False,numerical_gates_changed=False))
    print('VOICE_SPARSE_PREPARED')
if __name__=='__main__':main()
