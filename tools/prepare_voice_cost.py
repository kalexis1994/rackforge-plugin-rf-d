"""Pack admitted full selected histories for phase costs and changed-solver checks."""
import base64,json,struct,subprocess
from prepare_dual_chain import ROOT,sha,write
def main():
    before=ROOT/'evidence/voice_cost_before01.json';assert not before.exists()
    previous='evidence/dual_voice_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));assert old['passed']
    write(before,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    out=ROOT/'references-local/voice-cost01';out.mkdir()
    cases=[];used={}
    for maximum in [1048576,524288]:
        path=ROOT/f'references-local/dual-voice02/profile-{maximum}.stdout';name=path.relative_to(ROOT).as_posix();assert sha(path)==old['private_input_sha256'][name];used[name]=sha(path)
        for line in path.read_text(encoding='utf8').splitlines():
            if line.startswith('ROOT,'):
                values=list(map(float,line.split(',')[1:]));assert len(values)==2505;cases.append(values[:2502])
    assert len(cases)==24
    (out/'pairs.bin').write_bytes(struct.pack('<'+str(2502*24)+'d',*(v for row in cases for v in row)))
    write(ROOT/'evidence/voice_cost_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_voice_cost.py','docs/VOZ_COSTO_PROTOCOLO.md']},private_used_sha256=used,private_sha256={str((out/'pairs.bin').relative_to(ROOT).as_posix()):sha(out/'pairs.bin')},pairs=24,independent_new_history=False))
    print('VOICE_COST_INPUTS',len(cases))
if __name__=='__main__':main()
