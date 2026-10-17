"""Expose the admitted full VCO kernels by path, preserving their arithmetic."""
from prepare_dual_chain import ROOT
from prepare_pitch_program import replace_once
ORIGINS={
 'tools/vco_cv_load_fine.rs':'references-local/vco1-radau-cycles04/fine.rs',
 'tools/vco_cv_load_linear.rs':'references-local/vco1-radau-cycles04/linear.rs',
 'tools/vco_cv_load_radau.rs':'references-local/vco1-radau-cycles04/radau.rs',
}
def images():
    out={}
    for target,origin in ORIGINS.items():
        s=(ROOT/origin).read_text(encoding='utf8')
        if target.endswith('_fine.rs'):s=replace_once(s,'#[path="vco1_stamp_data.rs"]','#[path="../crates/rf-d-circuit/src/vco1_stamp_data.rs"]')
        out[target]=s
    return out
def main():
    for n,s in images().items():
        p=ROOT/n
        if p.exists():assert p.read_bytes()==s.encode()
        else:p.write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
