"""Release gate for own checkpoint proposal and a joined finite cycle."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
def source():
 s=(ROOT/'tools/validate_contour_reset.py').read_text(encoding='utf8').replace('contour_reset','contour_cycle');s=s.replace("previous='evidence/voice_contour_engine_tests01.json'","previous='evidence/voice_contour_reset_tests01.json'").replace('from prepare_contour_cycle import ATTR,START,BOUNDARIES,KEY,SHORT,engine,caller','from prepare_contour_cycle import ATTR,START,BOUNDARIES,KEY,SHORT,body,caller').replace("(ROOT/'tools/contour_cycle_engine.rs').read_text(encoding='utf8')==engine()", "(ROOT/'tools/joint_contour_cycle_body.rs').read_text(encoding='utf8')==body()")
 s=s.replace("cp['next_full']==2*s['maximum_half_ticks']", "cp['next_full']==s['inherited_next_full_ticks']")
 marker=" for obj in [native,ref]:"
 s=s.replace(marker,"  raw=bytearray((ROOT/s['origin_path']).read_bytes());raw[:8]=b'RFCYCT01';raw[28:32]=struct.pack('<I',0);require(bytes(raw)==(ROOT/s['path']).read_bytes(),'only magic/recipe phase changed')\n"+marker)
 s=s.replace("ref['adaptive229_reset_window_admitted']","ref['adaptive229_cycle_window_admitted']").replace('adaptive229_reset_window_admitted=True','adaptive229_cycle_window_admitted=True,steady_periodicity_admitted=False')
 marker=" require(ref['accepted_steps']==sum"
 extra=" require(len(ref['joined_cycles'])==4 and not ref['steady_periodicity_admitted'],'cycle scope')\n for c in ref['joined_cycles']:\n  require(c['full_cycle_between_resets_admitted'] and not c['steady_periodicity_admitted'] and Decimal(c['period_s'])>0 and c['seam_ticks']==START,'joined cycle')\n  for n,h in c['input_sha256'].items():require(private[n]==h,'same joined data')\n  for q in c['combined_ledger']['rows']:require(Decimal(q['error_c'])<=Decimal(q['gate_c']),'joined charge balance')\n"
 require(marker in s,'joined release insertion');s=s.replace(marker,extra+marker)
 s=s.replace('from check_contour_cycle import checkpoint','from check_contour_cycle import checkpoint\nfrom prepare_contour_cycle_repair import ATTR_REPAIR,repaired_caller\nfrom check_contour_cycle_repair import audit_failure')
 s=s.replace("saved['.gitattributes']+ATTR", "saved['.gitattributes']+ATTR+ATTR_REPAIR").replace("==caller()", "==repaired_caller()")
 s=s.replace('voice_contour_cycle_native01','voice_contour_cycle_native02').replace('voice_contour_cycle_inputs01','voice_contour_cycle_inputs02')
 s=s.replace(" private=dict(old['private_input_sha256'])", " private=dict(old['private_input_sha256']);private.update(audit_failure())")
 return s
def main():
 p=ROOT/'tools/validate_contour_cycle.py';require(not p.exists(),'exclusive validator');p.write_text(source(),encoding='utf8',newline='\n')
if __name__=='__main__':main()
