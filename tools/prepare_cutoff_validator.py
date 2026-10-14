"""Retain the loaded voice gates while admitting explicit panel recipe extension."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
def source():
 s=(ROOT/'tools/validate_voice_retrigger.py').read_text(encoding='utf8')
 # The previous fixture repair is protected by predecessor hashes, not rerun.
 a=s.index(" failed=read(");b=s.index(' native,ref,listening,cli=',a);s=s[:a]+s[b:]
 s=s.replace('prepare_voice_retrigger','prepare_voice_cutoff').replace('check_voice_retrigger','check_voice_cutoff').replace('voice_retrigger_before','voice_cutoff_before')
 s=s.replace("old=read('evidence/voice_tail_tests01.json')", "old=read('evidence/voice_retrigger_tests01.json')").replace("sha(ROOT/'evidence/voice_tail_tests01.json')", "sha(ROOT/'evidence/voice_retrigger_tests01.json')")
 for name in ['inputs','native','reference','listening']:s=s.replace('voice_retrigger_'+name,'voice_cutoff_'+name)
 s=s.replace('voice_retrigger_cli02','voice_cutoff_cli01').replace('voice_retrigger_tests','voice_cutoff_tests').replace('voice_retrigger_qa_failure','voice_cutoff_qa_failure').replace('retrigger-cli02','cutoff-cli01')
 s=s.replace("old=read('evidence/voice_cutoff_tests01.json')", "old=read('evidence/voice_retrigger_tests01.json')").replace("before['previous_qa_sha256']==sha(ROOT/'evidence/voice_cutoff_tests01.json')", "before['previous_qa_sha256']==sha(ROOT/'evidence/voice_retrigger_tests01.json')").replace("previous_qa_sha256=sha(ROOT/'evidence/voice_cutoff_tests01.json')", "previous_qa_sha256=sha(ROOT/'evidence/voice_retrigger_tests01.json')")
 s=s.replace("saved['README.md'].replace(b'voice_tail_tests01.json',b'voice_cutoff_tests01.json')", "saved['README.md'].replace(b'voice_retrigger_tests01.json',b'voice_cutoff_tests01.json')")
 s=s.replace("|{'evidence/voice_tail_tests01.json'}", "|{'evidence/voice_retrigger_tests01.json'}")
 s=s.replace('retrigger_reference={','cutoff_reference={').replace('retrigger_listening={','cutoff_listening={').replace('joined_duration_s\']==.148008','joined_duration_s\']==.164012').replace('7104','7872').replace('wav_duration_s=.148','wav_duration_s=.164').replace("f['wav_duration_s']==.148", "f['wav_duration_s']==.164").replace("sidecar['retrigger_start_ticks']", "sidecar['cutoff_start_ticks']").replace("len(sidecar['input_sha256'])==17", "len(sidecar['input_sha256'])==24")
 s=s.replace("dict(ticks=e['ticks'],keyboard_v=e['keyboard_v'],short=e['short'])", "dict(ticks=e['ticks'],keyboard_v=e['keyboard_v'],short=e['short'],cutoff_fraction=e['cutoff_fraction'],previous_cutoff_fraction=e['previous_cutoff_fraction'])")
 s=s.replace("'tail_reference','tail_listening']:r[k]=old[k]", "'tail_reference','tail_listening','retrigger_reference','retrigger_listening']:r[k]=old[k]")
 s=s.replace("cli_fixture_failure_retained=True,cli_unchanged_failure_replay=True,cli_fixture_repair_sha256=sha(ROOT/'evidence/voice_retrigger_cli_repair01.json'),",'')
 s=s.replace('rf-d/charged-retrigger-loaded-assembly/v1','rf-d/loaded-cutoff-panel-control/v1').replace('tools/validate_voice_retrigger.py','tools/validate_voice_cutoff.py').replace("print('RETRIGGER_QA'", "print('CUTOFF_QA'").replace('seventeen input identities','twenty-four input identities')
 anchor=" native,ref,listening,cli=[read(n) for n in receipts[1:]]"
 extra=""" from prepare_cutoff_render import renderer,cli as cli_source,checker
 require((ROOT/'tools/render_voice_cutoff.py').read_text(encoding='utf8')==renderer() and (ROOT/'tools/cutoff_render_cli.py').read_text(encoding='utf8')==cli_source() and (ROOT/'tools/check_cutoff_cli.py').read_text(encoding='utf8')==checker(),'declared renderer CLI and complete negative fixtures')
"""
 s=s.replace(anchor,extra+anchor,1)
 return s
def main():
 p=ROOT/'tools/validate_voice_cutoff.py';require(not p.exists(),'exclusive cutoff validator');s=source();compile(s,str(p),'exec');p.write_text(s,encoding='utf8',newline='\n');print('CUTOFF_VALIDATOR_PREPARED')
if __name__=='__main__':main()
