"""Preserve failed measured sources before an exact predictor-only substitution."""
import base64,json
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from diagnose_contour_cycle import OLD,NEW
ATTR_REPAIR=b'/tools/joint_contour_cycle_kernel.rs text eol=lf\n'
def repaired_caller():
 from prepare_contour_cycle import caller
 return caller().replace('path="joint_latch_kernel.rs"','path="joint_contour_cycle_kernel.rs"')
def repaired_kernel():return (ROOT/'tools/joint_latch_kernel.rs').read_text(encoding='utf8').replace(OLD,NEW)
def main():
 failed=json.loads((ROOT/'evidence/voice_contour_cycle_native01.json').read_text(encoding='utf8'));diag=json.loads((ROOT/'evidence/voice_contour_cycle_diagnostic04.json').read_text(encoding='utf8'));require(not failed['passed'] and diag['passed'],'frozen rejection and single-step hypothesis');require(failed['profiles'][0]['stderr']==failed['replays'][0]['stderr'],'identical profile failure')
 originals={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in failed['source_sha256']}
 for n,h in failed['source_sha256'].items():require(sha(ROOT/n)==h,'failed source '+n)
 aux={p.relative_to(ROOT).as_posix():sha(p) for a in [1,2,3] for p in (ROOT/f'references-local/contour-cycle-diagnostic{a:02d}').iterdir() if p.is_file()}
 write('evidence/voice_contour_cycle_repair_before01.json',dict(passed=True,failed_native_sha256=sha(ROOT/'evidence/voice_contour_cycle_native01.json'),diagnostic_sha256=sha(ROOT/'evidence/voice_contour_cycle_diagnostic04.json'),failed_source_base64=originals,auxiliary_survivors_sha256=aux,original_auxiliary_failure_stderr_retained=False,substitution_old=OLD,substitution_new=NEW,numerical_gates_changed=False))
 require((ROOT/'tools/joint_latch_kernel.rs').read_text(encoding='utf8').count(OLD)==1,'exact predictor condition')
 (ROOT/'tools/joint_contour_cycle_kernel.rs').write_text(repaired_kernel(),encoding='utf8',newline='\n');(ROOT/'tools/joint_contour_cycle_runner.rs').write_text(repaired_caller(),encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR_REPAIR)
 p=ROOT/'tools/run_contour_cycle.py';s=p.read_text(encoding='utf8');s=s.replace("names=['tools/run_contour_cycle.py',","names=['tools/joint_contour_cycle_kernel.rs','tools/prepare_contour_cycle_repair.py','docs/VOZ_CONTORNO_CICLO_REPARACION.md','tools/run_contour_cycle.py',");p.write_text(s,encoding='utf8',newline='\n')
 inp=json.loads((ROOT/'evidence/voice_contour_cycle_inputs01.json').read_text(encoding='utf8'));inp['source_sha256']={n:sha(ROOT/n) for n in set(inp['source_sha256'])|{'tools/joint_contour_cycle_kernel.rs','tools/run_contour_cycle.py','tools/prepare_contour_cycle_repair.py','docs/VOZ_CONTORNO_CICLO_REPARACION.md','evidence/voice_contour_cycle_repair_before01.json'}};inp['failed_attempt']=1;inp['predictor_repair_only']=True;write('evidence/voice_contour_cycle_inputs02.json',inp)
 print('CYCLE_REPAIR_DECLARED')
if __name__=='__main__':main()
