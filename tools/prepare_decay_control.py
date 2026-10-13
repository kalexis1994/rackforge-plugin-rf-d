"""Derive the controlled family directly from byte-preserved nominal sources."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from prepare_release_voice import once
START=14911799296;SPAN=8388608000;CUT=419430400
BOUNDARIES=[0,SPAN];KEY=[0.];SHORT=[False];DECAY=1000.
RUST=['crates/rf-d-circuit/src/decay_voice.rs','crates/rf-d-circuit/src/decay_contour.rs','crates/rf-d-circuit/src/decay_engine.rs','crates/rf-d-circuit/examples/decay_control.rs','tools/decay_nominal_legacy.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in RUST)).encode();EXPORT=b'\npub mod decay_voice;\npub mod decay_engine;\n'

def cuts(phase):require(phase==0,'one controlled phase');return list(range(START+CUT,START+SPAN,CUT))+[START+SPAN]

def family():
 v=(ROOT/'crates/rf-d-circuit/src/conditioned_voice.rs').read_text(encoding='utf8')
 v=once(v,'#[path="conditioned_voice_contour.rs"]','#[path="decay_contour.rs"]')
 v=once(v,'pub set_base:f64}','pub set_base:f64,pub decay_ohm:f64}')
 v=once(v,'set_base:0.01})','set_base:0.01,decay_ohm:100000.})')
 marker=' pub fn chain(self)->Chain {self.chain}'
 v=once(v,marker,''' /// Electrical resistance, not a calibrated knob mapping. See DECAY_CONTROL_PROTOCOLO.
 pub fn valid_decay(ohm:f64)->bool {ohm.is_finite()&&ohm>0.&&ohm<=1e6&&ohm.recip().is_finite()}
 pub fn from_nominal(p:crate::conditioned_voice::Parameters)->Self {Self{controls:p.controls,chain:p.chain(),sources:p.sources,c2_v:p.c2_v,reset_v:p.reset_v,q25:p.q25,reset_driver:p.reset_driver,final_decay:p.final_decay,keyboard:p.keyboard,short:p.short,set_base:p.set_base,decay_ohm:100000.}}
'''+marker)
 v=once(v,'p.keyboard,p.final_decay,p.short)?','p.keyboard,p.final_decay,p.short,p.decay_ohm)?')
 c=(ROOT/'crates/rf-d-circuit/src/conditioned_voice_contour.rs').read_text(encoding='utf8')
 c=once(c,'short:bool)->Result<Stamp,StepError>','short:bool,decay_ohm:f64)->Result<Stamp,StepError>')
 c=once(c,'if x.iter().any','if !super::Parameters::valid_decay(decay_ohm)||x.iter().any')
 c=once(c,'r(&mut s,&x,key,11,5,100000.0); // PANEL_R16','r(&mut s,&x,key,11,5,decay_ohm); // PANEL_R16')
 e=(ROOT/'crates/rf-d-circuit/src/conditioned_engine.rs').read_text(encoding='utf8').replace('crate::conditioned_voice','crate::decay_voice')
 e=once(e,' pub fn checkpoint(&self)', ''' /// Ideal parameter event; state, charges, clock and proposal are preserved.
 pub fn set_decay_ohm(&mut self,ohm:f64)->Result<(),Error>{if !joint::Parameters::valid_decay(ohm){return Err(Error::InvalidInput);}self.checkpoint.parameters.decay_ohm=ohm;Ok(())}
 pub fn checkpoint(&self)''')
 return dict(zip(RUST[:3],[v,c,e]))

def main():
 old=json.loads((ROOT/'evidence/voice_release_tests01.json').read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='d620bd4ad4559b85e66bd92d7b4dad8253fdc96f' and old['passed'],'base')
 require(not (ROOT/'evidence/voice_decay_before01.json').exists(),'exclusive preparation')
 mutable=['.gitattributes','crates/rf-d-circuit/src/lib.rs','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
 write('evidence/voice_decay_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_release_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
 for n,s in family().items():require(not (ROOT/n).exists(),'exclusive family');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 for n,s in [('.gitattributes',ATTR),('crates/rf-d-circuit/src/lib.rs',EXPORT)]:p=ROOT/n;p.write_bytes(p.read_bytes()+s)
 seeds=[]
 for maximum in [1048576,524288]:
  n=f'references-local/release-voice01/{maximum}/final.ckp';require(sha(ROOT/n)==old['private_input_sha256'][n],'own released seed');seeds.append(dict(maximum_half_ticks=maximum,path=n,sha256=sha(ROOT/n)))
 write('evidence/voice_decay_inputs01.json',dict(passed=True,seeds=seeds,start_ticks=START,span_ticks=SPAN,decay_ohm=DECAY,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_decay_control.py','docs/DECAY_CONTROL_PROTOCOLO.md','evidence/loudness_contour_graph.json',*RUST[:3]]},private_used_sha256={s['path']:s['sha256'] for s in seeds},new_source_event=True,source_voltage_event=False,own_history_preserved=True))
 print('DECAY_FAMILY_PREPARED')
if __name__=='__main__':main()
