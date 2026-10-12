"""Declare source substitutions; reuse exact incoming states and charge memory."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
ATTR=b'\n/tools/joint_cutoff_temporal_runner.rs text eol=lf\n'
MARKS=[1048576,8388608,33554432,65536000,131072000]
REPLACEMENTS=[
 ('const GOAL:u64=5373952000;', 'const GOAL:u64=131072000;const MARKS:[u64;5]=[1048576,8388608,33554432,65536000,131072000];'),
 ('let p=Chain {', 'let mut p=Chain {'),
 (' let controls=Controls::default();', ' p.boundary.panel.cutoff_fraction_from_neg10=std::env::args().last().unwrap().parse().map_err(|_|"cutoff argument")?;\n let controls=Controls::default();'),
 ('let target=if before.elapsed_ticks<1048576 {1048576} else {((before.elapsed_ticks/ANCHOR+1)*ANCHOR).min(GOAL)};', 'let target=*MARKS.iter().find(|&&v|v>before.elapsed_ticks).unwrap();'),
 ('as_secs_f64()>7200.', 'as_secs_f64()>900.'),
 ('before.elapsed_ticks==ANCHOR||before.elapsed_ticks==9*ANCHOR||before.elapsed_ticks==29*ANCHOR', 'before.elapsed_ticks==0||before.elapsed_ticks==33554432'),
 ('let mut trace=BufWriter::new', 'let mut ctl=BufWriter::new(File::create(out.join("control.bin")).map_err(|e|e.to_string())?);ctl.write_all(b"RFJCTL01").map_err(|e|e.to_string())?;let mut control_charge=Sum::default();\n let mut trace=BufWriter::new'),
 ('let c1=1e-8/h*', '''let dc=std::array::from_fn::<_,2,_>(|i|joint::parts(p,old,e.pair.increments[i],h).unwrap().dc[195]);
    for (i,weight) in [0.75,0.25].into_iter().enumerate() {control_charge.add(h*weight*dc[i]);}
    let c18=100e-12/h*(joint::B[1][0]*(d[0].high[195]+d[0].low[195])+joint::B[1][1]*(d[1].high[195]+d[1].low[195]));let control_kcl=c18+dc[1];
    if control_kcl.abs()>1e-12 {return Err(format!("C18_KCL,{control_kcl:e}"));}
    let c1=1e-8/h*'''),
 ('let o=e.observations;', '''let o=e.observations;
    ctl.write_all(&e.elapsed_ticks.to_le_bytes()).map_err(|e|e.to_string())?;
    for x in [v(195),(v(138)-v(198))/680.,control_charge.value,control_kcl] {ctl.write_all(&x.to_le_bytes()).map_err(|e|e.to_string())?;}'''),
 ('steps==1||event||engine.checkpoint().elapsed_ticks==GOAL', 'steps==1||event||MARKS.contains(&engine.checkpoint().elapsed_ticks)'),
 ('engine.checkpoint().elapsed_ticks%ANCHOR==0||engine.checkpoint().elapsed_ticks==1048576', 'MARKS.contains(&engine.checkpoint().elapsed_ticks)'),
 ('events.flush().map_err', 'ctl.flush().map_err(|e|e.to_string())?;events.flush().map_err'),
 ('let target=((q.elapsed_ticks/ANCHOR+1)*ANCHOR).min(GOAL);', 'let target=*MARKS.iter().find(|&&v|v>q.elapsed_ticks).unwrap_or(&GOAL);'),
 ('if crossings!=4||restores!=3||balance>0.002', 'if crossings!=0||restores!=2||balance>0.002')]
def main():
 previous='evidence/voice_cutoff_opening_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='22373df61ad9f9e50766a719543f6ca47af899bc','base')
 write('evidence/voice_cutoff_temporal_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 s=(ROOT/'tools/joint_candidate_cycles_runner.rs').read_text(encoding='utf8')
 for a,b in REPLACEMENTS:require(s.count(a)==1,'single substitution '+a);s=s.replace(a,b)
 p=ROOT/'tools/joint_cutoff_temporal_runner.rs';require(not p.exists(),'exclusive caller');p.write_text(s,encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
 inputs=json.loads((ROOT/'evidence/voice_candidate_cycles_inputs01.json').read_text(encoding='utf8'));profiles=[]
 for knob in [.5,1.]:
  for seed in inputs['outputs']:
   require(sha(ROOT/seed['path'])==old['private_input_sha256'][seed['path']],'protected charge seed');profiles.append(dict(cutoff_fraction=knob,maximum_half_ticks=seed['maximum_half_ticks'],path=seed['path'],sha256=seed['sha256']))
 write('evidence/voice_cutoff_temporal_inputs01.json',dict(passed=True,profiles=profiles,marks=MARKS,goal_ticks=MARKS[-1],substitutions=REPLACEMENTS,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_cutoff_temporal.py','tools/joint_candidate_cycles_runner.rs','tools/joint_cutoff_temporal_runner.rs','docs/VOZ_CUTOFF_TEMPORAL_PROTOCOLO.md']}));print('CUTOFF_TEMPORAL_INPUTS',len(profiles))
if __name__=='__main__':main()
