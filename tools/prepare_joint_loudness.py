"""Declare and generate the 205-node laboratory extension without changing kernels."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/tools/joint_loudness_kernel.rs text eol=lf\n/tools/joint_loudness_runner.rs text eol=lf\n'
ADDITION='''
 let now=old.advanced(delta.high).advanced(delta.low);
 let fp=rf_d_circuit::loudness_follower::Parameters::default();
 let fb=rf_d_circuit::loudness_follower::Boundary{c2_v:p.c2_v,reset_base_v:p.reset_v,supply_v:9.3,load_conductance_s:1./68000.,load_reference_v:now.high[165]};
 let (fr,fj)=rf_d_circuit::loudness_follower::linearize(std::array::from_fn(|k|now.high[200+k]),fp,fb)?;
 s.dc[165]-=(now.high[203]+now.low[203])/68000.;s.dc_jacobian[165][203]-=1./68000.;
 for a in 0..5 {
  s.candidate.high[200+a]=now.high[200+a];s.candidate.low[200+a]=now.low[200+a];
  s.dc[200+a]=fr[a]+(0..5).map(|k|fj[a][k]*now.low[200+k]).sum::<f64>();
  for b in 0..5 {s.dc_jacobian[200+a][200+b]=fj[a][b];}
 }
 s.dc[203]-=now.low[165]/68000.;s.dc_jacobian[203][165]=-1./68000.;
'''
REPLACEMENTS=[('crate::','rf_d_circuit::'),('pub const N:usize=200;','pub const N:usize=205;'),
 ('pub controls:Controls,chain:Chain,pub sources:[f64;5]','pub controls:Controls,chain:Chain,pub sources:[f64;5],pub c2_v:f64,pub reset_v:f64'),
 ('Ok(Self{controls,chain,sources})','chain.boundary.recovery.vca.loudness_v=0.;Ok(Self{controls,chain,sources,c2_v:3.2,reset_v:0.01})'),
 (' if s.dc.iter()',ADDITION+' if s.dc.iter()'),
 ('(k>=133&&chain_charge::constraint_row','(k>=133&&k<200&&chain_charge::constraint_row')]
def rendered():
 s=(ROOT/'crates/rf-d-circuit/src/joint_voice.rs').read_text(encoding='utf8')
 for a,b in REPLACEMENTS:
  require(a in s,'declared replacement '+a);s=s.replace(a,b)
 return s
def main():
 previous='evidence/voice_cutoff_cycles_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'))
 require(old['passed'],'previous admitted');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 require(head=='b7b5f646d5cacfdcb0a46a4934b94682442ce610','base')
 write('evidence/voice_loudness_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 p=ROOT/'tools/joint_loudness_kernel.rs';require(not p.exists(),'exclusive generated source');p.write_text(rendered(),encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
 seed='references-local/cutoff-cycles01/32768/final.ckp';require(sha(ROOT/seed)==old['private_input_sha256'][seed],'exact incoming memory')
 write('evidence/voice_loudness_inputs01.json',dict(passed=True,seed_path=seed,seed_sha256=sha(ROOT/seed),start_ticks=2752512000,c2_values=[.8469345758149237,3.2,6.],reset_values=[.01,.7],step_s=[125e-9,62.5e-9],duration_s=2e-6,kernel_substitutions=REPLACEMENTS,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_joint_loudness.py','tools/joint_loudness_kernel.rs','tools/joint_loudness_runner.rs','crates/rf-d-circuit/src/joint_voice.rs','docs/VOZ_SEGUIDOR_PROTOCOLO.md']}))
 print('LOUDNESS_INPUTS',12)
if __name__=='__main__':main()
