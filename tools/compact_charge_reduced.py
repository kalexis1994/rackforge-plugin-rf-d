"""Retire the oversized, unadmitted full export after bounded validation."""
import json
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from vco_family import decode_window

def main():
    sources=Sources(['tools/compact_charge_reduced.py']);old=json.loads((ROOT/'evidence/mono_voice_tests01.json').read_text(encoding='utf8'));oracle=json.loads((ROOT/'evidence/charge_reduced_oracle02.json').read_text(encoding='utf8'));domain=json.loads((ROOT/'evidence/charge_reduced_domain01.json').read_text(encoding='utf8'));validation=json.loads((ROOT/'evidence/charge_reduced_validation01.json').read_text(encoding='utf8'));assert oracle['passed'] and domain['passed'] and validation['passed']
    original=ROOT/oracle['pack'];compact=ROOT/domain['compact_pack'];assert original.parent.resolve()==(ROOT/'evidence').resolve() and not original.is_symlink() and original.resolve().is_relative_to(ROOT.resolve())
    assert original.relative_to(ROOT).as_posix() not in old['private_input_sha256'] and original.relative_to(ROOT).as_posix() not in old['source_sha256']
    assert sha(original)==oracle['pack_sha256'] and sha(compact)==domain['compact_sha256']
    for p,q in zip(oracle['profiles'],domain['profiles']):
        a=decode_window(p['window'],original);small=decode_window(q['full_state_window'],compact);assert a[q['full_state_rows']].tobytes()==small.tobytes()
    budget=sum(p.stat().st_size for p in(ROOT/'evidence').glob('charge_reduced*') if p!=original);assert budget<16*1024**2
    r=dict(passed=False,**sources.fields(),retired_path=oracle['pack'],retired_sha256=sha(original),retired_bytes=original.stat().st_size,retired_pack_was_unadmitted_generated_export=True,protected_inputs_retired=0,compact_path=domain['compact_pack'],compact_sha256=sha(compact),all_selected_full_states_verified_before_retirement=True,original_full_grid_not_reconstructible_from_compact=True,original_stream_digests_retained=True,full_grid_metrics_measured_before_retirement=True,resolves_retirement_pending_in='evidence/charge_reduced_domain01.json',domain_sha256=sha(ROOT/'evidence/charge_reduced_domain01.json'),validation_sha256=sha(ROOT/'evidence/charge_reduced_validation01.json'),retained_evidence_bytes_before_receipt=budget)
    out=ROOT/'evidence/charge_reduced_retirement01.json';assert not out.exists();write(out,r);original.unlink();r.update(passed=True,original_absent=not original.exists());sources.unchanged();write(out,r);print('CHARGE_RETIRED',r['retired_bytes'],budget)
if __name__=='__main__':main()
