"""Freeze the port contract and build public fixtures from admitted evidence."""
import base64, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def write(name,x):
    p=ROOT/name
    if p.exists(): raise ValueError(f'preserve {name}')
    p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
    old=json.loads((ROOT/'evidence/voice_vco1_radau_cycles_tests01.json').read_text())
    for name,digest in old['source_sha256'].items():
        assert sha(ROOT/name)==digest,name
    for name,digest in old['private_input_sha256'].items():
        assert sha(ROOT/name)==digest,name
    changed=['crates/rf-d-circuit/src/lib.rs','.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    write('evidence/voice_vco1_portable_before01.json',dict(
        schema='rf-d/portable-before/v1',base_commit='06b78be0cd8cb5addbe7e673ad283688de21d8b2',
        previous_qa_sha256=sha(ROOT/'evidence/voice_vco1_radau_cycles_tests01.json'),
        protected_sources=len(old['source_sha256']),protected_private=len(old['private_input_sha256']),
        source_sha256=old['source_sha256'],private_input_sha256=old['private_input_sha256'],
        mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in changed}))
    fine=(ROOT/'references-local/vco1-radau-cycles04/fine.rs').read_bytes()
    public=(ROOT/'crates/rf-d-circuit/src/vco1_increment.rs').read_bytes()
    assert fine==public.replace(b'125e-9/4096.',b'125e-9/65536.')
    (ROOT/'crates/rf-d-circuit/src/vco1_radau_fine.rs').write_bytes(fine)
    kernel=(ROOT/'tools/vco1_radau_residual_kernel.rs').read_bytes()
    assert kernel.count(b'fine::{self,State,Solution}')==1
    (ROOT/'crates/rf-d-circuit/src/vco1_radau.rs').write_bytes(kernel.replace(
        b'fine::{self,State,Solution}',b'vco1_radau_fine::{self as fine,State,Solution}'))
    bank=json.loads((ROOT/'evidence/voice_vco1_radau_cycles04.json').read_text())
    newton=json.loads((ROOT/'evidence/voice_vco1_radau_newton01.json').read_text())
    intervals=bank['profiles'][1]['actual_intervals']
    # Store entire admitted records: history, stages, Decimal roots and currents.
    write('evidence/voice_vco1_portable_vectors01.json',dict(
        schema='rf-d/portable-vectors/v1',bank_sha256=sha(ROOT/'evidence/voice_vco1_radau_cycles04.json'),
        diagnostic_sha256=sha(ROOT/'evidence/voice_vco1_radau_newton01.json'),
        actual_intervals=intervals,diagnostic=dict(previous_high=newton['previous_high'],
        previous_low=newton['previous_low'],elapsed_ticks=newton['elapsed_ticks'],
        independent=newton['independent'],residual_method=next(m for m in newton['methods'] if m['method']=='residual'))))
    print('Frozen inputs, exact physical fine port and residual kernel; fixtures prepared.')
if __name__=='__main__': main()
