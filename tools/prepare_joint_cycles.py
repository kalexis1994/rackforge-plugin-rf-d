"""Freeze the temporal engine before the first loaded-cycle campaign."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
def main():
    previous='evidence/voice_joint_engine_tests01.json';qa=json.loads((ROOT/previous).read_text())
    for group in ['source_sha256','private_input_sha256']:
        for n,h in qa[group].items():assert sha(ROOT/n)==h,n
    mutable=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','.gitattributes','crates/rf-d-circuit/src/lib.rs']
    write('evidence/voice_joint_cycles_before01.json',dict(schema='rf-d/joint-cycles-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
    print('CYCLES_BEFORE',len(qa['source_sha256']),len(qa['private_input_sha256']))
if __name__=='__main__':main()
