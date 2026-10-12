"""Freeze one truncated-SVD direction before any new own trajectory."""
import base64,json,struct,subprocess
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from conditioned_base_bank import bank,PATH

ATTR=b'\n/tools/dynamic_direction_tail.rs text eol=lf\n/tools/joint_dynamic_direction_runner.rs text eol=lf\n'

def main():
    previous='evidence/voice_conditioned_return_utf8_tests01.json';qa=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(qa['passed'] and head=='8e8fbefbe9da41ac8f7c9d4cc7563bc6da78f70f','base')
    write('evidence/voice_dynamic_direction_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    q=json.loads((ROOT/'evidence/voice_conditioned_return_reference01.json').read_text(encoding='utf8'));base=bank();a=np.array(q['native_capacitor_drift_derivative_v_per_target_v']);b=np.array([row['baseline_drift_v'] for row in q['capacitors']]);active=[k for k in range(18) if k!=16];aa=a[np.ix_(active,active)];u,s,vt=np.linalg.svd(aa,full_matrices=True);keep=s>1e-8*s[0];d=np.zeros(18);d[active]=vt[keep].T@((u[:,keep].T@(-b[active]))/s[keep]);trust=min(1.,.1/max(abs(d)));d*=trust;epsilon=1e-5/float(np.dot(base['gain'],abs(d)))
    require(np.count_nonzero(keep)==16 and d[16]==0 and np.max(abs(d))<=.1 and epsilon>0,'fixed selection')
    header=(ROOT/'tools/joint_charge_corrected_runner.rs').read_text(encoding='utf8').split('fn run()->Result<(),String>')[0];p=ROOT/'tools/joint_dynamic_direction_runner.rs';require(not p.exists(),'exclusive caller');p.write_text(header+(ROOT/'tools/dynamic_direction_tail.rs').read_text(encoding='utf8'),encoding='utf8',newline='\n');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
    p=ROOT/'references-local/dynamic-direction-inputs01.bin';require(not p.exists(),'exclusive input')
    points=sorted(base['samples'])
    with p.open('xb') as f:
        f.write(b'RFJDIRI1'+struct.pack('<I',42544));f.write(base['root'][:436].tobytes());f.write(struct.pack('<19d',*d,epsilon));f.write(struct.pack('<I20I',len(points),*points))
        for ticks,half,obs in base['schedule']:f.write(struct.pack('<QI7d',ticks,half,*obs))
    old_input='references-local/conditioned-return-inputs01.bin';private={n:sha(ROOT/n) for n in [PATH,old_input]}
    for n,h in private.items():require(h==qa['private_input_sha256'][n],'protected private')
    proposal=dict(active=active,rank=int(np.count_nonzero(keep)),relative_cutoff=1e-8,u=u.tolist(),singular_values=s.tolist(),vt=vt.tolist(),trust_scale=trust,direction_v=d.tolist(),epsilon_a=epsilon,predicted_drift_v=(b+a@d).tolist(),baseline_drift_v=b.tolist(),matrix_v_per_v=a.tolist(),predicted_period_change_s=float(base['dt']@d),predicted_j7_drift_v=float(base['drift'][194]+base['dd'][194]@d))
    write('evidence/voice_dynamic_direction_inputs01.json',dict(passed=True,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),private_used_sha256=private,points=points,steps=42544,proposal=proposal,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_dynamic_direction.py','tools/conditioned_base_bank.py','tools/dynamic_direction_tail.rs','tools/joint_charge_corrected_runner.rs','evidence/voice_conditioned_return_reference01.json','docs/VOZ_CORRECCION_DINAMICA_PROTOCOLO.md']}));print('DIRECTION_INPUTS',p.stat().st_size,epsilon,proposal['predicted_j7_drift_v'],flush=True)
if __name__=='__main__':main()
