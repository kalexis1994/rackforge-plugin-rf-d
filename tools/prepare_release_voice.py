"""Resume each accepted released checkpoint without restarting its proposal/history."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
START=10717495296;SPAN=4194304000;BOUNDARIES=[0,SPAN];CUT=157286400
KEY=[0.];SHORT=[False];MAXIMUM=[1048576,524288]
EXAMPLE='crates/rf-d-circuit/examples/release_continuation.rs'
ATTR=('\n/'+EXAMPLE+' text eol=lf\n/tools/release_observers.rs text eol=lf\n').encode()
def cuts(phase):require(phase==0,'single continuation phase');return list(range(START+CUT,START+SPAN,CUT))+[START+SPAN]
def once(s,a,b):require(s.count(a)==1,'one continuation declaration '+a[:65]);return s.replace(a,b)

def caller():
 s=(ROOT/'crates/rf-d-circuit/examples/sustained_voice.rs').read_text(encoding='utf8');prefix=s[:s.index('// Offline replay storage')]
 decoder=prefix[prefix.index('fn decode('):prefix.index('fn observations(')]
 decoder=decoder.replace('fn decode(','fn incoming_decode(').replace('START','PARENT_START').replace('REL[','PARENT_REL[').replace('KEY[','PARENT_KEY[').replace('SHORT[','PARENT_SHORT[')
 prefix=prefix.replace('//! ON diagnostic: 4 us rest, 8 ms gate, 4 ms release; own public histories.','//! Continue released ON history by 8 ms; no new source event.')
 prefix=prefix.replace('VOZ_SOSTENIDA_PROTOCOLO','VOZ_LIBERACION_PROTOCOLO')
 prefix=once(prefix,'const START:u64=4423942144;const REL:[u64;4]=[0,2097152,4196401152,6293553152];','const START:u64=10717495296;const REL:[u64;2]=[0,4194304000];')
 prefix=once(prefix,'const KEY:[f64;3]=[0.,10.,0.];const SHORT:[bool;3]=[false,true,false];','const KEY:[f64;1]=[0.];const SHORT:[bool;1]=[false];')
 prefix=prefix.replace('RFHLD001','RFREL001').replace('phase>=3','phase!=0').replace('flags>3','flags!=1')
 prefix+='\nconst PARENT_START:u64=4423942144;const PARENT_REL:[u64;4]=[0,2097152,4196401152,6293553152];const PARENT_KEY:[f64;3]=[0.,10.,0.];const PARENT_SHORT:[bool;3]=[false,true,false];\n'+decoder
 body=(ROOT/'tools/sustained_voice_body.rs').read_text(encoding='utf8')
 a=body.index(' let args:Vec<_>');b=body.index(' for kind in 0..4')
 body=body[:a]+''' let args:Vec<_>=std::env::args().collect();if args.len()!=3{return Err("usage: release_continuation <sustained-final.ckp> <new-output-directory>".into());}
 let raw=fs::read(&args[1]).map_err(|e|e.to_string())?;let incoming=incoming_decode(&raw)?;
 if incoming.phase!=2||incoming.q.elapsed_ticks!=START||!incoming.q.parameters.final_decay||incoming.q.parameters.keyboard!=0.||incoming.q.parameters.short{return Err("released source recipe".into());}
 let mut converted=raw.clone();converted[..8].copy_from_slice(b"RFREL001");converted[28..32].copy_from_slice(&0_u32.to_le_bytes());let restored=decode(&converted)?;
 if encode(restored).as_slice()!=converted{return Err("only magic/phase may change".into());}
 let dir=std::path::Path::new(&args[2]);fs::create_dir(dir).map_err(|e|e.to_string())?;fs::write(dir.join("incoming-original.ckp"),raw).map_err(|e|e.to_string())?;
 let mut engine=temporal::Engine::restore(restored.q).map_err(|e|format!("own restore:{e:?}"))?;let mut workspace=joint::Workspace::new();let mut saved=restored;let bytes=encode(saved);
''' +body[b:]
 body=once(body,'for phase in 0..3{','for phase in 0..1{')
 body=once(body,'let end=START+REL[phase+1];if phase==0{return vec![end];}','let end=START+REL[phase+1];')
 a=body.index('  if phase==1{');b=body.index('  for target in targets{',a);body=body[:a]+body[b:]
 body=once(body,'engine.trigger(KEY[phase],SHORT[phase]).map_err(|e|format!("source:{e:?}"))?;','// Sources are inherited without a new trigger.')
 body=once(body,'if phase>0&&target==START+REL[phase]+CUT','if target==START+CUT')
 body=once(body,'||after.elapsed_ticks==START+788529152','||turn||flip')
 anchor=' let started=Instant::now();'
 body=once(body,anchor,''' let mut flux_file=std::io::BufWriter::new(fs::File::create(dir.join("flux.bin")).map_err(|e|e.to_string())?);flux_file.write_all(b"RFRELFX1").unwrap();
 let mut event_file=std::io::BufWriter::new(fs::File::create(dir.join("transitions.txt")).map_err(|e|e.to_string())?);
 let initial=initial_flux(saved.q.parameters,saved.q.state)?;write_flux(&mut flux_file,START,initial)?;
 let(mut last_slope,mut last_latch,mut last_c2,mut transition_count)=(initial[1],initial[5],initial[0],0);
'''+anchor)
 anchor='    if reset{add_probe'
 addition='''    let values=[endpoint_flux(&a.endpoints[0],h),endpoint_flux(&a.endpoints[1],h)];
    let(mut slope,mut latch)=(last_slope,last_latch);let(mut turn,mut flip)=(false,false);
    for x in values{turn|=slope>0.&&x[1]<=0.;flip|=(latch<0.&&x[5]>=0.)||(latch>=0.&&x[5]<0.);slope=x[1];latch=x[5];}
    if (turn||flip)&&!reset{add_probe(&mut probes,Saved{q:old,phase:0},format!("phase0-transition{transition_count}.ckp"),dir)?;restores+=1;max_probes=max_probes.max(probes.len());transition_count+=1;}
'''
 body=once(body,anchor,addition+anchor)
 anchor='    for ep in &a.endpoints{'
 body=once(body,anchor,'    for (ep,x) in a.endpoints.iter().zip(values){')
 anchor='     last_ramp=ep.observations.ramp_v;'
 addition='''     write_flux(&mut flux_file,ep.elapsed_ticks,x)?;
     if last_slope>0.&&x[1]<=0.{writeln!(event_file,"TURN,{last_ticks},{},{last_slope:.17e},{:.17e},{last_c2:.17e},{:.17e}",ep.elapsed_ticks,x[1],x[0]).unwrap();}
     if (last_latch<0.&&x[5]>=0.)||(last_latch>=0.&&x[5]<0.){writeln!(event_file,"LATCH,{last_ticks},{},{last_latch:.17e},{:.17e},{last_c2:.17e},{:.17e}",ep.elapsed_ticks,x[5],x[0]).unwrap();}
     last_slope=x[1];last_latch=x[5];last_c2=x[0];
'''
 body=once(body,anchor,addition+anchor)
 body=once(body,' w.flush().unwrap();cps.flush().unwrap();replay_log.flush().unwrap();',' flux_file.flush().unwrap();event_file.flush().unwrap();w.flush().unwrap();cps.flush().unwrap();replay_log.flush().unwrap();')
 return prefix+(ROOT/'tools/release_observers.rs').read_text(encoding='utf8')+body

def main():
 previous='evidence/voice_sustained_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='8110b386bad1640b9618603833a742dc0a9df43a','base')
 write('evidence/voice_release_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 p=ROOT/EXAMPLE;require(not p.exists(),'exclusive continuation caller');p.write_text(caller(),encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
 seeds=[]
 for maximum in MAXIMUM:
  n=f'references-local/sustained-voice01/{maximum}/final.ckp';require(sha(ROOT/n)==old['private_input_sha256'][n],'own final checkpoint');seeds.append(dict(maximum_half_ticks=maximum,path=n,sha256=sha(ROOT/n)))
 lib='references-local/conditioned-recipe-library02/librf_d_circuit.rlib';require(sha(ROOT/lib)==old['private_input_sha256'][lib],'frozen library')
 write('evidence/voice_release_inputs01.json',dict(passed=True,start_ticks=START,span_ticks=SPAN,source_event_applied=False,seeds=seeds,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_release_voice.py','tools/release_observers.rs',EXAMPLE,'docs/VOZ_LIBERACION_PROTOCOLO.md']},private_used_sha256={lib:sha(ROOT/lib),**{s['path']:s['sha256'] for s in seeds}},only_magic_and_recipe_phase_changed=True,new_library_compile=False))
 print('RELEASE_INPUTS',2,.008)
if __name__=='__main__':main()
