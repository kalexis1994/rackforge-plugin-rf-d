"""Complete only negative CLI fixtures, retaining the failed source and exact replay."""
import base64,json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def repaired_source():
 old=json.loads((ROOT/'evidence/voice_retrigger_cli01.json').read_text(encoding='utf8'));s=base64.b64decode(old['failed_source_base64']['tools/check_retrigger_cli.py']).decode('utf8')
 s=s.replace('references-local/retrigger-cli01','references-local/retrigger-cli02').replace('evidence/voice_retrigger_cli01.json','evidence/voice_retrigger_cli02.json')
 marker=" scope={'__name__':'retrigger_cli_harness'}"
 extra=''' s=s.replace("for n in ['incoming-original.ckp','final.ckp']:", "for n in ['incoming-original.ckp','final.ckp','event1-before.ckp','event1-after.ckp','event2-before.ckp','event2-after.ckp']:")
 s=s.replace("names=['tools/check_extended_cli.py'", "names=['tools/check_retrigger_cli_attempt01.py','tools/repair_retrigger_cli.py','evidence/voice_retrigger_cli01.json','evidence/voice_retrigger_cli_replay01.json','evidence/voice_retrigger_cli_repair01.json','tools/check_extended_cli.py'")
'''
 require(s.count(marker)==1,'one harness scope');return s.replace(marker,extra+marker,1)
def main():
 old=json.loads((ROOT/'evidence/voice_retrigger_cli01.json').read_text(encoding='utf8'));replay=json.loads((ROOT/'evidence/voice_retrigger_cli_replay01.json').read_text(encoding='utf8'));require(not old['passed'] and replay['passed'] and replay['unchanged_failure_identical'] and replay['no_output_publication'],'unchanged rejection replay before repair');require(sha(ROOT/'tools/check_retrigger_cli.py')==old['source_sha256']['tools/check_retrigger_cli.py']==sha(ROOT/'tools/check_retrigger_cli_attempt01.py'),'frozen failed harness source');s=repaired_source();compile(s,'repaired CLI checker','exec');(ROOT/'tools/check_retrigger_cli.py').write_text(s,encoding='utf8',newline='\n')
 write('evidence/voice_retrigger_cli_repair01.json',dict(passed=True,reason='negative fixture omitted four event checkpoints required by input provenance; unchanged replay rejects the same missing input',unchanged_gates=True,circuit_and_renderer_unchanged=True,source_sha256={n:sha(ROOT/n) for n in ['tools/repair_retrigger_cli.py','tools/check_retrigger_cli.py','tools/check_retrigger_cli_attempt01.py','tools/retrigger_render_cli.py','tools/render_voice_retrigger.py','evidence/voice_retrigger_cli01.json','evidence/voice_retrigger_cli_replay01.json']},failed_private_sha256={o['path']:o['sha256'] for o in old['outputs']},new_work='references-local/retrigger-cli02',new_receipt='evidence/voice_retrigger_cli02.json'))
 print('CLI_FIXTURE_REPAIR_PREPARED')
if __name__=='__main__':main()
