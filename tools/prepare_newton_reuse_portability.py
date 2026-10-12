"""Freeze the new receipt family after numerical measurement, before publication."""
import base64,hashlib,json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
PORTABLE=b'\n# Freeze the exact bytes of the operation-reuse receipt family.\nevidence/newton_reuse*.json -text\n'
def audit_portability():
 p=json.loads((ROOT/'evidence/newton_reuse_portability01.json').read_text(encoding='utf8'));old=json.loads((ROOT/'evidence/newton_reuse_tests_pre_portability01.json').read_text(encoding='utf8'));require(p['pre_portability_qa_sha256']==sha(ROOT/'evidence/newton_reuse_tests_pre_portability01.json') and old['passed'],'prior release identity');saved={n:base64.b64decode(v) for n,v in p['changed_source_before_base64'].items()}
 for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'pre-portability source '+n)
 require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+PORTABLE and not p['numerical_measurements_changed'],'receipt portability only')
def main():
 qa=ROOT/'evidence/newton_reuse_tests01.json';require(json.loads(qa.read_text(encoding='utf8'))['passed'],'measured release');p=ROOT/'evidence/newton_reuse_tests_pre_portability01.json';require(not p.exists(),'exclusive prior QA');p.write_bytes(qa.read_bytes());write('evidence/newton_reuse_portability01.json',dict(passed=True,pre_portability_qa_sha256=sha(p),changed_source_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','tools/validate_newton_reuse.py']},numerical_measurements_changed=False,reason='Git would convert new receipt family on Windows checkout',pattern='evidence/newton_reuse*.json -text'));p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+PORTABLE);print('REUSE_RECEIPTS_FROZEN')
if __name__=='__main__':main()
