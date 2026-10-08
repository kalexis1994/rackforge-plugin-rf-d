import base64,json
from prepare_vco1_portable import ROOT,sha
def main():
    out=ROOT/'evidence/voice_chain_charge_before01.json';assert not out.exists()
    q=json.loads((ROOT/'evidence/voice_vco1_portable_tests01.json').read_text())
    for n,h in q['source_sha256'].items():assert sha(ROOT/n)==h,n
    for n,h in q['private_input_sha256'].items():assert sha(ROOT/n)==h,n
    mutable=['crates/rf-d-circuit/src/lib.rs','.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    out.write_text(json.dumps(dict(schema='rf-d/chain-charge-before/v1',base_commit='79b85364bf28ee207bf60faac62838d38410bfd1',
        previous_qa_sha256=sha(ROOT/'evidence/voice_vco1_portable_tests01.json'),
        mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable},
        protected_sources=len(q['source_sha256']),protected_private=len(q['private_input_sha256'])),indent=2)+'\n',encoding='utf8',newline='\n')
    print('Previous public/private hashes verified; mutable files snapshotted.')
if __name__=='__main__':main()
