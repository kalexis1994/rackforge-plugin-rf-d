"""Declare the simultaneous C2 extension and preserve exact own 205-node memory."""
import base64,json,struct,subprocess
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from check_loudness_control import checkpoint
from c2_charge_reference import prepare
START=2758803456;SPAN=5242880;SOURCES=[[8.3,9.,.7],[.05,9.,.7],[8.3,9.,.7],[8.3,.03,.7],[8.3,.03,.01]]
ATTR=b'\n/tools/c2_charge_driver.rs text eol=lf\n/tools/joint_c2_kernel.rs text eol=lf\n/tools/joint_c2_body.rs text eol=lf\n/tools/joint_c2_runner.rs text eol=lf\n'
ADDITION='''
 let driver=c2_charge_driver::linearize(std::array::from_fn(|k|now.high[205+k]),c2_charge_driver::Controls{q25:p.q25,reset_driver:p.reset_driver,final_decay:p.final_decay})?;
 for a in 0..12 {
  s.candidate.high[205+a]=now.high[205+a];s.candidate.low[205+a]=now.low[205+a];
  s.dc[205+a]+=driver.dc[a]+(0..12).map(|b|driver.jacobian[a][b]*now.low[205+b]).sum::<f64>();
  for b in 0..12 {s.dc_jacobian[205+a][205+b]+=driver.jacobian[a][b];}
 }
 s.dc[200]-=now.low[205]/10000.;s.dc_jacobian[200][205]-=1./10000.;
 s.dc[205]+=(now.high[205]-now.high[200]+now.low[205]-now.low[200])/10000.;s.dc_jacobian[205][205]+=1./10000.;s.dc_jacobian[205][200]-=1./10000.;
 s.charge_over_h[205]=1e-5/h*(delta.high[205]+delta.low[205]);s.mass_over_h[205][205]=1e-5/h;
'''
SEED='''let mut seed=[0.;N];
 if p.q25-(old.high[209]+old.low[209])>0.6 {seed[209]=p.q25-0.6-old.high[209]-old.low[209];}
 if old.high[214]+old.low[214]-p.reset_driver>0.5 {
  let emitter=p.reset_driver+0.5;seed[214]=emitter-old.high[214]-old.low[214];
  if old.high[210]+old.low[210]-emitter>0.6 {seed[210]=emitter+0.6-old.high[210]-old.low[210];}
 }
 if !p.final_decay&&old.high[205]+old.low[205]-old.high[216]-old.low[216]>0.5 {seed[216]=old.high[205]+old.low[205]-0.5-old.high[216]-old.low[216];}
 let mut delta=[State::from_nodes(seed);2];'''
REPLACEMENTS=[('pub const N:usize=205;','pub const N:usize=217;'),('pub c2_v:f64,pub reset_v:f64','pub c2_v:f64,pub reset_v:f64,pub q25:f64,pub reset_driver:f64,pub final_decay:bool'),('c2_v:3.2,reset_v:0.01','c2_v:3.2,reset_v:0.01,q25:8.3,reset_driver:9.,final_decay:true'),('c2_v:p.c2_v','c2_v:now.high[205]'),(' if s.dc.iter()',ADDITION+' if s.dc.iter()'),('let mut delta=[State::from_nodes([0.;N]);2];',SEED)]
def kernel():
 s=(ROOT/'tools/joint_loudness_kernel.rs').read_text(encoding='utf8')
 for a,b in REPLACEMENTS:require(s.count(a)==1,'single C2 replacement '+a);s=s.replace(a,b)
 i=s.index("use rf_d_circuit");return s[:i]+'#[path="c2_charge_driver.rs"] pub mod c2_charge_driver;\n'+s[i:]
def caller():return (ROOT/'tools/joint_loudness_runner.rs').read_text(encoding='utf8').split('fn run()->')[0].replace('joint_loudness_kernel.rs','joint_c2_kernel.rs')+(ROOT/'tools/joint_c2_body.rs').read_text(encoding='utf8')
def main():
 previous='evidence/voice_loudness_control_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='2fcfe7ef92e54f6b52bfab60f3d96f2fa7c77461','base')
 write('evidence/voice_c2_charge_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 work=ROOT/'references-local/c2-charge-inputs01';require(not work.exists(),'exclusive inputs');work.mkdir();seeds=[]
 for on in [True,False]:
  nodes,diagnostics=prepare(on)
  for half in [65536,32768]:
   origin=f'references-local/loudness-control01/{half}/final.ckp';require(sha(ROOT/origin)==old['private_input_sha256'][origin],'protected own seed')
   with localcontext() as ctx:ctx.prec=100;cp=checkpoint((ROOT/origin).read_bytes())
   require(cp['ticks']==START and cp['c2']==3.2 and cp['reset']==.7,'source to capacitor boundary');v=cp['values'];high=[*v[:205],*nodes];low=[*v[205:],*([0.]*12)];raw=b'RFLC2C01'+struct.pack('<QII3dII434d',START,half,0,*SOURCES[0],int(on),0,*high,*low);require(len(raw)==3528,'217 codec');p=work/f'{int(on)}-{half}.ckp';p.write_bytes(raw);seeds.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),origin_path=origin,origin_sha256=sha(ROOT/origin),final_decay=on,half_ticks=half,algebraic_preparation=diagnostics,new_c2_initial_v=3.2,new_c2_initial_charge_c=3.2e-5))
 for name,body in [('tools/joint_c2_kernel.rs',kernel()),('tools/joint_c2_runner.rs',caller())]:
  p=ROOT/name;require(not p.exists(),'exclusive generated source');p.write_text(body,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
 write('evidence/voice_c2_charge_inputs01.json',dict(passed=True,start_ticks=START,phase_span_ticks=SPAN,sources=SOURCES,seeds=seeds,kernel_substitutions=REPLACEMENTS,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_c2_charge.py','tools/c2_charge_reference.py','tools/c2_charge_driver.rs','tools/joint_c2_body.rs','tools/joint_c2_kernel.rs','tools/joint_c2_runner.rs','tools/joint_loudness_kernel.rs','tools/joint_loudness_runner.rs','evidence/loudness_contour_graph.json','tools/loudness_contour_reference.py','docs/VOZ_C2_CARGA_PROTOCOLO.md']}));print('C2_CHARGE_INPUTS',len(seeds))
if __name__=='__main__':main()
