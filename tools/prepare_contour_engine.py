"""Bind the admitted adaptive engine to229 and freeze own full histories."""
import base64,json,struct,subprocess
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_latch_charge import checkpoint
from joint_cycles_analysis import require
START=2795503616;BOUNDARIES=[0,1048576,27262976,53477376]
KEY=[0.,10.,0.];SHORT=[False,True,False]
ATTR=b'\n/tools/contour_engine.rs text eol=lf\n/tools/joint_contour_body.rs text eol=lf\n/tools/joint_contour_runner.rs text eol=lf\n'
DOMAIN='''  if !q.parameters.keyboard.is_finite()||!(0. ..=10.).contains(&q.parameters.keyboard){return Err(Error::InvalidInput);}
  let mut trial=[0.;N];
  if q.parameters.keyboard-(q.state.high[222]+q.state.low[222])>0.5{trial[222]=q.parameters.keyboard-0.5-q.state.high[222]-q.state.low[222];}
  joint::parts(q.parameters,q.state,State::from_nodes(trial),4.*TICK_S).map_err(|_|Error::InvalidInput)?;
'''
EVENT=''' /// Explicit ideal sources; no state or accepted charge is assigned.
 pub fn trigger(&mut self,key:f64,short:bool)->Result<(),Error>{
  if !key.is_finite()||!(0. ..=10.).contains(&key){return Err(Error::InvalidInput);}
  self.checkpoint.parameters.keyboard=key;self.checkpoint.parameters.short=short;Ok(())
 }
'''
def engine():
 s=(ROOT/'crates/rf-d-circuit/src/joint_engine.rs').read_text(encoding='utf8');s=s.replace('use crate::{joint_voice::{self as joint,State,N},joint_vco_fine::two_sum,StepError};','use super::joint::{self,State,N};\nuse rf_d_circuit::StepError;\nfn two_sum(a:f64,b:f64)->(f64,f64){let s=a+b;let v=s-a;(s,(a-(s-v))+(b-v))}')
 s=s.replace('crate::vco1_engine::TICK_S','rf_d_circuit::vco1_engine::TICK_S');s=s.replace('  joint::parts(q.parameters,q.state,State::from_nodes([0.;N]),4.*TICK_S).map_err(|_|Error::InvalidInput)?;\n',DOMAIN);s=s.replace(' pub fn checkpoint(&self)->Checkpoint {self.checkpoint}',EVENT+' pub fn checkpoint(&self)->Checkpoint {self.checkpoint}');return s
def caller():
 s=(ROOT/'tools/joint_loudness_runner.rs').read_text(encoding='utf8').split('fn run()->')[0].replace('joint_loudness_kernel.rs','joint_latch_kernel.rs');s=s.replace('use std::{fs,io::Write,time::Instant};','use std::{fs,io::Write,time::Instant};\n#[path="contour_engine.rs"] mod temporal;');return s+(ROOT/'tools/joint_contour_body.rs').read_text(encoding='utf8')
def main():
 previous='evidence/voice_latch_charge_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='5595f14b4f7829f6ac1a31cfa05faba5fa0c7739','base');write('evidence/voice_contour_engine_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}));work=ROOT/'references-local/contour-engine-inputs01';require(not work.exists(),'exclusive inputs');work.mkdir();seeds=[]
 for on in [True,False]:
  origin=f'references-local/latch-charge04/{int(on)}-4096/final.ckp';require(sha(ROOT/origin)==old['private_input_sha256'][origin],'own229 seed')
  with localcontext() as ctx:ctx.prec=100;cp=checkpoint((ROOT/origin).read_bytes())
  require(cp['ticks']==START and cp['key']==0. and not cp['short'],'calendar')
  for maximum in [131072,65536]:
   raw=struct.pack('<8sQ6IdQ458d',b'RFCTRE01',START,maximum,20,maximum*2,0,1,int(on),KEY[0],0,*cp['values']);require(len(raw)==3720,'adaptive229 codec');p=work/f'{int(on)}-{maximum}.ckp';p.write_bytes(raw);seeds.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),origin_path=origin,origin_sha256=sha(ROOT/origin),final_decay=on,maximum_half_ticks=maximum))
 for n,s in [('tools/contour_engine.rs',engine()),('tools/joint_contour_runner.rs',caller())]:
  p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);names=['tools/prepare_contour_engine.py','tools/contour_engine.rs','tools/joint_contour_body.rs','tools/joint_contour_runner.rs','tools/joint_latch_kernel.rs','tools/latch_charge_driver.rs','tools/contour_closed_driver.rs','crates/rf-d-circuit/src/joint_engine.rs','docs/VOZ_CONTORNO_ADAPTATIVO_PROTOCOLO.md'];write('evidence/voice_contour_engine_inputs01.json',dict(passed=True,start_ticks=START,boundaries_relative_ticks=BOUNDARIES,keyboard=KEY,short_states=SHORT,seeds=seeds,source_sha256={n:sha(ROOT/n) for n in names}));print('CONTOUR_INPUTS',len(seeds))
if __name__=='__main__':main()
