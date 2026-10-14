"""Retain the full prior QA gates and add explicit charged source-event ownership."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
def source():
 s=(ROOT/'tools/validate_long_tail.py').read_text(encoding='utf8')
 s=s.replace('from prepare_long_tail import','from prepare_voice_retrigger import').replace('voice_tail_before','voice_retrigger_before').replace("old=read('evidence/voice_assembly_tests01.json')", "old=read('evidence/voice_tail_tests01.json')").replace("sha(ROOT/'evidence/voice_assembly_tests01.json')", "sha(ROOT/'evidence/voice_tail_tests01.json')")
 s=s.replace('tools/check_long_tail.py','tools/check_voice_retrigger.py').replace('voice_tail_inputs','voice_retrigger_inputs').replace('voice_tail_native','voice_retrigger_native').replace('voice_tail_reference','voice_retrigger_reference').replace('voice_tail_listening','voice_retrigger_listening').replace('voice_tail_cli','voice_retrigger_cli').replace('voice_tail_tests','voice_retrigger_tests')
 # The predecessor stays protected and linked, rather than becoming this release QA.
 s=s.replace("old=read('evidence/voice_retrigger_tests01.json')", "old=read('evidence/voice_tail_tests01.json')").replace("before['previous_qa_sha256']==sha(ROOT/'evidence/voice_retrigger_tests01.json')", "before['previous_qa_sha256']==sha(ROOT/'evidence/voice_tail_tests01.json')").replace("previous_qa_sha256=sha(ROOT/'evidence/voice_retrigger_tests01.json')", "previous_qa_sha256=sha(ROOT/'evidence/voice_tail_tests01.json')")
 s=s.replace("saved['README.md'].replace(b'voice_assembly_tests01.json',b'voice_retrigger_tests01.json')", "saved['README.md'].replace(b'voice_tail_tests01.json',b'voice_retrigger_tests01.json')")
 s=s.replace('==81 and max','==22 and max').replace('shared_clock_states=81','shared_clock_states=22').replace("ref['continued_duration_s']==.064", "ref['continued_duration_s']==.016004").replace("ref['joined_duration_s']==.132004", "ref['joined_duration_s']==.148008").replace("not ref['new_source_event']", "ref['new_source_event']").replace("not native['new_source_event']", "native['new_source_event']")
 s=s.replace('6336','7104').replace('wav_duration_s=.132','wav_duration_s=.148').replace("f['wav_duration_s']==.132", "f['wav_duration_s']==.148").replace('192*1024**2','96*1024**2').replace('tail-cli01','retrigger-cli01').replace("len(sidecar['input_sha256'])==10", "len(sidecar['input_sha256'])==17").replace("sidecar['tail_start_ticks']", "sidecar['retrigger_start_ticks']").replace("sha(ROOT/'tools'/n)", "sha(ROOT/n)")
 s=s.replace('rf-d/finite-long-tail-loaded-assembly/v1','rf-d/charged-retrigger-loaded-assembly/v1').replace('new_source_event=False','new_source_event=True').replace('new_circuit_duration_s=.064','new_circuit_duration_s=.016004').replace('tail_reference={','retrigger_reference={').replace('tail_listening={','retrigger_listening={')
 s=s.replace("'public_assembly_family_admitted']:r[k]=old[k]", "'public_assembly_family_admitted','tail_reference','tail_listening']:r[k]=old[k]")
 extra=""" require(ref['event_compared_accepted']==native['event_compared_accepted']==16 and len(ref['source_events'])==2 and all(len(p)==2 and all(e['preserved_values']==458 and e['complete_accepted_bit_comparisons']==4 for e in p) for p in ref['source_events']),'charged source events and original block advances')
 require(sidecar['new_source_event'] and sidecar['source_events']==[dict(ticks=e['ticks'],keyboard_v=e['keyboard_v'],short=e['short']) for e in ref['source_events'][1]],'complete CLI source event provenance')
"""
 s=s.replace(" require(cli['integration_checks']==4",extra+" require(cli['integration_checks']==4",1)
 s=s.replace('tools/validate_long_tail.py','tools/validate_voice_retrigger.py').replace('voice_tail_qa_failure','voice_retrigger_qa_failure').replace("print('TAIL_QA'", "print('RETRIGGER_QA'")
 s=s.replace("|{'evidence/voice_assembly_tests01.json'}", "|{'evidence/voice_tail_tests01.json'}")
 s=s.replace('seam_compared_accepted=8,seam_full_state_values=458','seam_compared_accepted=8,event_compared_accepted=16,source_events=ref[\'source_events\'],seam_full_state_values=458')
 s=s.replace('voice_retrigger_cli01.json','voice_retrigger_cli02.json').replace('retrigger-cli01/j7.json','retrigger-cli02/j7.json')
 repair=""" failed=read('evidence/voice_retrigger_cli01.json');replay=read('evidence/voice_retrigger_cli_replay01.json');repair=read('evidence/voice_retrigger_cli_repair01.json')
 require(not failed['passed'] and replay['passed'] and replay['unchanged_failure_identical'] and replay['no_output_publication'] and repair['passed'] and repair['unchanged_gates'] and repair['circuit_and_renderer_unchanged'],'failed fixture and unchanged replay retained')
 from repair_retrigger_cli import repaired_source
 require((ROOT/'tools/check_retrigger_cli.py').read_text(encoding='utf8')==repaired_source(),'only declared fixture completion')
 for n,b in failed['failed_source_base64'].items():
  path='tools/check_retrigger_cli_attempt01.py' if n=='tools/check_retrigger_cli.py' else n
  require((ROOT/path).read_bytes()==base64.b64decode(b),'exact failed source '+n)
 for n,h in repair['source_sha256'].items():require(sha(ROOT/n)==h,'frozen fixture repair '+n)
 for n,h in repair['failed_private_sha256'].items():require(sha(ROOT/n)==h,'retained failed fixture output '+n);private[n]=h
"""
 s=s.replace(" native,ref,listening,cli=[read(n) for n in receipts[1:]]",repair+" native,ref,listening,cli=[read(n) for n in receipts[1:]]",1)
 s=s.replace('cli_integration_checks=4,','cli_integration_checks=4,cli_fixture_failure_retained=True,cli_unchanged_failure_replay=True,cli_fixture_repair_sha256=sha(ROOT/\'evidence/voice_retrigger_cli_repair01.json\'),')
 return s.replace('ten input identities and integer audio clock','seventeen input identities and integer audio clock')
def main():
 p=ROOT/'tools/validate_voice_retrigger.py';require(not p.exists(),'exclusive validator');s=source();compile(s,str(p),'exec');p.write_text(s,encoding='utf8',newline='\n');print('RETRIGGER_VALIDATOR_PREPARED')
if __name__=='__main__':main()
