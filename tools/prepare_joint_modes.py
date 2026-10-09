"""Freeze the admitted initialization before additive modal diagnostics."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
def main():
    previous='evidence/voice_joint_startup_tests01.json';q=json.loads((ROOT/previous).read_text())
    assert q['passed']
    for key in ['source_sha256','private_input_sha256']:
        for n,h in q[key].items():assert sha(ROOT/n)==h,n
    names=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    write('evidence/voice_joint_modes_before01.json',dict(schema='rf-d/joint-modes-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    print('MODES_BEFORE',len(q['source_sha256']),len(q['private_input_sha256']),flush=True)
if __name__=='__main__':main()
