"""Generate numerical maps without copying any private device/source data."""
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from recovery_cost_exp_model import build,cases,independent_maps

def main():
    models=[build(c) for c in cases()];independent=[independent_maps(m) for m in models];typ={'dc':'[f64;68]','iexp':'[f64;12]','f':'[[f64;18];18]','u0':'[f64;18]','u1':'[f64;18]','n0':'[[f64;12];18]','n1':'[[f64;12];18]','xq':'[[f64;18];68]','xu':'[f64;68]','xd':'[[f64;12];68]','zh':'[[f64;18];12]','zu':'[f64;12]','p':'[[f64;12];12]'}
    def rust(v):return '['+','.join(map(rust,v))+']' if isinstance(v,list) else format(v,'.17e')
    name='tools/recovery_cost_exp_data.rs';out='//! Semilinear exponential FOH maps from own RF-D SVC-9 stamp.\n'
    for key,ty in typ.items():out+=f'pub const {key.upper()}:[{ty};3]='+rust([m[key].tolist() for m in models])+';\n'
    target=ROOT/name
    if target.exists():assert target.read_bytes()==out.encode()
    else:target.write_bytes(out.encode())
    sources=Sources(['tools/prepare_recovery_cost_exp.py','tools/recovery_cost_exp_model.py','docs/RECOVERY_COST_EXP_PROTOCOLO.md','docs/RECOVERY_COST_EXP_MAPAS.md']);path=ROOT/'evidence/recovery_cost_exp_maps01.json';assert not path.exists()
    write(path,dict(passed=True,**sources.fields(),generated_sha256={name:sha(target)},checks=[{k:m[k] for k in ['projection_error','imaginary_error','semigroup_error','identity_scaled','eigen_residual']} for m in models],independent=independent,retained_charge_coordinates=18,constitutive_laws=12))
if __name__=='__main__':main()
