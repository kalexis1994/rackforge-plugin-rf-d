"""Publish the measured traversal as an explicit family; preserve old modules."""
import json
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import once
from prepare_voice_paired import paired
from joint_cycles_analysis import require
from voice_block_structure import source as structural_solver
RUST=['crates/rf-d-circuit/src/block_decay_voice.rs','crates/rf-d-circuit/src/block_decay_engine.rs','crates/rf-d-circuit/examples/block_decay_verify.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in RUST)).encode();EXPORT=b'\npub mod block_decay_voice;\npub mod block_decay_engine;\n'
def sources():
 old=(ROOT/'crates/rf-d-circuit/src/decay_voice.rs').read_text(encoding='utf8');a='  for k in 0..M{let i=k/N;let a=k%N;for l in 0..M{let j=l/N;let b=l%N;self.jacobian[k][l]=B[i][j]*q[j].mass_over_h[a][b]+if i==j{q[i].dc_jacobian[a][b]}else{0.};}}';b='  for i in 0..2{for a in 0..N{for j in 0..2{for b in 0..N{self.jacobian[i*N+a][j*N+b]=B[i][j]*q[j].mass_over_h[a][b]+if i==j{q[i].dc_jacobian[a][b]}else{0.};}}}}'
 voice=once(old,a,b).replace('path="conditioned_voice_solver.rs"','path="block_decay_solver.rs"');engine=(ROOT/'crates/rf-d-circuit/src/decay_engine.rs').read_text(encoding='utf8').replace('crate::decay_voice','crate::block_decay_voice')
 return {**dict(zip(RUST,[voice,engine,paired(True)])),'crates/rf-d-circuit/src/block_decay_solver.rs':structural_solver()}
def main():
 names=['evidence/voice_block_bench01.json','evidence/voice_block_paired_reference02.json'];a,b=[json.loads((ROOT/n).read_text(encoding='utf8')) for n in names];require(a['passed'] and a['cost_utility_passed'] and b['passed'] and b['every_accepted_bits_identical'],'bank/utility and every accepted admission')
 for n,s in sources().items():require(not (ROOT/n).exists(),'exclusive public family');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 for n,s in [('.gitattributes',ATTR),('crates/rf-d-circuit/src/lib.rs',EXPORT)]:p=ROOT/n;p.write_bytes(p.read_bytes()+s)
 write('evidence/voice_block_promotion01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/promote_voice_block.py',*RUST,*names]},nominal_modules_unchanged=True,only_stage_jacobian_traversal_changed=True,portable_validation_pending=True,physical_fidelity=False,real_time=False))
 print('BLOCK_PUBLIC_FAMILY_PREPARED')
if __name__=='__main__':main()
