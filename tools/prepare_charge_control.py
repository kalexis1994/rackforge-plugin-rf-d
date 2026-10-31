"""Prepare discrete operating points with a shared physical charge basis."""
import json
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from prepare_charge_reduced import capacitors

def add(a,b):
    s=a+b;v=s-a;return s,(a-(s-v))+(b-v)
def advance(h,l,x):
    h,e=add(h,x);l,f=add(l,e);h,l=add(h,l);return add(h,l+f)

def main():
    sources=Sources(['tools/prepare_charge_control.py']);name='evidence/charge_control_native01.json';r=json.loads((ROOT/name).read_text(encoding='utf8'));assert r['passed'];models=r['models'];native_dc=[]
    for line in unpack(r['export']['stdout']).decode().splitlines():
        z=line.split(',')
        if z[0]=='DC':native_dc.append(np.array(list(map(float,z[2:]))))
    highs=[];lows=[]
    for values in native_dc:
        hs=[];ls=[]
        for i,j,c in capacitors():
            h,l=values[i],values[68+i]
            if j<68:h,l=advance(h,l,-values[j]);h,l=advance(h,l,-values[68+j])
            hs.append(h);ls.append(l)
        highs.append(hs);lows.append(ls)
    def rust(v):return '['+','.join(map(rust,v))+']' if isinstance(v,list) else format(v,'.17e')
    text='//! Generated fixed cutoff points; absolute charge-voltage state, CHARGE_CONTROL_PROTOCOLO.\n'
    for key,ty in [('f','[[f64;18];18]'),('u0','[f64;18]'),('u1','[f64;18]'),('xq','[[f64;18];68]'),('xu','[f64;68]'),('dc','[f64;68]')]:text+=f'pub const {key.upper()}:[{ty};3]='+rust([m[key] for m in models])+';\n'
    for key,v in [('CAP_HIGH',highs),('CAP_LOW',lows)]:text+=f'pub const {key}:[[f64;18];3]='+rust(v)+';\n'
    path=ROOT/'tools/charge_control_data.rs';assert not path.exists();path.write_bytes(text.encode('utf8'));sources.unchanged();write(ROOT/'evidence/charge_control_preparation01.json',dict(passed=True,**sources.fields(),native_sha256=sha(ROOT/name),generated_sha256={path.relative_to(ROOT).as_posix():sha(path)},cutoff_values=r['cutoff_values'],cap_dc_high=highs,cap_dc_low=lows,dc_input_high_low_retained=True,no_parameter_interpolation=True,no_reserved_trajectory_fitting=True));print('CONTROL_PREPARED')
if __name__=='__main__':main()
