"""Generate an IO-only continuation caller; preserve the measured original."""
import base64,json
from prepare_vco1_portable import ROOT,sha,write
def continuation_source():
    source=(ROOT/'tools/joint_cycles_runner.rs').read_text(encoding='utf8')
    replacements=[
      ('fn run(maximum:u32,out:&Path,limit:usize)', 'fn run(maximum:u32,out:&Path,limit:usize,restore:&Path)'),
      ('let(p,initial)=scene()?;let mut engine=Engine::from_conditioned(p,initial,Settings{maximum_half_ticks:maximum,attempt_limit:20}).map_err(|e|format!("init:{e:?}"))?;',
       'let(p,seed)=scene()?;let mut engine=if restore.to_str()==Some("-") {Engine::from_conditioned(p,seed,Settings{maximum_half_ticks:maximum,attempt_limit:20})} else {let q=decode(&fs::read(restore).map_err(|e|e.to_string())?,p)?;if q.settings.maximum_half_ticks!=maximum {return Err("profile mismatch".into());}Engine::restore(q)}.map_err(|e|format!("init:{e:?}"))?;let initial=engine.checkpoint().state;'),
      ('started.elapsed().as_secs_f64()>900.', 'started.elapsed().as_secs_f64()>1800.'),
      ('if crossings<2||restores!=2||balance>0.002', 'if balance>0.002'),
      ('a[4].parse().unwrap())} else', 'a[4].parse().unwrap(),Path::new(&a[5]))} else'),
    ]
    for before,after in replacements:
        assert source.count(before)==1,before;source=source.replace(before,after)
    return source
def main():
    previous='evidence/voice_joint_cycles_native01.json';report=json.loads((ROOT/previous).read_text());assert not report['passed']
    for n,h in report['source_sha256'].items():assert sha(ROOT/n)==h,n
    for o in report['outputs']:assert sha(ROOT/o['path'])==o['sha256'],o['path']
    write('evidence/voice_joint_cycles_extension01.json',dict(schema='rf-d/joint-cycles-resource-extension/v1',previous_receipt_sha256=sha(ROOT/previous),reason='Measured CPU cost exceeds original per-profile budget. Continue exact checkpoint histories; reuse completed prefix/profile. No numerical/physical gates change.',before_base64={'tools/joint_cycles_runner.rs':base64.b64encode((ROOT/'tools/joint_cycles_runner.rs').read_bytes()).decode()},cached_library='references-local/joint-cycles01/librf_d_circuit.rlib',cached_library_sha256=sha(ROOT/'references-local/joint-cycles01/librf_d_circuit.rlib'),new_process_budget_s=1800,new_global_budget_s=2100,aggregate_crossing_gate=2,aggregate_restore_gate=2,estimated_additional_bytes=28*1024**2,strip_only_debug_metadata=True))
    target=ROOT/'tools/joint_cycles_resume_runner.rs';assert not target.exists();target.write_text(continuation_source(),encoding='utf8',newline='\n')
    print('CYCLES_EXTENSION_READY')
if __name__=='__main__':main()
