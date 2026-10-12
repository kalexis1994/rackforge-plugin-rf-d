"""Freeze229 full board2, own225 histories and compatible Q25/Q15 mass."""
import base64,json,struct,subprocess
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_trigger_charge import checkpoint
from latch_charge_reference import network,NAMES,RAILS,charges,D
from joint_cycles_analysis import require
START=2790260736;SPAN=1048576;KEY=[0.,10.,10.,0.,0.];SHORT=[False,False,True,False,False]
NEW=[.01,8.3,.7,.05]
ATTR=b'\n/tools/latch_charge_driver.rs text eol=lf\n/tools/contour_closed_driver.rs text eol=lf\n/tools/joint_latch_kernel.rs text eol=lf\n/tools/joint_latch_body.rs text eol=lf\n/tools/joint_latch_runner.rs text eol=lf\n'
def driver():
 n=network(False,True);names=[*NAMES,'VCA_CONTROL_LOAD','GROUND','CONTOUR_SUPPLY','MINUS_10','PLUS_10','KEYBOARD_TRIGGER'];idx={k:i for i,k in enumerate(names)};idx['EXTERNAL_S_TRIGGER']=30
 s='''//! Full reviewed board2 graph; last unknown is the loaded VCA base port.
use rf_d_circuit::StepError;
pub const N:usize=30;
pub struct Stamp{pub dc:[f64;N],pub jacobian:[[f64;N];N],pub ports:[f64;5]}
fn v(x:&[f64;N],key:f64,k:usize)->f64{if k<N{x[k]}else{[0.,9.3,-10.,10.,key][k-N]}}
fn row(s:&mut Stamp,k:usize,i:f64,d:&[(usize,f64)]){if k<N{s.dc[k]+=i;for &(j,g)in d{if j<N{s.jacobian[k][j]+=g;}}}else{s.ports[k-N]+=i;}}
fn r(s:&mut Stamp,x:&[f64;N],key:f64,a:usize,b:usize,ohm:f64){let g=1./ohm;let i=(v(x,key,a)-v(x,key,b))*g;row(s,a,i,&[(a,g),(b,-g)]);row(s,b,-i,&[(a,-g),(b,g)]);}
fn diode(s:&mut Stamp,x:&[f64;N],key:f64,a:usize,b:usize,is:f64)->Result<(),StepError>{let vt=1.5*super::latch_charge_driver::VT;let z=(v(x,key,a)-v(x,key,b))/vt;if z>45.{return Err(StepError::ExponentialDomain);}let i=is*z.exp_m1();let g=is*z.exp()/vt;row(s,a,i,&[(a,g),(b,-g)]);row(s,b,-i,&[(a,-g),(b,g)]);Ok(())}
fn bjt(s:&mut Stamp,x:&[f64;N],key:f64,sign:f64,b:usize,c:usize,e:usize)->Result<(),StepError>{let vt=super::latch_charge_driver::VT;let be=sign*(v(x,key,b)-v(x,key,e))/vt;let bc=sign*(v(x,key,b)-v(x,key,c))/vt;if be>45.||bc>45.{return Err(StepError::ExponentialDomain);}let f=1e-14*be.exp_m1();let rr=1e-14*bc.exp_m1();let gf=1e-14*be.exp()/vt;let gr=1e-14*bc.exp()/vt;let ib=f/100.+rr/5.;let ic=f-1.2*rr;row(s,b,sign*ib,&[(b,gf/100.+gr/5.),(e,-gf/100.),(c,-gr/5.)]);row(s,c,sign*ic,&[(b,gf-1.2*gr),(e,-gf),(c,1.2*gr)]);row(s,e,-sign*(ib+ic),&[(b,-gf-gf/100.+gr),(e,gf+gf/100.),(c,-gr)]);Ok(())}
pub fn linearize(x:[f64;N],key:f64,on:bool,short:bool)->Result<Stamp,StepError>{
 if x.iter().any(|v|!v.is_finite())||!key.is_finite()||!(0. ..=10.).contains(&key){return Err(StepError::InvalidInput);}
 let mut s=Stamp{dc:[0.;N],jacobian:[[0.;N];N],ports:[0.;5]};
'''
 for ref,a,b,ohm in n.resistors:
  prefix='if short{' if ref=='R49' else ''
  s+=f' {prefix}r(&mut s,&x,key,{idx[a]},{idx[b]},{float(ohm)!r});'+('}' if prefix else '')+f' // {ref}\n'
 for p in n.bjts:s+=f' bjt(&mut s,&x,key,{1. if p["kind"]=="NPN" else -1.},{idx[p["base"]]},{idx[p["collector"]]},{idx[p["emitter"]]})?; // {p["ref"]}\n'
 for p in n.diodes:
  prefix='if !on{' if p['ref']=='CR4' else ''
  s+=f' {prefix}diode(&mut s,&x,key,{idx[p["anode"]]},{idx[p["cathode"]]},{1e-8 if p["marking"]=="1N34A" else 1e-12})?;'+('}' if prefix else '')+f' // {p["ref"]}\n'
 return s+' Ok(s)\n}\n'
