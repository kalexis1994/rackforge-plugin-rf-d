"""Declare the loaded trigger closure with inherited217 memory and new C7/C4."""
import base64,json,struct,subprocess
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_c2_charge import checkpoint
from trigger_charge_reference import prepare
from joint_cycles_analysis import require
from repair_trigger_seed import PREDICTOR
START=2785017856;SPAN=1048576;SOURCES=[[8.3,0.,.01],[8.3,10.,.01],[8.3,10.,.01],[8.3,0.,.01],[8.3,0.,.7]];SHORT=[False,False,True,False,False]
ATTR=b'\n/tools/trigger_charge_driver.rs text eol=lf\n/tools/joint_trigger_kernel.rs text eol=lf\n/tools/joint_trigger_body.rs text eol=lf\n/tools/joint_trigger_runner.rs text eol=lf\n'
ADDITION='''
 let cg=1e-12*((now.high[214]-now.high[217])/(1.5*1.380649e-23*298.15/1.602176634e-19)).exp()/(1.5*1.380649e-23*298.15/1.602176634e-19);
 s.dc[214]-=cg*now.low[217];s.dc_jacobian[214][217]-=cg;s.dc[216]-=now.low[217]/1500.;s.dc_jacobian[216][217]-=1./1500.;
 s.dc[217]+=driver.ports[5]+(0..12).map(|b|driver.port_jacobian[5][b]*now.low[205+b]).sum::<f64>()+(cg+1./1500.)*now.low[217];
 for b in 0..12 {s.dc_jacobian[217][205+b]+=driver.port_jacobian[5][b];}s.dc_jacobian[217][217]+=cg+1./1500.;
 let tr=trigger_charge_driver::linearize(std::array::from_fn(|k|now.high[217+k]),trigger_charge_driver::Controls{keyboard:p.keyboard,reset_base:p.reset_v,short:p.short})?;
 for a in 0..8 {s.candidate.high[217+a]=now.high[217+a];s.candidate.low[217+a]=now.low[217+a];s.dc[217+a]+=tr.dc[a]+(0..8).map(|b|tr.jacobian[a][b]*now.low[217+b]).sum::<f64>();for b in 0..8 {s.dc_jacobian[217+a][217+b]+=tr.jacobian[a][b];}}
 for (k,c) in [(221,1e-7),(223,1e-8)] {s.charge_over_h[k]=c/h*(delta.high[k]+delta.low[k]);s.mass_over_h[k][k]=c/h;}
'''
def kernel():
 s=(ROOT/'tools/joint_c2_kernel.rs').read_text(encoding='utf8');s=s.replace('pub const N:usize=217;','pub const N:usize=225;').replace('pub final_decay:bool','pub final_decay:bool,pub keyboard:f64,pub short:bool,pub set_base:f64').replace('final_decay:true}','final_decay:true,keyboard:0.,short:false,set_base:0.01}')
 s=s.replace('reset_driver:p.reset_driver,final_decay:p.final_decay','reset_driver:now.high[217],final_decay:p.final_decay')
 s=s.replace(' if s.dc.iter()',ADDITION+' if s.dc.iter()')
 a=s.index(' if old.high[214]');b=s.index(' let mut delta=',a);s=s[:a]+''' if p.keyboard-(old.high[222]+old.low[222])>0.5 {seed[222]=p.keyboard-0.5-old.high[222]-old.low[222];}
'''+s[b:]
 s=s.replace(" let mut delta=[State::from_nodes(seed);2];",PREDICTOR+" let mut delta=[State::from_nodes(seed);2];")
 module='#[path="trigger_charge_driver.rs"] pub mod trigger_charge_driver;\n';i=s.index('use rf_d_circuit');return s[:i]+module+s[i:]
def caller():return (ROOT/'tools/joint_loudness_runner.rs').read_text(encoding='utf8').split('fn run()->')[0].replace('joint_loudness_kernel.rs','joint_trigger_kernel.rs')+(ROOT/'tools/joint_trigger_body.rs').read_text(encoding='utf8')
def main():
 old=__import__('json').loads((ROOT/'evidence/voice_c2_charge_tests01.json').read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='a238fed9d41510bc60c695e276630d4516121471','base');write('evidence/voice_trigger_charge_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_c2_charge_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}));work=ROOT/'references-local/trigger-charge-inputs01';require(not work.exists(),'exclusive inputs');work.mkdir();seeds=[]
 for on in [True,False]:
  for half in [65536,32768]:
   origin=f'references-local/c2-charge02/{int(on)}-{half}/final.ckp';require(sha(ROOT/origin)==old['private_input_sha256'][origin],'own217 seed')
   with localcontext() as ctx:ctx.prec=100;cp=checkpoint((ROOT/origin).read_bytes())
   require(cp['ticks']==START and cp['sources']==[8.3,.03,.01],'source recipe');v=cp['values'];nodes,diag=prepare(v[214]+v[431],v[216]+v[433],.01);high=[*v[:217],*nodes];low=[*v[217:],*([0.]*8)];raw=struct.pack('<8sQII4dII450d',b'RFLTRG01',START,half,0,*SOURCES[0],.01,int(on),0,*high,*low);require(len(raw)==3664,'225 codec');p=work/f'{int(on)}-{half}.ckp';p.write_bytes(raw);seeds.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),origin_path=origin,origin_sha256=sha(ROOT/origin),final_decay=on,half_ticks=half,algebraic_preparation=diag,new_c7_initial_v=0.,new_c4_initial_v=nodes[6]-.01))
 for n,s in [('tools/joint_trigger_kernel.rs',kernel()),('tools/joint_trigger_runner.rs',caller())]:
  p=ROOT/n;require(not p.exists(),'exclusive caller');p.write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);write('evidence/voice_trigger_charge_inputs01.json',dict(passed=True,start_ticks=START,phase_span_ticks=SPAN,sources=SOURCES,short_states=SHORT,set_base_v=.01,seeds=seeds,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_trigger_charge.py','tools/trigger_charge_driver.rs','tools/trigger_charge_reference.py','tools/joint_trigger_kernel.rs','tools/joint_trigger_body.rs','tools/joint_trigger_runner.rs','tools/joint_c2_kernel.rs','tools/joint_loudness_runner.rs','evidence/loudness_contour_graph.json','tools/loudness_contour_reference.py','docs/VOZ_GATILLO_CARGADO_PROTOCOLO.md']}));print('TRIGGER_INPUTS',len(seeds))
if __name__=='__main__':main()
