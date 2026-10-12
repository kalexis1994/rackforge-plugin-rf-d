"""Freeze the long-window release gates from the admitted adaptive release."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
def source():
 s=(ROOT/'tools/validate_contour_engine.py').read_text(encoding='utf8').replace('contour_engine','contour_reset');s=s.replace("previous='evidence/voice_latch_charge_tests01.json'","previous='evidence/voice_contour_engine_tests01.json'")
 s=s.replace('tools/contour_reset.rs','tools/contour_reset_engine.rs').replace('tools/joint_contour_runner.rs','tools/joint_contour_reset_runner.rs')
 s=s.replace("'<8sQII2dII458d'","'<8sQ6IdQ458d'").replace("read_bytes())[8:]","read_bytes())[10:]")
 s=s.replace("obj['passed'] and obj['source_sha256']==obj['source_sha256_after']","obj['passed'] and obj['source_sha256']==obj['source_sha256_after']")
 s=s.replace("p['wall_s']<=300","p['wall_s']<=990").replace("native['wall_s']<=1500","native['wall_s']<=4000").replace("native['estimated_output_bytes']==32*1024**2","native['estimated_output_bytes']==64*1024**2")
 old="counts=dict(independent_candidates=144,independent_nonlinear_rows=32976,native_current_endpoint_vectors=48,native_current_values=144,restores=20,rejected_corruptions=16,atomic_rollbacks=8,inherited_bit_coordinates=458,source_boundary_bit_coordinates=458)"
 new="selected=sum(p['selected_accepted_count'] for p in ref['profiles']);crossings=sum(len(p['resets']) for p in ref['profiles']);counts=dict(independent_candidates=6*selected,independent_nonlinear_rows=1374*selected,native_current_endpoint_vectors=2*selected,native_current_values=6*selected,restores=20+crossings,reset_crossings=crossings,rejected_corruptions=16,atomic_rollbacks=8,inherited_bit_coordinates=458,source_boundary_bit_coordinates=458)"
 require(old in s,'release counts');s=s.replace(old,new).replace("ref['adaptive229_window_admitted']","ref['adaptive229_reset_window_admitted']").replace('adaptive229_window_admitted=True','adaptive229_reset_window_admitted=True')
 s=s.replace("len(p['root_checks'])==18 and len(p['port_checks'])==12 and len(p['selected_lte'])==6 and p['restores']==5", "len(p['root_checks'])==3*p['selected_accepted_count'] and len(p['port_checks'])==2*p['selected_accepted_count'] and len(p['selected_lte'])==p['selected_accepted_count'] and p['restores']==5+len(p['resets'])")
 marker="  for c in p['root_checks']:"
 s=s.replace(marker, "  require(len(p['resets'])>=1 and p['selected_accepted_count']==sum(min(2,q['accepted_steps']) for q in p['phases'])+len(p['resets']) and p['replayed_accepted_steps']==sum(q['accepted_replayed'] for q in p['replay_points']) and len(p['replay_points'])==p['restores'],'reset/prefix replay coverage')\n"+marker)
 s=s.replace('def audit():', "from prepare_contour_reset_auditor import source as declared_auditor\nfrom prepare_contour_reset_validator import source as declared_validator\ndef audit():\n require((ROOT/'tools/check_contour_reset.py').read_text(encoding='utf8')==declared_auditor() and (ROOT/'tools/validate_contour_reset.py').read_text(encoding='utf8')==declared_validator(),'reproducible adapters')")
 return s
def main():
 p=ROOT/'tools/validate_contour_reset.py';require(not p.exists(),'exclusive validator');p.write_text(source(),encoding='utf8',newline='\n')
if __name__=='__main__':main()
