"""Suggest an elimination order; never turn an observed zero into an omission."""
import json,re
import numpy as np
from prepare_dual_chain import ROOT,sha,write
def main():
    profile=json.loads((ROOT/'evidence/voice_cost_profile01.json').read_text(encoding='utf8'));assert profile['passed']
    source='crates/rf-d-circuit/src/dual_voice_solver.rs';s=(ROOT/source).read_text(encoding='utf8')
    line=next(l for l in s.splitlines() if l.startswith('const CHAIN:'))
    original=list(map(int,re.findall(r'\d+',line.split('=',1)[1])));assert len(original)==234 and len(set(original))==234
    used={};pattern=np.zeros((234,234),dtype=bool)
    for maximum in [1048576,524288]:
        path=ROOT/f'references-local/dual-voice02/linear-{maximum}.bin';used[path.relative_to(ROOT).as_posix()]=sha(path)
        j=np.frombuffer(path.read_bytes(),dtype='<f8')[:250000].reshape(500,500)
        a=j[np.ix_(original,original)];pattern|=(a!=0)|(a.T!=0)
    graph={i:set(np.flatnonzero(pattern[i]))-{i} for i in range(234)};remaining=set(graph);order=[]
    while remaining:
        k=min(remaining,key=lambda i:(len(graph[i]&remaining),original[i]));neighbors=graph[k]&remaining
        for i in neighbors:graph[i]|=neighbors-{i}
        remaining.remove(k);order.append(original[k])
    assert sorted(order)==sorted(original)
    s=s.replace(line,'const CHAIN:[usize;234]=['+','.join(map(str,order))+'];')
    s=s.replace('pub fn solve_observed(j:[[f64;500];500],b:[f64;500])->Result<Observation,StepError>{',
        'pub struct Workspace{prepared:Prepared}\nimpl Workspace{\n pub const fn new()->Self{Self{prepared:Prepared::blank()}}\n pub fn solve_observed(&mut self,j:&[[f64;500];500],b:[f64;500])->Result<Observation,StepError>{')
    s=s.replace('let mut p=Prepared::blank();p.initialize(&j)?;','let p=&mut self.prepared;p.initialize(j)?;')
    s=s.replace('p.correction(&j,','p.correction(j,')
    old='pub fn solve(j:[[f64;500];500],b:[f64;500])->Result<[f64;500],StepError>{Ok(solve_observed(j,b)?.correction)}'
    assert s.count(old)==1
    s=s.replace(old,'pub fn solve(&mut self,j:&[[f64;500];500],b:[f64;500])->Result<[f64;500],StepError>{Ok(self.solve_observed(j,b)?.correction)}\n}\n')
    solver=ROOT/'crates/rf-d-circuit/src/ordered_voice_solver.rs';assert not solver.exists();solver.write_text(s,encoding='utf8',newline='\n')
    source_voice='crates/rf-d-circuit/src/dual_voice.rs';v=(ROOT/source_voice).read_text(encoding='utf8')
    v=v.replace('path="dual_voice_solver.rs"','path="ordered_voice_solver.rs"').replace('pub struct Workspace{first:Stamp,second:Stamp}','pub struct Workspace{first:Stamp,second:Stamp,linear:solver::Workspace}')
    v=v.replace('Self{first:Stamp::blank(),second:Stamp::blank()}','Self{first:Stamp::blank(),second:Stamp::blank(),linear:solver::Workspace::new()}')
    v=v.replace('solver::solve(s.jacobian,','self.linear.solve(&s.jacobian,').replace('solver::solve(t.jacobian,','self.linear.solve(&t.jacobian,')
    voice=ROOT/'crates/rf-d-circuit/src/ordered_voice.rs';assert not voice.exists();voice.write_text(v,encoding='utf8',newline='\n')
    write(ROOT/'evidence/voice_order_recipe01.json',dict(schema='rf-d/voice-cost/order-v1',passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_voice_order.py',source,source_voice,'crates/rf-d-circuit/src/ordered_voice_solver.rs','crates/rf-d-circuit/src/ordered_voice.rs']},private_used_sha256=used,original_chain_order=original,chain_order=order,ordering_seed='minimum-degree suggestion from two admitted initial matrices; symmetric incidence; tie by physical node ID',observed_pattern_is_not_a_drop_mask=True,all_coefficients_copied=True,workspace_reused=True,borrowed_matrix=True,physical_circuit_changed=False,numerical_gates_changed=False))
    print('VOICE_ORDER_RECIPE',len(order))
if __name__=='__main__':main()
