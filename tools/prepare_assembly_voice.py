"""Remove the intermediate Parts200 while preserving every electrical contribution."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import once
from joint_cycles_analysis import require
RUST=['tools/assembly_voice_kernel.rs','tools/assembly_voice_bench.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in RUST)).encode()
def public_voice():
 s=(ROOT/'crates/rf-d-circuit/src/block_decay_voice.rs').read_text(encoding='utf8');a=s.index(' let project=|s:State|');b=s.index('\n let now=old.advanced',a)
 s=s[:a]+''' let vco=|s:State|crate::joint_vco_fine::State{high:std::array::from_fn(|k|vco_index(k).map_or(0.,|i|s.high[i])),low:std::array::from_fn(|k|vco_index(k).map_or(0.,|i|s.low[i]))};
 let e=crate::joint_vco_fine::linearize_compensated(vco(old),vco(delta),p.controls,h).map_err(|_|StepError::InvalidInput)?;
 let d=vco1_stamp::linearize(e.candidate.high,p.controls,Mode::Dc).map_err(|_|StepError::InvalidInput)?;
 let c=chain_charge::linearize_compensated(pp.chain(),p.sources,old.chain(),delta.chain(),h)?;
 let mut s=Parts{dc:[0.;N],charge_over_h:[0.;N],dc_jacobian:[[0.;N];N],mass_over_h:[[0.;N];N],candidate:State::from_nodes([0.;N])};
 for a in 0..134{if let Some(i)=vco_index(a){
  let f=d.residual[a]+(0..134).map(|b|d.jacobian[a][b]*e.candidate.low[b]).sum::<f64>();
  s.dc[i]+=f;s.charge_over_h[i]+=e.residual[a]-f;s.candidate.high[i]=e.candidate.high[a];s.candidate.low[i]=e.candidate.low[a];
  for b in 0..134{if let Some(j)=vco_index(b){s.dc_jacobian[i][j]+=d.jacobian[a][b];s.mass_over_h[i][j]+=e.jacobian[a][b]-d.jacobian[a][b];}}
 }}
 for a in 0..68{let i=chain_index(a);s.dc[i]+=c.dc[a];s.charge_over_h[i]+=c.charge_over_h[a];
  if a!=66{s.candidate.high[i]=c.candidate.high[a];s.candidate.low[i]=c.candidate.low[a];}
  for b in 0..68{let j=chain_index(b);s.dc_jacobian[i][j]+=c.dc_jacobian[a][b];s.mass_over_h[i][j]+=c.mass_over_h[a][b];}
 }
 if s.dc[..200].iter().chain(s.charge_over_h[..200].iter()).chain(s.dc_jacobian[..200].iter().flat_map(|r|r[..200].iter())).chain(s.mass_over_h[..200].iter().flat_map(|r|r[..200].iter())).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
'''+s[b:]
 return s
def kernel():
 s=public_voice();s=s.replace('path="block_decay_solver.rs"','path="../crates/rf-d-circuit/src/block_decay_solver.rs"')
 s=s.replace('crate::joint_vco_fine::','base_vco_fine::');s=once(s,'use crate::{','#[path="assembly_vco_helper.rs"] mod base_vco_fine;\nuse crate::{')
 for n in ['conditioned_voice_latch.rs','decay_contour.rs']:s=s.replace(f'path="{n}"',f'path="../crates/rf-d-circuit/src/{n}"')
 return s
def vco_helper():
 s=(ROOT/'crates/rf-d-circuit/src/joint_vco_fine.rs').read_text(encoding='utf8')
 s=once(s,'use crate::output_conversion::solve_linear_sparse;','use crate::block_decay_voice::solve_linear_sparse;')
 return once(s,'#[path="vco1_stamp_data.rs"]','#[path="../crates/rf-d-circuit/src/vco1_stamp_data.rs"]')
def bench(public=False):
 s=(ROOT/'tools/zero_voice_bench.rs').read_text(encoding='utf8');a=s.index('#[path="zero_baseline_kernel.rs"]');b=s.index('struct Case',a)
 s=s[:a]+('use rf_d_circuit::{block_decay_voice as baseline,assembly_decay_voice as candidate};\n' if public else 'use rf_d_circuit::block_decay_voice as baseline;\n#[path="assembly_voice_kernel.rs"] mod candidate;\n')+s[b:]
 a=s.index('fn ieee(){');b=s.index('fn errors(){',a);s=s[:a]+s[b:]
 a=s.index('fn main(){');s=s[:a]+'''fn parts(cs:&[Case]){for c in cs{let mut p=baseline::Parameters::from_nominal(scene());p.decay_ohm=c.ohm;let mut q=candidate::Parameters::from_nominal(scene());q.decay_ohm=c.ohm;let o=baseline::State{high:std::array::from_fn(|k|c.old[k]),low:std::array::from_fn(|k|c.old[k+229])};let co=candidate::State{high:o.high,low:o.low};for i in 0..2{let d=baseline::State{high:std::array::from_fn(|k|f64::from_bits(c.expected[i*458+k])),low:std::array::from_fn(|k|f64::from_bits(c.expected[i*458+229+k]))};let cd=candidate::State{high:d.high,low:d.low};let a=baseline::parts(p,o,d,c.h).unwrap();let b=candidate::parts(q,co,cd,c.h).unwrap();assert!(a.dc.iter().chain(a.charge_over_h.iter()).chain(a.dc_jacobian.iter().flatten()).chain(a.mass_over_h.iter().flatten()).chain(a.candidate.high.iter()).chain(a.candidate.low.iter()).zip(b.dc.iter().chain(b.charge_over_h.iter()).chain(b.dc_jacobian.iter().flatten()).chain(b.mass_over_h.iter().flatten()).chain(b.candidate.high.iter()).chain(b.candidate.low.iter())).all(|(a,b)|a.to_bits()==b.to_bits()),"Parts complete bits");}}println!("PARTS_PASSED,336,105798");}
fn invalid(cs:&[Case]){let c=&cs[0];for kind in 0..12{let mut p=baseline::Parameters::from_nominal(scene());p.decay_ohm=c.ohm;let mut o=baseline::State{high:std::array::from_fn(|k|c.old[k]),low:std::array::from_fn(|k|c.old[k+229])};let mut d=baseline::State::from_nodes([0.;229]);let mut h=c.h;match kind{0=>h=0.,1=>h=-1.,2=>h=f64::NAN,3=>h=f64::INFINITY,4=>o.high[12]=f64::NAN,5=>o.high[12]=41.,6=>o.low[0]=f64::MAX,7=>d.high[3]=f64::NAN,8=>p.sources[0]=f64::NAN,9=>p.sources[0]=41.,10=>p.decay_ohm=0.,_=>p.keyboard=f64::NAN}let mut q=candidate::Parameters::from_nominal(scene());q.decay_ohm=p.decay_ohm;q.sources=p.sources;q.keyboard=p.keyboard;let co=candidate::State{high:o.high,low:o.low};let cd=candidate::State{high:d.high,low:d.low};let a=baseline::parts(p,o,d,h).err();let b=candidate::parts(q,co,cd,h).err();assert!(a.is_some(),"invalid Parts fixture {kind}");assert_eq!(a,b,"Parts error class {kind}");}println!("INVALID_PARTS_PASSED,12");}
fn main(){let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),168);parts(&cs);stamps(&cs);invalid(&cs);errors();println!("STORAGE,{},{}",baseline::Workspace::storage_bytes(),candidate::Workspace::storage_bytes());let(_,gold)=run_baseline(&cs);for round in 0..5{let(a,x,b,y)=if round%2==0{let(a,x)=run_baseline(&cs);let(b,y)=run_candidate(&cs);(a,x,b,y)}else{let(b,y)=run_candidate(&cs);let(a,x)=run_baseline(&cs);(a,x,b,y)};assert_eq!(gold,x);assert_eq!(gold,y);println!("ROUND,{round},{a},{b}");}println!("ASSEMBLY_BENCH_PASSED,168,1834,5");}
'''
 return s
def main():
 qa=json.loads((ROOT/'evidence/voice_zero_tests01.json').read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(qa['passed'] and head=='8e3dbb40c52591f05a82864d718eab256ea24b0b','admitted base');require(not (ROOT/'evidence/voice_assembly_before01.json').exists(),'exclusive assembly experiment');write('evidence/voice_assembly_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_zero_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','crates/rf-d-circuit/src/lib.rs']}))
 for n,s in [(RUST[0],kernel()),(RUST[1],bench())]:require(not (ROOT/n).exists(),'exclusive source');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);bank='references-local/voice-zero-inputs01/pairs.bin';require(sha(ROOT/bank)==qa['private_input_sha256'][bank],'own protected bank');write('evidence/voice_assembly_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_assembly_voice.py','docs/VOZ_ENSAMBLADO_PROTOCOLO.md',*RUST]},private_used_sha256={bank:sha(ROOT/bank)},pairs=168,median_gate=.95,worst_round_gate=1.05,parts_per_pair=2,parts_f64_fields=105798,stamp_f64_fields=211138));print('ASSEMBLY_PREPARED')
if __name__=='__main__':main()
