"""Promote two actual load nodes; preserve the frozen dual-contour source."""
import base64, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
def generate():
    x=(ROOT/'crates/rf-d-circuit/src/dual_contour.rs').read_text(encoding='utf8')
    changes=[
      ('pub const N: usize = 54;', 'pub const N: usize = 56;'),
      ('if k < 29 { v[k] } else { 0. }','if k < 29 { v[k] } else { v[54] }'),
      ('for a in 0..29 {\n        s.dc[a] = vol.dc[a];\n        for b in 0..29 {\n            s.j[a][b] = vol.jacobian[a][b];\n        }\n    }',
       'for a in 0..30 {\n        let i = if a < 29 { a } else { 54 };\n        s.dc[i] = vol.dc[a];\n        for b in 0..30 {\n            let j = if b < 29 { b } else { 54 };\n            s.j[i][j] = vol.jacobian[a][b];\n        }\n    }'),
      ('    s.ports[5] += vol.dc[29];\n',''),
      ('let map = [38, 41, N + 6, N + 1, N + 2, N + 7, N + 8, N];',
       'let map = [38, 41, 55, N + 1, N + 2, N + 7, N + 8, N];'),
    ]
    for a,b in changes:
        assert x.count(a)==1,a
        x=x.replace(a,b)
    header='//! Generated promotion of VCA_BASE=54 and TAIL=55 into simultaneous unknowns.\n//! Source and exact substitutions: tools/prepare_dual_chain.py.\n'
    x=header+'\n'.join(x.splitlines()[2:])+'\n'
    out=ROOT/'crates/rf-d-circuit/src/dual_contour_loaded.rs'
    out.write_text(x,encoding='utf8',newline='\n')
    return sha(out)
if __name__=='__main__':
    before=ROOT/'evidence/dual_chain_before01.json'
    if not before.exists():
        qa='evidence/c5_trigger_tests01.json'
        write(before,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=qa,previous_qa_sha256=sha(ROOT/qa),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    print(generate())
