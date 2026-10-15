"""Inline electrical return boundaries; preserve every original statement."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
def derive():
    result={}
    for name,functions in [('chain_charge',['linearize_prevalidated']),('contour_residual',['dc','parts']),('volume_residual',['linearize']),('filter_residual',['linearize'])]:
        s=(ROOT/f'crates/rf-d-circuit/src/prepared_{name}.rs').read_text(encoding='utf8')
        for f in functions:s=once(s,'pub fn '+f+'<const FULL:bool>', '#[inline(always)]\npub fn '+f+'<const FULL:bool>')
        if name=='contour_residual':s=s.replace('prepared_filter_residual.rs','inline_filter_residual.rs').replace('prepared_volume_residual.rs','inline_volume_residual.rs')
        result[f'crates/rf-d-circuit/src/inline_{name}.rs']=s
    g=(ROOT/'crates/rf-d-circuit/src/prepared_voice_chain.rs').read_text(encoding='utf8').replace('prepared_chain_charge.rs','inline_chain_charge.rs').replace('prepared_contour_residual.rs','inline_contour_residual.rs')
    from refine_inline_transfer import transform
    g=transform(g)
    v=(ROOT/'crates/rf-d-circuit/src/direct_hybrid_voice.rs').read_text(encoding='utf8').replace('prepared_voice_chain.rs','inline_voice_chain.rs')
    p=(ROOT/'tools/hybrid_direct_probe.rs').read_text(encoding='utf8')
    p=once(p,'stage_hybrid_voice.rs','direct_hybrid_voice.rs')
    p=once(p,'#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"] mod circuit;\n#[path=', '#[path="../crates/rf-d-circuit/src/inline_hybrid_voice.rs"] mod circuit;\n#[path=')
    local=(ROOT/'tools/hybrid_stamp_local.rs').read_text(encoding='utf8').replace('hybrid_schur_voice.rs','direct_hybrid_voice.rs').replace('prepared_hybrid_voice.rs','inline_hybrid_voice.rs')
    local=once(local,'let a=old::parts(po,','let a=old::parts::<true>(po,')
    guards=(ROOT/'tools/hybrid_stamp_guards.rs').read_text(encoding='utf8').replace('prepared_hybrid_voice.rs','inline_hybrid_voice.rs')
    result.update({'crates/rf-d-circuit/src/inline_voice_chain.rs':g,'crates/rf-d-circuit/src/inline_hybrid_voice.rs':v,'tools/hybrid_inline_probe.rs':p,'tools/hybrid_inline_local.rs':local,'tools/hybrid_inline_guards.rs':guards})
    return result
def main():
    out=ROOT/'evidence/hybrid_inline_before01.json';assert not out.exists();sources=derive();assert not any((ROOT/n).exists() for n in sources)
    previous='evidence/hybrid_support_tests01.json'
    write(out,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in sources.items():(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
