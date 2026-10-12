"""Repair only private helper access after preserving compiler rejection/replay."""
import json
from prepare_vco1_portable import ROOT,sha,write
from prepare_joint_loudness import rendered,ADDITION
from joint_cycles_analysis import require
PREFIX='''
 let pp=rf_d_circuit::joint_voice::Parameters::new(p.controls,p.chain,[false;4],[0.5;4],p.sources)?;
 let project=|s:State|rf_d_circuit::joint_voice::State{high:std::array::from_fn(|k|s.high[k]),low:std::array::from_fn(|k|s.low[k])};
 let base=rf_d_circuit::joint_voice::parts(pp,project(old),project(delta),h)?;
 let mut s=Parts{dc:[0.;N],charge_over_h:[0.;N],dc_jacobian:[[0.;N];N],mass_over_h:[[0.;N];N],candidate:State::from_nodes([0.;N])};
 for a in 0..200 {
  s.dc[a]=base.dc[a];s.charge_over_h[a]=base.charge_over_h[a];s.candidate.high[a]=base.candidate.high[a];s.candidate.low[a]=base.candidate.low[a];
  for b in 0..200 {s.dc_jacobian[a][b]=base.dc_jacobian[a][b];s.mass_over_h[a][b]=base.mass_over_h[a][b];}
 }
'''
def repaired():
 s=rendered().replace('joint_vco_fine as fine,','').replace('output_conversion::solve_linear_sparse,','')
 a=s.index(' fn vco(self)');b=s.index('\n fn chain(self)',a);s=s[:a]+s[b:]
 a=s.index(' let e=fine::linearize_compensated');b=s.index(ADDITION,a);s=s[:a]+PREFIX+s[b:]
 source=(ROOT/'crates/rf-d-circuit/src/joint_vco_fine.rs').read_text(encoding='utf8');two=source[source.index('pub fn two_sum'):source.index('\nfn add_pair')]
 source=(ROOT/'crates/rf-d-circuit/src/output_conversion.rs').read_text(encoding='utf8');helpers=source[source.index('pub(crate) fn max_abs'):source.index('/// Scaled-pivot elimination for several right-hand sides')].replace('pub(crate)','pub')
 return s+'\nmod fine { '+two+' }\n'+helpers
def main():
 bad=json.loads((ROOT/'evidence/voice_loudness_native01.json').read_text(encoding='utf8'));require(not bad['passed'] and len(bad['replays'])==1 and bad['commands'][0]['stderr']==bad['replays'][0]['stderr'],'preserved identical compiler rejection')
 require(sha(ROOT/'tools/joint_loudness_kernel.rs')==bad['source_sha256']['tools/joint_loudness_kernel.rs'],'failed kernel identity')
 (ROOT/'tools/joint_loudness_kernel.rs').write_text(repaired(),encoding='utf8',newline='\n')
 inp=json.loads((ROOT/'evidence/voice_loudness_inputs01.json').read_text(encoding='utf8'));inp['dependency_repair']='public 200-node parts projection; byte-derived two_sum/sparse elimination; unchanged physical laws, solver and gates';inp['source_sha256']={n:sha(ROOT/n) for n in [*inp['source_sha256'],'tools/repair_joint_loudness.py','tools/run_joint_loudness.py','crates/rf-d-circuit/src/joint_vco_fine.rs','crates/rf-d-circuit/src/output_conversion.rs']};write('evidence/voice_loudness_inputs02.json',inp);print('LOUDNESS_ACCESS_REPAIR')
if __name__=='__main__':main()
