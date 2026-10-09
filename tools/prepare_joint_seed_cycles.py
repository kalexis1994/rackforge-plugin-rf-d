"""Freeze the prior release and create exact roots/checkpoints for new histories."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import checkpoint,require

def caller():
    text=(ROOT/'tools/joint_conditioned_cycles_runner.rs').read_text(encoding='utf8')
    changes=[
      ('q.elapsed_ticks!=262144000','q.elapsed_ticks!=0'),
      ('conditioned prefix metadata','conditioned charge seed metadata'),
      ('let target=((before.elapsed_ticks/ANCHOR+1)*ANCHOR).min(GOAL);','let target=if before.elapsed_ticks<1048576 {1048576} else {((before.elapsed_ticks/ANCHOR+1)*ANCHOR).min(GOAL)};'),
      ('let mut charge=Sum::default();let mut absolute=Sum::default();','let mut charge=Sum::default();let mut absolute=Sum::default();let mut means:[Sum;5]=std::array::from_fn(|_|Sum::default());'),
      ('let s=e.pair.candidates[1];let v=|k|s.high[k]+s.low[k];let o=e.observations;', '''for (stage,weight) in e.pair.candidates.into_iter().zip([0.75,0.25]) {
     let v=|k|stage.high[k]+stage.low[k];let saw=v(46);let bus=v(12);let input=v(joint::chain_index(6));let series=(v(39)-bus)/33000.;
     for(k,value)in [saw,bus,input,series,0.5*saw-bus].into_iter().enumerate() {means[k].add(h*weight*value);}
    }
    let s=e.pair.candidates[1];let v=|k|s.high[k]+s.low[k];let o=e.observations;'''),
      ('writeln!(events,"EVENT,{},{},{:.17e},{:.17e}",e.elapsed_ticks-u64::from(accepted.half_ticks),e.elapsed_ticks,charge.value,absolute.value).map_err(|e|e.to_string())?;', '''write!(events,"EVENT,{},{},{:.17e},{:.17e}",e.elapsed_ticks-u64::from(accepted.half_ticks),e.elapsed_ticks,charge.value,absolute.value).map_err(|e|e.to_string())?;
     for mean in &means {write!(events,",{:.17e}",mean.value).map_err(|e|e.to_string())?;}writeln!(events).map_err(|e|e.to_string())?;'''),
      ('engine.checkpoint().elapsed_ticks%ANCHOR==0','engine.checkpoint().elapsed_ticks%ANCHOR==0||engine.checkpoint().elapsed_ticks==1048576'),
      ('if balance>0.002 {return Err("final cycle/restore/balance gate".into());}', '''eprint!("MEAN_LEDGER");for mean in &means {eprint!(",{:.17e}",mean.value);}eprintln!();
 if balance>0.002 {return Err("final cycle/restore/balance gate".into());}''')]
    for a,b in changes:require(text.count(a)==1,'single caller substitution '+a);text=text.replace(a,b)
    return text

def main():
    previous='evidence/voice_joint_charge_seed_tests01.json';q=json.loads((ROOT/previous).read_text());require(q['passed'],'admitted prior block')
    for key in ['source_sha256','private_input_sha256']:
        for n,h in q[key].items():require(sha(ROOT/n)==h,'protected '+n)
    names=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','.gitattributes']
    write('evidence/voice_joint_seed_cycles_before01.json',dict(schema='rf-d/joint-seed-cycles-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    p=ROOT/'tools/joint_seed_cycles_runner.rs';require(not p.exists(),'new lab caller');p.write_text(caller(),encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_seed_cycles_runner.rs text eol=lf\n')
    native='evidence/voice_joint_charge_seed_native02.json';data=json.loads((ROOT/native).read_text());lines=data['commands'][-1]['stdout'].splitlines();rows={}
    for i,line in enumerate(lines):
        if line.startswith('CHARGE_ROOT,'):
            id,guess=map(int,line.split(',')[1:3])
            if guess==0:rows[id]=list(map(float,lines[i+1].split(',')[1:]))
    require(set(rows)=={0,1} and all(len(r)==400 for r in rows.values()),'two exact native roots')
    directory=ROOT/'references-local/joint-seed-cycle-inputs01';require(not directory.exists(),'new root inputs');directory.mkdir();outputs=[]
    for id,raw in rows.items():
        for maximum in [65536,32768]:
            p=directory/f'{id}-{maximum}.ckp';blob=struct.pack('<QIIII400d',0,2*maximum,maximum,20,0,*raw);p.write_bytes(blob);cp=checkpoint(blob);require(list(cp['high'])+list(cp['low'])==raw,'root byte restoration')
            outputs.append(dict(id=id,maximum_half_ticks=maximum,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=len(blob)))
    write('evidence/voice_joint_seed_cycles_inputs01.json',dict(schema='rf-d/joint-seed-cycle-inputs/v1',passed=True,native_seed_source=native,native_seed_sha256=sha(ROOT/native),source_sha256={'tools/prepare_joint_seed_cycles.py':sha(ROOT/'tools/prepare_joint_seed_cycles.py')},outputs=outputs,start_ticks=0,proposal_rule='from_conditioned:2*maximum_half_ticks',targets_are_distinct_histories=True))
    print('SEED_CYCLES_PREPARED',len(q['source_sha256']),len(q['private_input_sha256']),flush=True)
if __name__=='__main__':main()
