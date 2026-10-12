"""Extend the same229 time contract, preserving the finer complete history."""
import base64,json,struct,subprocess
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_contour_engine import checkpoint
from joint_cycles_analysis import require
START=2848980992;BOUNDARIES=[0,2097152,788529152,1574961152];CUT=157286400
KEY=[0.,10.,0.];SHORT=[False,True,False];MAXIMUM=[1048576,524288]
ATTR=b'\n/tools/contour_reset_engine.rs text eol=lf\n/tools/joint_contour_reset_body.rs text eol=lf\n/tools/joint_contour_reset_runner.rs text eol=lf\n'
def engine():return (ROOT/'tools/contour_engine.rs').read_text(encoding='utf8').replace('(4..=131072).contains','(4..=1048576).contains')
def body():
 s=(ROOT/'tools/joint_contour_body.rs').read_text(encoding='utf8');s=s.replace('START:u64=2795503616','START:u64=2848980992').replace('[0,1048576,27262976,53477376]','[0,2097152,788529152,1574961152]').replace('CUT:u64=5242880','CUT:u64=157286400').replace('RFCTRE01','RFMCTR01').replace('![131072,65536].contains','![1048576,524288].contains').replace('>300.','>900.')
 s=s.replace('let started=Instant::now();','let started=Instant::now();let mut last_ramp=engine.checkpoint().state.high[43]+engine.checkpoint().state.low[43];let mut last_ticks=START;let mut crossing_count=0;')
 s=s.replace('let mut inside=None;','let mut inside=None;let mut reset_points=Vec::new();')
 s=s.replace('if started.elapsed().as_secs_f64()>900.{return Err("wall budget".into());}', 'if started.elapsed().as_secs_f64()>900.{fs::write(dir.join("budget.ckp"),encode(Saved{q:engine.checkpoint(),phase:phase as u32})).unwrap();return Err("wall budget".into());}')
 s=s.replace('let a=engine.advance_to(target).map_err(|e|format!("advance,phase={phase},ticks={}:{e:?}",old.elapsed_ticks))?;', '''let a=match engine.advance_to(target){Ok(a)=>a,Err(e)=>{if encode(Saved{q:old,phase:phase as u32})!=encode(Saved{q:engine.checkpoint(),phase:phase as u32}){return Err("rejection mutated state".into());}fs::write(dir.join("rejected.ckp"),encode(Saved{q:old,phase:phase as u32})).unwrap();fs::write(dir.join("rejected-target.bin"),target.to_le_bytes()).unwrap();return Err(format!("advance,phase={phase},ticks={}:{e:?}",old.elapsed_ticks));}};''')
 s=s.replace('if records.is_empty()||after.elapsed_ticks==end{','''let mut ramp=last_ramp;let reset=a.endpoints.iter().any(|ep|{let v=ep.observations.ramp_v;let crossed=ramp< -2.&&v>= -2.;ramp=v;crossed});
    if reset{let point=Saved{q:old,phase:phase as u32};let name=format!("phase{phase}-reset{crossing_count}.ckp");fs::write(dir.join(&name),encode(point)).unwrap();reset_points.push((records.len(),name,point));}
    if records.is_empty()||after.elapsed_ticks==end||reset{''')
 s=s.replace('writeln!(w).unwrap();predecessor=ep.pair.candidates[1];','''writeln!(w).unwrap();if last_ramp< -2.&&ep.observations.ramp_v>= -2.{writeln!(w,"RESET,{phase},{last_ticks},{},{last_ramp:.17e},{:.17e}",ep.elapsed_ticks,ep.observations.ramp_v).unwrap();crossing_count+=1;}last_ramp=ep.observations.ramp_v;last_ticks=ep.elapsed_ticks;predecessor=ep.pair.candidates[1];''')
 s=s.replace('for(k,name,expected)in points{','points.extend(reset_points);for(k,name,expected)in points{').replace('for j in k..records.len(){','for j in k..(k+16).min(records.len()){')
 s=s.replace('writeln!(w,"TOTAL").unwrap();','if crossing_count==0{return Err("missing VCO reset".into());}writeln!(w,"TOTAL").unwrap();').replace('rollbacks={rollbacks},wall_s=', 'rollbacks={rollbacks},crossings={crossing_count},wall_s=');return s
def caller():
 s=(ROOT/'tools/joint_contour_runner.rs').read_text(encoding='utf8').split('// All IO')[0].replace('contour_engine.rs','contour_reset_engine.rs');return s+body()
def main():
 previous='evidence/voice_contour_engine_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='938a36f9a9e9313e247e1306053b965f9e0a51ce','base');write('evidence/voice_contour_reset_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}));work=ROOT/'references-local/contour-reset-inputs01';require(not work.exists(),'exclusive inputs');work.mkdir();seeds=[]
 for on in [True,False]:
  origin=f'references-local/contour-engine01/{int(on)}-65536/final.ckp';require(sha(ROOT/origin)==old['private_input_sha256'][origin],'own229 seed')
  with localcontext() as ctx:ctx.prec=100;cp=checkpoint((ROOT/origin).read_bytes())
  require(cp['ticks']==START and cp['key']==0. and not cp['short'],'calendar')
  for maximum in MAXIMUM:
   raw=struct.pack('<8sQ6IdQ458d',b'RFMCTR01',START,maximum,20,maximum*2,0,1,int(on),KEY[0],0,*cp['values']);p=work/f'{int(on)}-{maximum}.ckp';p.write_bytes(raw);seeds.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),origin_path=origin,origin_sha256=sha(ROOT/origin),final_decay=on,maximum_half_ticks=maximum))
 for n,s in [('tools/contour_reset_engine.rs',engine()),('tools/joint_contour_reset_body.rs',body()),('tools/joint_contour_reset_runner.rs',caller())]:
  p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);names=['tools/prepare_contour_reset.py','tools/contour_reset_engine.rs','tools/joint_contour_reset_body.rs','tools/joint_contour_reset_runner.rs','tools/contour_engine.rs','tools/joint_contour_body.rs','tools/joint_latch_kernel.rs','tools/latch_charge_driver.rs','tools/contour_closed_driver.rs','docs/VOZ_CONTORNO_RESET_PROTOCOLO.md'];write('evidence/voice_contour_reset_inputs01.json',dict(passed=True,start_ticks=START,boundaries_relative_ticks=BOUNDARIES,keyboard=KEY,short_states=SHORT,seeds=seeds,maximum_half_ticks=MAXIMUM,source_sha256={n:sha(ROOT/n) for n in names}));print('CONTOUR_RESET_INPUTS',len(seeds))
if __name__=='__main__':main()
