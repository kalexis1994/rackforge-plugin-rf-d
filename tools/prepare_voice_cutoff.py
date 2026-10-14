"""Declare cutoff close/reopen from own charged state with a complete recipe codec."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import once
from joint_cycles_analysis import require
START=82022760448;BOUNDARIES=[0,2097152,4196401152,8390705152];SPAN=BOUNDARIES[-1];CUT=419430400
KEY=[0.,0.,0.];SHORT=[False]*3;DECAY=1000.;ALPHA=[1.,.5,1.]
EXAMPLE='crates/rf-d-circuit/examples/voice_cutoff.rs';ATTR=b'\n/crates/rf-d-circuit/examples/voice_cutoff.rs text eol=lf\n'
def cuts(phase):return list(range(START+BOUNDARIES[phase]+CUT,START+BOUNDARIES[phase+1],CUT))+[START+BOUNDARIES[phase+1]]
def caller():
 s=(ROOT/'crates/rf-d-circuit/examples/voice_retrigger.rs').read_text(encoding='utf8').replace('//! Retrigger the loaded own history: 4 us rest, 8 ms gate, 8 ms release.','//! Loaded cutoff: 4 us continuity, 8 ms alpha=0.5, 8 ms alpha=1.').replace('VOZ_RETRIGGER_PROTOCOLO','VOZ_CUTOFF_PROTOCOLO').replace('const START:u64=73632055296','const START:u64=82022760448').replace('const SIZE:usize=3728','const SIZE:usize=3736').replace('const KEY:[f64;3]=[0.,10.,0.];const SHORT:[bool;3]=[false,true,false];','const KEY:[f64;3]=[0.;3];const SHORT:[bool;3]=[false;3];const ALPHA:[f64;3]=[1.,0.5,1.];').replace('RFDCY001','RFCTF001')
 a=s.index('fn scene()');b=s.index('fn write_state',a)
 s=s[:a]+'''fn nominal(alpha:f64)->rf_d_circuit::conditioned_voice::Parameters{
 let original=rf_d_circuit::conditioned_recipe::Recipe{final_decay:rf_d_circuit::conditioned_recipe::FinalDecay::On,resolution:rf_d_circuit::conditioned_recipe::Resolution::Half2Us}.parameters();
 let mut chain=original.chain();chain.boundary.panel.cutoff_fraction_from_neg10=alpha;
 rf_d_circuit::conditioned_voice::Parameters::new(original.controls,chain,[false;4],[0.5;4],original.sources).expect("declared cutoff recipe")
}
fn scene(alpha:f64)->joint::Parameters{joint::Parameters::from_nominal(nominal(alpha))}
'''+s[b:]
 s=s.replace('b[64+8*k..72+8*k]','b[72+8*k..80+8*k]').replace('f64::from_le_bytes(b[64+8*k..72+8*k]','f64::from_le_bytes(b[72+8*k..80+8*k]')
 s=once(s,'b[56..64].copy_from_slice(&q.parameters.decay_ohm.to_le_bytes());','b[56..64].copy_from_slice(&q.parameters.decay_ohm.to_le_bytes());b[64..72].copy_from_slice(&q.parameters.chain().boundary.panel.cutoff_fraction_from_neg10.to_le_bytes());')
 s=once(s,'let mut p=scene();','let alpha=f64::from_le_bytes(b[64..72].try_into().unwrap());if alpha.to_bits()!=ALPHA[phase as usize].to_bits(){return Err("cutoff recipe".into());}let mut p=scene(alpha);')
 a=s.index(' let mut p=legacy_joint::Parameters::from_nominal(');b=s.index(';p.decay_ohm=',a)
 s=s[:a]+' let mut p=legacy_joint::Parameters::from_nominal(nominal(q.parameters.chain().boundary.panel.cutoff_fraction_from_neg10))'+s[b:]
 s=s.replace('usage: voice_retrigger <tail-final.ckp>','usage: voice_cutoff <retrigger-final.ckp>')
 old='let raw=fs::read(&args[1]).map_err(|e|e.to_string())?;let restored=decode(&raw)?;'
 new='''let raw=fs::read(&args[1]).map_err(|e|e.to_string())?;
 if raw.len()!=3728||&raw[..8]!=b"RFDCY001"||u32::from_le_bytes(raw[28..32].try_into().unwrap())!=2{return Err("own previous codec".into());}
 let mut converted=[0;SIZE];converted[..64].copy_from_slice(&raw[..64]);converted[..8].copy_from_slice(b"RFCTF001");converted[28..32].copy_from_slice(&0_u32.to_le_bytes());converted[64..72].copy_from_slice(&1_f64.to_le_bytes());converted[72..].copy_from_slice(&raw[64..]);let restored=decode(&converted)?;'''
 s=once(s,old,new).replace('encode(restored).as_slice()!=raw.as_slice()','encode(restored)!=converted')
 old='let incoming=encode(saved);engine.trigger(KEY[phase],SHORT[phase]).map_err(|e|format!("trigger:{e:?}"))?;'
 new='let incoming=encode(saved);let mut q=engine.checkpoint();let mut p=scene(ALPHA[phase]);p.keyboard=q.parameters.keyboard;p.short=q.parameters.short;p.decay_ohm=q.parameters.decay_ohm;q.parameters=p;engine=temporal::Engine::restore(q).map_err(|e|format!("cutoff event:{e:?}"))?;'
 s=once(s,old,new).replace('incoming[56..]!=changed[56..]||incoming[8..28]!=changed[8..28]','incoming[72..]!=changed[72..]||incoming[56..64]!=changed[56..64]||incoming[8..28]!=changed[8..28]||incoming[32..56]!=changed[32..56]')
 # Corruption must address the shifted state payload.
 s=s.replace('b[64+8*225..72+8*225]','b[72+8*225..80+8*225]')
 return s
def auditor():
 s=(ROOT/'tools/check_voice_retrigger.py').read_text(encoding='utf8').replace('prepare_voice_retrigger','prepare_voice_cutoff').replace('check_voice_retrigger','check_voice_cutoff').replace('VOZ_RETRIGGER_PROTOCOLO','VOZ_CUTOFF_PROTOCOLO').replace('voice_retrigger_native','voice_cutoff_native').replace('voice_retrigger_inputs','voice_cutoff_inputs')
 s=s.replace('CUT,cuts,DECAY','CUT,cuts,DECAY,ALPHA').replace("from decay_control_reference import state,lift,packed,scoped,currents,ledger,D", "from cutoff_control_reference import state,lift,packed,scoped,currents,ledger,D")
 s=s.replace("CODEC=struct.Struct('<8sQ6IdQd458d')", "CODEC=struct.Struct('<8sQ6IdQ2d458d')").replace('len(raw)==3728','len(raw)==3736').replace('key,reserved,decay,*v=r','key,reserved,decay,alpha,*v=r').replace("magic==b'RFDCY001'", "magic==b'RFCTF001'").replace('flags in [1,3]','flags==1').replace('reserved==0 and decay==DECAY','reserved==0 and decay==DECAY and alpha==ALPHA[phase]')
 s=s.replace('decay_ohm=decay,values=v','decay_ohm=decay,cutoff_fraction=alpha,values=v').replace('25*3728','25*3736').replace('range(0,len(raw),3728)','range(0,len(raw),3736)').replace('raw[k:k+3728]','raw[k:k+3736]')
 s=s.replace("published=json.loads((ROOT/'evidence/voice_tail_reference01.json')", "published=json.loads((ROOT/'evidence/voice_retrigger_reference01.json')")
 s=s.replace("struct.unpack('<8sQ6IdQd458d',(ROOT/f'references-local/long-tail01/{maximum}/final.ckp').read_bytes())[4]", "struct.unpack('<8sQ6IdQd458d',(ROOT/f'references-local/voice-retrigger01/{maximum}/final.ckp').read_bytes())[4]")
 s=s.replace("directory=ROOT/f'references-local/voice-retrigger01/{maximum}'", "directory=ROOT/f'references-local/voice-cutoff01/{maximum}'").replace("directory=ROOT/f\"references-local/voice-retrigger01/{p['maximum_half_ticks']}\"", "directory=ROOT/f\"references-local/voice-cutoff01/{p['maximum_half_ticks']}\"")
 s=s.replace("parent=ROOT/f'references-local/long-tail01/{maximum}/final.ckp'", "parent=ROOT/f'references-local/voice-retrigger01/{maximum}/final.ckp'")
 s=s.replace(".replace('release-voice01','voice-retrigger01')", ".replace('release-voice01','voice-cutoff01')")
 s=s.replace("checks.append(scoped(KEY[phase],on,SHORT[phase])", "checks.append(scoped(KEY[phase],on,SHORT[phase],ALPHA[phase])")
 s=s.replace("[:3728]", "[:3736]")
 s=once(s,"require(raw==copy==new,'all seed metadata, parameters and state preserved by bits')", "expected=bytearray(raw[:64]+struct.pack('<d',1.)+raw[64:]);expected[:8]=b'RFCTF001';expected[28:32]=struct.pack('<I',0);require(raw==copy and bytes(expected)==new,'declared codec extension preserves clock proposal recipe and 458 states')")
 s=s.replace("a[56:]==b[56:] and a[8:28]==b[8:28]", "a[72:]==b[72:] and a[56:64]==b[56:64] and a[8:28]==b[8:28] and a[32:56]==b[32:56]")
 s=s.replace("keyboard_v=v['key'],short=v['short'],preserved_values", "keyboard_v=v['key'],short=v['short'],cutoff_fraction=v['cutoff_fraction'],previous_cutoff_fraction=u['cutoff_fraction'],preserved_values")
 s=s.replace("parent=json.loads((ROOT/'evidence/voice_tail_reference01.json')", "parent=json.loads((ROOT/'evidence/voice_retrigger_reference01.json')")
 s=s.replace('joined_duration_s=.148008','joined_duration_s=.164012').replace('source_voltage_event=True','source_voltage_event=False,cutoff_parameter_event=True')
 s=s.replace("'evidence/voice_tail_reference01.json'", "'evidence/voice_retrigger_reference01.json'").replace("'tools/decay_control_reference.py'", "'tools/cutoff_control_reference.py'")
 s=s.replace("write('evidence/voice_retrigger_reference01.json',r)", "write('evidence/voice_cutoff_reference01.json',r)")
 return s
def main():
 qa=json.loads((ROOT/'evidence/voice_retrigger_tests01.json').read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(qa['passed'] and head=='59b60328b27f812a76e5bc6589ddf629fd30ba22','frozen admitted base');require(not (ROOT/'evidence/voice_cutoff_before01.json').exists(),'exclusive cutoff')
 write('evidence/voice_cutoff_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_retrigger_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
 for n,t in [(EXAMPLE,caller()),('tools/check_voice_cutoff.py',auditor())]:require(not (ROOT/n).exists(),'exclusive source');(ROOT/n).write_text(t,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);lib=qa['public_assembly_library_path'];seeds=[]
 for m in [1048576,524288]:
  n=f'references-local/voice-retrigger01/{m}/final.ckp';require(sha(ROOT/n)==qa['private_input_sha256'][n],'own final seed');seeds.append(dict(path=n,sha256=sha(ROOT/n),maximum_half_ticks=m))
 write('evidence/voice_cutoff_inputs01.json',dict(passed=True,start_ticks=START,end_ticks=START+SPAN,span_ticks=SPAN,boundaries_relative_ticks=BOUNDARIES,keyboard_v=KEY,short=SHORT,cutoff_fraction_from_neg10=ALPHA,decay_ohm=DECAY,new_source_event=True,seeds=seeds,source_sha256={n:sha(ROOT/n) for n in [EXAMPLE,'tools/prepare_voice_cutoff.py','tools/check_voice_cutoff.py','tools/cutoff_control_reference.py','docs/VOZ_CUTOFF_PROTOCOLO.md']},private_used_sha256={lib:sha(ROOT/lib),**{s['path']:s['sha256'] for s in seeds}}))
 print('CUTOFF_PREPARED',START+SPAN)
if __name__=='__main__':main()
