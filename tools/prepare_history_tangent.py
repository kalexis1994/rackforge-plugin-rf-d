"""Preserve the previous admission and four exact selected-step inputs."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write

def main():
    previous='evidence/voice_joint_corrected_cycles_tests01.json';old=json.loads((ROOT/previous).read_text());assert old['passed']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert head=='8ac0d612933d266a41e6975e96776e3f3cf5d29a'
    names=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    write('evidence/voice_history_tangent_before01.json',dict(schema='rf-d/history-tangent-before/v1',base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    native=json.loads((ROOT/'evidence/voice_joint_corrected_cycles_native01.json').read_text());assert native['passed']
    paths=[]
    for p in native['profiles']:
        path=__import__('pathlib').Path(p['command'][3])/'selected.txt';name=path.relative_to(ROOT).as_posix();assert sha(path)==old['private_input_sha256'][name];paths.append(name)
    assert len(paths)==4
    target=ROOT/'references-local/history-tangent-inputs01.txt';assert not target.exists();target.write_text('\n'.join(paths)+'\n',encoding='utf8',newline='\n')
    attr=ROOT/'.gitattributes';attr.write_bytes(attr.read_bytes()+b'\n/tools/joint_history_tangent.rs text eol=lf\n/tools/joint_history_tangent_runner.rs text eol=lf\n')
    write('evidence/voice_history_tangent_inputs01.json',dict(passed=True,source_sha256={'tools/prepare_history_tangent.py':sha(ROOT/'tools/prepare_history_tangent.py')},selected_sha256={n:sha(ROOT/n) for n in paths},path=target.relative_to(ROOT).as_posix(),sha256=sha(target)))
    print('HISTORY_INPUTS',len(paths))
if __name__=='__main__':main()
