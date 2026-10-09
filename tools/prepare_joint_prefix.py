"""Freeze modal release and derive a bounded conditioned-prefix lab caller."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
def caller():
    text=(ROOT/'tools/joint_cycles_runner.rs').read_text(encoding='utf8')
    changes=[('const GOAL:u64=2752512000;','const GOAL:u64=262144000;'),
        ('let(p,initial)=scene()?;let mut engine=', 'let(p,seed)=scene()?;let conditioned=rf_d_circuit::joint_startup::condition(p,seed,rf_d_circuit::vco1_newton::Budget::default()).map_err(|e|format!("condition:{e:?}"))?;let initial=conditioned.state;eprintln!("CONDITIONED,iterations={},trials={},residual={:.17e},correction={:.17e},forcing_a={:.17e}",conditioned.iterations,conditioned.trials,conditioned.residual_ratio,conditioned.correction_ratio,conditioned.constraint_current_a);let mut engine='),
        ('if crossings<2||restores!=2||balance>0.002','if restores!=1||balance>0.002')]
    for a,b in changes:assert text.count(a)==1,a;text=text.replace(a,b)
    return text
def main():
    previous='evidence/voice_joint_modes_tests01.json';q=json.loads((ROOT/previous).read_text());assert q['passed']
    for key in ['source_sha256','private_input_sha256']:
        for n,h in q[key].items():assert sha(ROOT/n)==h,n
    names=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','.gitattributes']
    write('evidence/voice_joint_prefix_before01.json',dict(schema='rf-d/joint-prefix-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    target=ROOT/'tools/joint_conditioned_prefix_runner.rs';assert not target.exists();target.write_text(caller(),encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_conditioned_prefix_runner.rs text eol=lf\n')
    print('PREFIX_BEFORE',len(q['source_sha256']),len(q['private_input_sha256']),flush=True)
if __name__=='__main__':main()
