"""Freeze the admitted prefix and derive its exact checkpoint continuation."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
def caller():
    text=(ROOT/'tools/joint_cycles_resume_runner.rs').read_text(encoding='utf8')
    old='let(p,seed)=scene()?;let mut engine=if restore.to_str()==Some("-") {Engine::from_conditioned(p,seed,Settings{maximum_half_ticks:maximum,attempt_limit:20})} else {let q=decode(&fs::read(restore).map_err(|e|e.to_string())?,p)?;if q.settings.maximum_half_ticks!=maximum {return Err("profile mismatch".into());}Engine::restore(q)}.map_err(|e|format!("init:{e:?}"))?;let initial=engine.checkpoint().state;'
    new='let(p,_)=scene()?;let q=decode(&fs::read(restore).map_err(|e|e.to_string())?,p)?;if q.settings.maximum_half_ticks!=maximum||q.elapsed_ticks!=262144000 {return Err("conditioned prefix metadata".into());}let mut engine=Engine::restore(q).map_err(|e|format!("init:{e:?}"))?;let initial=engine.checkpoint().state;'
    changes=[(old,new),
      ('let mut steps=0;let mut crossings=0;', 'let mut events=BufWriter::new(File::create(out.join("events.txt")).map_err(|e|e.to_string())?);writeln!(events,"RFJEVENT01").map_err(|e|e.to_string())?;let mut steps=0;let mut crossings=0;'),
      ('last_ramp=o.ramp_v;old=s;', '''if last_ramp< -2.&&o.ramp_v>= -2. {
     writeln!(events,"EVENT,{},{},{:.17e},{:.17e}",e.elapsed_ticks-u64::from(accepted.half_ticks),e.elapsed_ticks,charge.value,absolute.value).map_err(|e|e.to_string())?;
     for state in [old,s] {write!(events,"JOINT_STATE").map_err(|e|e.to_string())?;for x in state.high.into_iter().chain(state.low) {write!(events,",{x:.17e}").map_err(|e|e.to_string())?;}writeln!(events).map_err(|e|e.to_string())?;}
    }
    last_ramp=o.ramp_v;old=s;'''),
      ('trace.flush().map_err(|e|e.to_string())?;checks.flush()', 'events.flush().map_err(|e|e.to_string())?;trace.flush().map_err(|e|e.to_string())?;checks.flush()')]
    for a,b in changes:assert text.count(a)==1,a;text=text.replace(a,b)
    return text
def main():
    previous='evidence/voice_joint_prefix_tests01.json';q=json.loads((ROOT/previous).read_text());assert q['passed']
    for key in ['source_sha256','private_input_sha256']:
        for n,h in q[key].items():assert sha(ROOT/n)==h,n
    names=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','.gitattributes']
    write('evidence/voice_joint_conditioned_cycles_before01.json',dict(schema='rf-d/joint-conditioned-cycles-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    p=ROOT/'tools/joint_conditioned_cycles_runner.rs';assert not p.exists();p.write_text(caller(),encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_conditioned_cycles_runner.rs text eol=lf\n')
    print('CONDITIONED_CYCLES_BEFORE',len(q['source_sha256']),len(q['private_input_sha256']),flush=True)
if __name__=='__main__':main()
