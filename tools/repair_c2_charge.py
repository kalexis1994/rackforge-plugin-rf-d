"""Preserve the compiler replay and fix declaration order/index typing only."""
import base64,hashlib,json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 bad=json.loads((ROOT/'evidence/voice_c2_charge_native01.json').read_text(encoding='utf8'));require(not bad['passed'] and bad['commands'][0]['stderr']==bad['replays'][0]['stderr'],'identical compile rejection')
 raw_sources={}
 for n,h in bad['source_sha256'].items():
  raw=(ROOT/n).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=h:
   require(n=='tools/run_c2_charge.py','only receipt-index adapter already changed');raw=bad['failed_source_text'][n].encode()
  require(hashlib.sha256(raw).hexdigest()==h,'exact failed source bytes')
  if n in bad['failed_source_text']:raw_sources[n]=base64.b64encode(raw).decode()
 write('evidence/voice_c2_charge_failure_source_bytes01.json',dict(source_sha256=bad['source_sha256'],source_base64=raw_sources,compile_diagnostics_identical=True))
 p=ROOT/'tools/prepare_c2_charge.py';s=p.read_text(encoding='utf8');a=' return \'#[path="c2_charge_driver.rs"] pub mod c2_charge_driver;\\n\'+s';b=' i=s.index("use rf_d_circuit");return s[:i]+\'#[path="c2_charge_driver.rs"] pub mod c2_charge_driver;\\n\'+s[i:]';require(s.count(a)==1,'module declaration ordering repair');p.write_text(s.replace(a,b),encoding='utf8',newline='\n')
 p=ROOT/'tools/joint_c2_body.rs';s=p.read_text(encoding='utf8');require(s.count('let source=|k|')==1,'source index repair');p.write_text(s.replace('let source=|k|','let source=|k:usize|'),encoding='utf8',newline='\n')
 from prepare_c2_charge import kernel,caller
 for n,s in [('tools/joint_c2_kernel.rs',kernel()),('tools/joint_c2_runner.rs',caller())]:(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 inp=json.loads((ROOT/'evidence/voice_c2_charge_inputs01.json').read_text(encoding='utf8'));inp['compiler_only_repair']=['module follows inner doc comments','explicit usize source index'];inp['source_sha256']={n:sha(ROOT/n) for n in [*inp['source_sha256'],'tools/repair_c2_charge.py']};write('evidence/voice_c2_charge_inputs02.json',inp);print('C2_COMPILER_REPAIR')
if __name__=='__main__':main()
