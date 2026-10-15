"""Freeze parent admission and derive the 222-coordinate solver/probe."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
def derive():
    s=(ROOT/'crates/rf-d-circuit/src/direct_hybrid_solver.rs').read_text(encoding='utf8')
    for a,b in [('pub const M:usize=236;','pub const M:usize=222;'),('pub const N:usize=118;','pub const N:usize=111;'),
                ('[54,55,172,173]','[54,55,165,166]'),('a-56+62*stage','a-56+55*stage'),('i+64','i+57')]:s=once(s,a,b)
    s=once(s,'const AUDIO:[usize;124]={let mut x=[0;124];let mut i=0;while i<124{x[i]=if i<62{i+56}else{i+112};i+=1;}x};',
             'const AUDIO:[usize;110]={let mut x=[0;110];let mut i=0;while i<110{x[i]=if i<55{i+56}else{i+112};i+=1;}x};')
    s=s.replace('124','110')
    s='//! Derived direct solver: 111 coordinates/stage, 108 contour + 110 audio + 4 ports.\n'+s
    p=(ROOT/'tools/hybrid_direct_probe.rs').read_text(encoding='utf8')
    p=once(p,'stage_hybrid_voice.rs','direct_hybrid_voice.rs');p=once(p,'#[cfg(condensed)]\n#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"]', '#[cfg(condensed)]\n#[path="../crates/rf-d-circuit/src/ladder_voice.rs"]')
    return {'crates/rf-d-circuit/src/ladder_voice_solver.rs':s,'tools/ladder_voice_probe.rs':p}
def main():
    path=ROOT/'evidence/ladder_voice_before01.json';assert not path.exists();out=derive();assert not any((ROOT/n).exists() for n in out)
    previous='evidence/ladder_algebraic_tests01.json';mutable=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    write(path,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
    for n,s in out.items():(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
