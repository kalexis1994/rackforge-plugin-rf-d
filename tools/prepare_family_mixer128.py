"""Training-only harmonic extension; protected H64 data and code stay intact."""
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from vco_family_receipts import read,logical_sha
from vco_family import decode_window,COLS,complex_coeff,coefficients
def main():
    sources=Sources(['tools/prepare_family_mixer128.py','docs/FAMILIA_MIXER_BANDA.md','tools/vco_family_kernel.rs','tools/family_mixer_kernel.rs','tools/family_mixer_probe.rs','tools/vco_family_data.rs'])
    oracle=read('evidence/vco_family_oracle03.json');blocks=[]
    for i,x in enumerate(oracle['training']):
        raw=decode_window(x['window'],ROOT/x.get('window_pack',oracle['pack']));a,b=x['measurements']['reset_crossings_s'][-2:];t=raw[:,0];knots=np.r_[a,t[(t>a)&(t<b)],b];p=(knots-a)/(b-a);p[0]=0.;p[-1]=1.
        c=np.array([coefficients(p,np.interp(knots,t,raw[:,k]),128) for k in COLS]);assert np.array_equal(c[:,:65],complex_coeff(x['reduction']));blocks.append(c);print('H128_TRAINING',i,flush=True)
    old=(ROOT/'tools/vco_family_data.rs').read_text(encoding='utf8');prefix=old.split('pub const COEFFICIENTS:')[0];text=prefix+'pub const COEFFICIENTS:[[[[[f64;2];129];7];2];4]=[\n'
    for i in range(4):
        text+='[\n'
        for j in range(2):
            text+='[\n'
            for row in blocks[2*i+j]:text+='[\n'+''.join(f'[{v.real:.17e},{v.imag:.17e}],\n' for v in row)+'],\n'
            text+='],\n'
        text+='],\n'
    outputs={'tools/family_mixer_data128.rs':text+'];\n'}
    s=(ROOT/'tools/vco_family_kernel.rs').read_text(encoding='utf8');assert s.count('0..=64')==1;outputs['tools/family_mixer_family128.rs']=s.replace('0..=64','0..=128',1)
    s=(ROOT/'tools/family_mixer_kernel.rs').read_text(encoding='utf8');assert s.count('1..=64')==1;outputs['tools/family_mixer_kernel128.rs']=s.replace('vco_family_kernel.rs','family_mixer_family128.rs',1).replace('1..=64','1..=128',1)
    s=(ROOT/'tools/family_mixer_probe.rs').read_text(encoding='utf8');outputs['tools/family_mixer_probe128.rs']=s.replace('vco_family_data.rs','family_mixer_data128.rs',1).replace('family_mixer_kernel.rs','family_mixer_kernel128.rs',1)
    for n,s in outputs.items():
        p=ROOT/n;assert not p.exists();p.write_text(s,encoding='utf8',newline='\n')
    sources.unchanged();write(ROOT/'evidence/family_mixer128_generation01.json',dict(passed=True,**sources.fields(),training_oracle_sha256=logical_sha('evidence/vco_family_oracle03.json'),training_count=8,reserved_data_used=False,harmonics=128,first_65_coefficients_bitwise_identical=True,generated_sha256={n:sha(ROOT/n) for n in outputs},old_data_sha256=sha(ROOT/'tools/vco_family_data.rs')))
if __name__=='__main__':main()
