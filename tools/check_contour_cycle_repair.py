"""Verify frozen failure, unchanged accepted prefix and exact numerical repair."""
import base64,hashlib,json
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from prepare_contour_cycle_repair import repaired_kernel,repaired_caller,ATTR_REPAIR
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def audit_failure():
 frozen=read('evidence/voice_contour_cycle_native01.json');saved=read('evidence/voice_contour_cycle_repair_before01.json');diag=read('evidence/voice_contour_cycle_diagnostic04.json');new=read('evidence/voice_contour_cycle_native02.json');private={}
 require(not frozen['passed'] and saved['passed'] and diag['passed'] and new['passed'],'failure/repair status')
 require(saved['failed_native_sha256']==sha(ROOT/'evidence/voice_contour_cycle_native01.json') and saved['diagnostic_sha256']==sha(ROOT/'evidence/voice_contour_cycle_diagnostic04.json'),'frozen receipts')
 originals={n:base64.b64decode(v) for n,v in saved['failed_source_base64'].items()}
 def source(n,h):require(hashlib.sha256(originals.get(n,(ROOT/n).read_bytes())).hexdigest()==h,'frozen diagnostic source '+n)
 require(frozen['source_sha256']==frozen['source_sha256_after'] and frozen['private_used_sha256']==frozen['private_used_sha256_after'],'stable failed campaign')
 for n,h in frozen['source_sha256'].items():require(n in originals and hashlib.sha256(originals[n]).hexdigest()==h,'raw failed source '+n)
 for n,s in frozen['failed_source_text'].items():require(originals[n].decode('utf8').replace('\r\n','\n')==s,'failed text adapter '+n)
 a,b=frozen['profiles'][0],frozen['replays'][0];require(a['exit_code']!=0 and a['exit_code']==b['exit_code'] and a['stderr']==b['stderr'] and 'ticks=5212471296:PrecisionLimit(Nonlinear(IterationBudget))' in a['stderr'],'identical failure')
 require(diag['source_sha256']==diag['source_sha256_after'] and diag['private_used_sha256']==diag['private_used_sha256_after'],'stable diagnostic')
 for n,h in diag['source_sha256'].items():source(n,h)
 commands=diag['commands'];require(len(commands)==5 and all(q['exit_code']==0 for q in commands) and commands[1]['stderr']==commands[2]['stderr']=='REJECT,PrecisionLimit(Nonlinear(IterationBudget)),unchanged=true\n' and commands[4]['stderr'].startswith('ACCEPT,half=16,'),'one-step diagnosis')
 require(diag['only_newton_guess_changed'] and not diag['numerical_gates_changed'] and not diag['complete_trajectory_admitted'],'diagnostic scope')
 require((ROOT/'tools/joint_contour_cycle_kernel.rs').read_text(encoding='utf8')==repaired_kernel() and (ROOT/'tools/joint_contour_cycle_runner.rs').read_text(encoding='utf8')==repaired_caller(),'single predictor substitution')
 for obj in [frozen,diag]:
  for n,h in obj['private_used_sha256'].items():require(sha(ROOT/n)==h,'failed/diagnostic input');private[n]=h
  for f in obj['outputs']:require(sha(ROOT/f['path'])==f['sha256'],'failed/diagnostic output');private[f['path']]=f['sha256']
 for n,h in saved['auxiliary_survivors_sha256'].items():require(sha(ROOT/n)==h,'auxiliary survivor');private[n]=h
 for n,h in read('evidence/voice_contour_cycle_diagnostic_compile01.json')['private_used_sha256'].items():require(sha(ROOT/n)==h,'auxiliary compile survivor');private[n]=h
 recovery=read('evidence/voice_contour_cycle_aux_replay01.json');require(recovery['passed'] and not recovery['original_attempts_stderr_retained'] and recovery['recovery_after_adapter_fix'] and not recovery['circuit_trajectory_evidence'],'auxiliary recovery scope')
 for n,h in recovery['source_sha256'].items():require(sha(ROOT/n)==h,'recovery source')
 for n,h in recovery['private_used_sha256'].items():require(sha(ROOT/n)==h,'recovery private source');private[n]=h
 a0,b0=recovery['commands'];require(a0['exit_code']!=0 and a0['exit_code']==b0['exit_code'] and a0['stderr']==b0['stderr'] and 'circular modules' in a0['stderr'],'recursive include reproduced')
 first=next(p for p in new['profiles'] if p['final_decay']==a['final_decay'] and p['maximum_half_ticks']==a['maximum_half_ticks']);old_dir=__import__('pathlib').Path(a['command'][2]);replay_dir=__import__('pathlib').Path(b['command'][2]);new_dir=__import__('pathlib').Path(first['command'][2]);raw=(old_dir/'selected.txt').read_bytes();require(raw==(replay_dir/'selected.txt').read_bytes() and (new_dir/'selected.txt').read_bytes().startswith(raw),'unchanged accepted prefix')
 for n in ['rejected.ckp','rejected-target.bin']:require((old_dir/n).read_bytes()==(replay_dir/n).read_bytes(),'same rejected entry/destination')
 require(not saved['original_auxiliary_failure_stderr_retained'],'honest auxiliary scope')
 return private
