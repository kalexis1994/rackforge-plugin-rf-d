"""Resume only the unmeasured preparation after a retained syntax rejection."""
import base64,json
from prepare_vco1_portable import ROOT,sha,write
from prepare_cutoff_ab import *
def main():
 before=json.loads((ROOT/'evidence/cutoff_ab_before01.json').read_text(encoding='utf8'));failed=json.loads((ROOT/'evidence/cutoff_ab_preflight_failure01.json').read_text(encoding='utf8'));qa=json.loads((ROOT/'evidence/voice_cutoff_tests01.json').read_text(encoding='utf8'));require(qa['passed'] and before['previous_qa_sha256']==sha(ROOT/'evidence/voice_cutoff_tests01.json') and failed['failure']==failed['unchanged_replay'],'frozen preparation and unchanged failure')
 for n,b in before['mutable_before_base64'].items():require((ROOT/n).read_bytes()==base64.b64decode(b),'no mutable edits before preparation resume')
 require((ROOT/EXAMPLE).read_text(encoding='utf8')==caller(),'prepared caller unchanged');s=auditor();compile(s,'repaired auditor','exec');p=ROOT/'tools/check_cutoff_ab.py';require(not p.exists(),'new repaired auditor');p.write_text(s,encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);lib=qa['public_assembly_library_path'];seeds=[]
 for m in [1048576,524288]:
  n=f'references-local/voice-cutoff01/{m}/event1-before.ckp';require(sha(ROOT/n)==qa['private_input_sha256'][n],'own common seed');seeds.append(dict(path=n,sha256=sha(ROOT/n),maximum_half_ticks=m))
 write('evidence/cutoff_ab_preflight_repair01.json',dict(passed=True,reason='restrict phase guard substitution so it does not rewrite the for loop',before_unchanged=True,no_native_measurement_before_repair=True,source_sha256={n:sha(ROOT/n) for n in ['tools/resume_cutoff_ab_preflight.py','tools/prepare_cutoff_ab.py','tools/check_cutoff_ab.py','evidence/cutoff_ab_preflight_failure01.json']}))
 write('evidence/cutoff_ab_inputs01.json',dict(passed=True,start_ticks=START,end_ticks=START+SPAN,span_ticks=SPAN,new_source_event=False,open_cutoff_fraction=1.,closed_cutoff_fraction=.5,closed_phase=1,seeds=seeds,source_sha256={n:sha(ROOT/n) for n in [EXAMPLE,'tools/prepare_cutoff_ab.py','tools/check_cutoff_ab.py','tools/cutoff_ab_audit.py','docs/VOZ_CUTOFF_AB_PROTOCOLO.md','tools/resume_cutoff_ab_preflight.py','evidence/cutoff_ab_preflight_failure01.json','evidence/cutoff_ab_preflight_repair01.json']},private_used_sha256={lib:sha(ROOT/lib),**{s['path']:s['sha256'] for s in seeds}}));print('CUTOFF_AB_PREPARED_AFTER_SYNTAX_REPAIR')
if __name__=='__main__':main()
