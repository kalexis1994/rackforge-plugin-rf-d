"""Correct the ordered-float observation adapter, retaining all numeric gates/data."""
import json,struct
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 bad=json.loads((ROOT/'evidence/voice_trigger_charge_reference01.json').read_text(encoding='utf8'));require(not bad['passed'] and bad['failure'].splitlines()[-1]==bad['replay'].splitlines()[-1]=='ValueError: actual native currents/voltages','preserved identical observer failure');source=ROOT/'tools/check_trigger_charge.py';require(sha(source)==bad['source_sha256']['tools/check_trigger_charge.py'],'unchanged failed observer')
 from check_trigger_charge import state,currents,D
 path='references-local/trigger-charge02/1-65536/selected.txt';lines=(ROOT/path).read_text(encoding='utf8').splitlines();i=next(k for k,v in enumerate(lines) if v.startswith('JOINT_ROOT,'));h=float(lines[i].split(',')[2]);states=[state(v) for v in lines[i+1:i+6]];x,raw=states[-1];obs=list(map(float,lines[i+6].split(',')[1:]));native=(raw[223]+raw[448])-.01
 with localcontext() as ctx:
  ctx.prec=100;exact=float(x[223]-D(.01));errors=[abs(float(a)-b) for a,b in zip(currents(x,8.3,0.,.01,True,[p[0] for p in states],h),obs[5:15])]
 require(max(errors)<=1e-9 and native==obs[17] and exact!=native,'single observation-order mismatch');write('evidence/voice_trigger_charge_observer_adapter01.json',dict(passed=True,native_data_receipt_sha256=sha(ROOT/'evidence/voice_trigger_charge_native02.json'),private_input_sha256={path:sha(ROOT/path)},failed_observer_sha256=sha(source),maximum_current_error_a=max(errors),decimal_then_float_c4_v=exact,ordered_native_c4_v=native,published_c4_v=obs[17],absolute_difference_v=abs(exact-native),native_bits=struct.pack('<d',native).hex(),decimal_bits=struct.pack('<d',exact).hex(),numerical_gates_changed=False,native_reexecuted=False))
 s=source.read_text(encoding='utf8');a="float(x[223]-D(.01))";b="float(x[223])-float(D(.01))";require(s.count(a)==1,'one ordered-float expression');source.write_text(s.replace(a,b),encoding='utf8',newline='\n');print('TRIGGER_OBSERVER_REPAIR')
if __name__=='__main__':main()