ADDITION='''
 s.dc[165]-=(now.high[165]+now.low[165])/68000.;s.dc_jacobian[165][165]-=1./68000.;
 let map=|k:usize|if k<29{200+k}else{165};
 let tr=contour_closed_driver::linearize(std::array::from_fn(|k|now.high[map(k)]),p.keyboard,p.final_decay,p.short)?;
 for a in 0..30{let i=map(a);s.candidate.high[i]=now.high[i];s.candidate.low[i]=now.low[i];s.dc[i]+=tr.dc[a]+(0..30).map(|b|tr.jacobian[a][b]*now.low[map(b)]).sum::<f64>();for b in 0..30{s.dc_jacobian[i][map(b)]+=tr.jacobian[a][b];}}
 for (a,b,c) in [(205,None,1e-5),(221,None,1e-7),(223,Some(225),1e-8)]{
  let d=c/h*(delta.high[a]+delta.low[a]-b.map_or(0.,|k|delta.high[k]+delta.low[k]));s.charge_over_h[a]+=d;s.mass_over_h[a][a]+=c/h;
  if let Some(b)=b{s.charge_over_h[b]-=d;s.mass_over_h[a][b]-=c/h;s.mass_over_h[b][a]-=c/h;s.mass_over_h[b][b]+=c/h;}
 }
 for(b,c)in[(225,226),(227,228)]{
  let(q,m)=latch_charge_driver::terminal([(old.high[b],old.low[b]),(old.high[c],old.low[c])],[(now.high[b],now.low[b]),(now.high[c],now.low[c])])?;
  for(a,i)in[b,c].into_iter().enumerate(){s.charge_over_h[i]+=q[a]/h;for(k,j)in[b,c].into_iter().enumerate(){s.mass_over_h[i][j]+=m[a][k]/h;}}
 }
'''
def kernel():
 s=(ROOT/'tools/joint_trigger_kernel.rs').read_text(encoding='utf8');s=s.replace('pub const N:usize=225;','pub const N:usize=229;')
 a=s.index('#[path="c2_charge_driver.rs"]');b=s.index('use rf_d_circuit',a);s=s[:a]+'#[path="latch_charge_driver.rs"] pub mod latch_charge_driver;\n#[path="contour_closed_driver.rs"] pub mod contour_closed_driver;\n'+s[b:]
 a=s.index(' let fp=');b=s.index(' if s.dc.iter()',a);s=s[:a]+ADDITION+s[b:]
 a=s.index(' let mut seed=');b=s.index(' let mut delta=',a);s=s[:a]+' let seed=[0.;N];\n'+s[b:]
 return s
def caller():return (ROOT/'tools/joint_loudness_runner.rs').read_text(encoding='utf8').split('fn run()->')[0].replace('joint_loudness_kernel.rs','joint_latch_kernel.rs')+(ROOT/'tools/joint_latch_body.rs').read_text(encoding='utf8')
def main():
 previous='evidence/voice_trigger_charge_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='137c4cf58c585705bd8eb328449ccfda4c18e309','base');write('evidence/voice_latch_charge_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}));work=ROOT/'references-local/latch-charge-inputs01';require(not work.exists(),'exclusive seeds');work.mkdir();seeds=[]
 for on in [True,False]:
  for half,origin_half in [(16384,65536),(8192,32768)]:
   origin=f'references-local/trigger-charge02/{int(on)}-{origin_half}/final.ckp';require(sha(ROOT/origin)==old['private_input_sha256'][origin],'own225 seed')
   with localcontext() as ctx:
    ctx.prec=100;cp=checkpoint((ROOT/origin).read_bytes());require(cp['ticks']==START,'absolute calendar');v=cp['values'];high=[*v[:225],*NEW];low=[*v[225:],0.,0.,0.,0.];q,_=charges([D(a)+D(b) for a,b in zip(high,low)])
   raw=struct.pack('<8sQII2dII458d',b'RFLATCH1',START,half,0,KEY[0],1.,int(on),0,*high,*low);require(len(raw)==3712,'229 codec');p=work/f'{int(on)}-{half}.ckp';p.write_bytes(raw);seeds.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),origin_path=origin,origin_sha256=sha(ROOT/origin),final_decay=on,half_ticks=half,origin_half_ticks=origin_half,new_node_bias_v=NEW,new_terminal_charge_c=[str(q[k]) for k in range(225,229)]))
 for n,s in [('tools/contour_closed_driver.rs',driver()),('tools/joint_latch_kernel.rs',kernel()),('tools/joint_latch_runner.rs',caller())]:
  p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);names=['tools/prepare_latch_charge.py','tools/latch_charge_driver.rs','tools/latch_charge_reference.py','tools/contour_closed_driver.rs','tools/joint_latch_kernel.rs','tools/joint_latch_body.rs','tools/joint_latch_runner.rs','tools/joint_trigger_kernel.rs','evidence/loudness_contour_graph.json','docs/VOZ_BIESTABLE_CARGADO_PROTOCOLO.md'];write('evidence/voice_latch_charge_inputs01.json',dict(passed=True,start_ticks=START,phase_span_ticks=SPAN,keyboard=KEY,short_states=SHORT,seeds=seeds,source_sha256={n:sha(ROOT/n) for n in names}));print('LATCH_INPUTS',len(seeds))
if __name__=='__main__':main()
