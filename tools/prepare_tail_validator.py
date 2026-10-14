"""Declare the existing full continuation gates with the new fixed clock/span."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
def source():
 s=(ROOT/'tools/validate_extended_release.py').read_text(encoding='utf8');s=s.replace('from prepare_extended_release import EXAMPLE,ATTR,START,SPAN,caller,auditor','from prepare_long_tail import EXAMPLE,ATTR,START,SPAN,caller,auditor').replace('voice_block_tests01','voice_assembly_tests01').replace('voice_extended','voice_tail').replace('tools/check_extended_release.py','tools/check_long_tail.py');s=s.replace('==41 and max','==81 and max').replace('shared_clock_states=41','shared_clock_states=81').replace('ref[\'continued_duration_s\']==.032','ref[\'continued_duration_s\']==.064').replace('ref[\'joined_duration_s\']==.068004','ref[\'joined_duration_s\']==.132004').replace("f['frames']==3264","f['frames']==6336").replace("f['wav_duration_s']==.068","f['wav_duration_s']==.132").replace('128*1024**2','192*1024**2').replace('wav_duration_s=.068,wav_frames=3264','wav_duration_s=.132,wav_frames=6336').replace('new_circuit_duration_s=.032','new_circuit_duration_s=.064').replace('extended_reference={','tail_reference={').replace('extended_listening={','tail_listening={').replace('rf-d/finite-extended-loaded-release/v1','rf-d/finite-long-tail-loaded-assembly/v1')
 s=s.replace("'decay_listening','decay_reference']:r[k]=old[k]","'decay_listening','decay_reference','extended_reference','extended_listening','public_assembly_library_sha256','public_assembly_library_path','public_assembly_family_admitted']:r[k]=old[k]")
 insert=" require(cli['integration_checks']==4"
 extra=""" sidecar=read('references-local/tail-cli01/j7.json');require(len(sidecar['input_sha256'])==10 and sidecar['tail_start_ticks']==START and sidecar['final_ticks']==START+SPAN and sidecar['frames']==6336,'ten input identities and integer audio clock')
 for n,h in sidecar['code_sha256'].items():require(sha(ROOT/'tools'/n)==h,'sidecar code identity '+n)
"""
 s=s.replace("ROOT/'tools/validate_extended_release.py'", "ROOT/'tools/validate_long_tail.py'").replace("print('EXTENDED_QA'", "print('TAIL_QA'")
 require(s.count(insert)==1,'one CLI gate insertion');return s.replace(insert,extra+insert,1)
def main():
 p=ROOT/'tools/validate_long_tail.py';require(not p.exists(),'exclusive validator source');p.write_text(source(),encoding='utf8',newline='\n');print('TAIL_VALIDATOR_PREPARED')
if __name__=='__main__':main()
