"""Summarize preserved reset failures and a separately scoped substep probe."""
import json
import numpy as np
from vco1_newton_reference import ROOT,sha
from vco1_circuit_probes import observations,GATES
from vco1_native_cycles import NODES

def main():
 out=ROOT/'evidence/voice_vco1_reset_diagnostics01.json'
 if out.exists():raise ValueError('preserve diagnostic summary')
 work=ROOT/'references-local/vco1-native-cycles01';cycle=json.loads((ROOT/'evidence/voice_vco1_native_cycles01.json').read_text(encoding='utf8'))
 fixed=json.loads((work/'diagnostic-step-bank.json').read_text(encoding='utf8'));ind=json.loads((work/'failure-independent.json').read_text(encoding='utf8'));pred=[json.loads((work/f'predictor-{ns}-receipt.json').read_text(encoding='utf8')) for ns in (500,250,125)]
 if cycle['passed'] or len(cycle['unchanged_replays'])!=1 or cycle['unchanged_replays'][0]['exit_code']!=cycle['commands'][-1]['exit_code']:raise ValueError('original/replay fixed bank')
 if any(c['exit_code']==0 or c['unchanged_replay']['exit_code']!=c['exit_code'] or c['unchanged_replay']['sha256']!=c['original_sha256'] for c in fixed):raise ValueError('fixed diagnostic replay')
 if any(c['exit_code']==0 or c['unchanged_replay']['exit_code']!=c['exit_code'] or c['unchanged_replay']['export_sha256']!=c['export_sha256'] for c in pred):raise ValueError('predictor replay')
 if ind['passed'] or ind['error']!=ind['unchanged_replay_error']:raise ValueError('independent reject')
 probe=work/'substep-probe01';receipt=json.loads((probe/'receipt.json').read_text(encoding='utf8'));path=probe/'trajectory.bin';raw=np.memmap(path,dtype='<f8',mode='r').reshape(-1,143)
 if any(c['exit_code'] for c in receipt['commands']) or raw[-1,0]!=.03:raise ValueError('diagnostic complete probe')
 def measure():return observations(np.column_stack([raw[:,0],*[raw[:,1+n] for n in NODES],raw[:,135],raw[:,136]]),None)
 m=measure();again=measure()
 if m!=again:raise ValueError('same export measurement replay')
 private={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(work.rglob('*')) if p.is_file()}
 sources=['tools/vco1_reset_diagnostics.py','tools/vco1_native_cycles.py','tools/vco1_native_trajectory.rs','tools/vco1_circuit_probes.py','tools/vco1_circuit_reference.py','evidence/voice_vco1_native_cycles01.json']
 for n,h in receipt['modified_source_sha256'].items():
  if sha(probe/n)!=h:raise ValueError('retained modified probe source')
 r=dict(schema='rf-d/vco1-reset-diagnostic/v1',passed=True,production_full_cycles_admitted=False,production_fixed_bank_passed=False,gates=GATES,fixed_rejects=[dict(dt_ns=500,error=cycle['commands'][-1]['stderr'])]+[dict(dt_ns=int(c['command'][1]),error=c['stderr']) for c in fixed],independent_500ns_error=ind['error'],predictor_rejects=[dict(dt_ns=int(c['command'][1]),error=c['stderr']) for c in pred],substep_probe=dict(production=False,original_sources_unchanged=True,changed_guards=['vco1_stamp.rs','vco_bjt.rs','vco_jfet.rs','lm741.rs'],guard_floor_s=1e-9,minimum_actual_dt_s=float(np.min(np.diff(raw[:,0]))),maximum_dt_s=float(np.max(np.diff(raw[:,0]))),rows=len(raw),last_time_s=float(raw[-1,0]),measurements=m,period_spread_gate_passed=m['period_spread_relative']<=GATES['period_spread_relative'],charge_gate_passed=m['cycle_charge_check']['relative_imbalance']<=GATES['cycle_charge_relative'],metrics_replay_identical=True),source_sha256={n:sha(ROOT/n) for n in sources},private_input_sha256=private,new_spice_processes=0,new_audio=False,next='derive and verify short-step API and accuracy policy; reject-only halving still misses periodicity gate')
 out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('Reset diagnostics preserved; complete private substep probe, periodicity gate:',r['substep_probe']['period_spread_gate_passed'],flush=True)
if __name__=='__main__':main()
