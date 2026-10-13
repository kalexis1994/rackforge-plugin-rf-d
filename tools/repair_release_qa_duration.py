"""Preserve a rejected QA adapter and replace only its duration representation."""
import base64,hashlib,json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require,TICK
from prepare_release_voice import START,SPAN

def main():
    failure='evidence/voice_release_qa_failure01.json';name='tools/validate_release_voice.py';r=json.loads((ROOT/failure).read_text(encoding='utf8'));original=base64.b64decode(r['failed_source_base64'])
    require(not r['passed'] and 'ValueError: joined physical charge endpoints' in r['failure'] and 'ValueError: joined physical charge endpoints' in r['replay'],'preserved failed check and unchanged replay')
    require((ROOT/name).read_bytes()==original,'failed source remains unchanged')
    old=b"j['duration_s']==.020004";new=b"j['duration_s']==(START+SPAN-4423942144)*TICK";require(original.count(old)==1,'one representation comparison')
    ref=json.loads((ROOT/'evidence/voice_release_reference01.json').read_text(encoding='utf8'));expected=(START+SPAN-4423942144)*TICK
    require(all(j['duration_s']==expected and j['duration_s']!=.020004 for j in ref['joined_ledgers']),'binary tick product proves representation mismatch')
    changed=original.replace(old,new).replace(b'from joint_cycles_analysis import require\n',b'from joint_cycles_analysis import require,TICK\n');require(changed!=original,'explicit tick adapter import')
    (ROOT/name).write_bytes(changed)
    write('evidence/voice_release_qa_representation01.json',dict(passed=True,source_sha256={'tools/repair_release_qa_duration.py':sha(ROOT/'tools/repair_release_qa_duration.py'),failure:sha(ROOT/failure),'evidence/voice_release_reference01.json':sha(ROOT/'evidence/voice_release_reference01.json'),name:sha(ROOT/name)},failed_source_sha256=hashlib.sha256(original).hexdigest(),only_duration_comparison_and_tick_import_changed=True,preserved_failure_and_unchanged_replay=True,duration_ticks=START+SPAN-4423942144,tick_seconds=TICK,tick_product_seconds=expected,decimal_label_seconds=.020004,numerical_gates_changed=False,measured_inputs_changed=False))
    print('RELEASE_QA_REPRESENTATION',expected)
if __name__=='__main__':main()
