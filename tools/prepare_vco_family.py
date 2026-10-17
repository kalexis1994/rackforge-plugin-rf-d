"""Generate data only from the eight predeclared training cycles."""
import json,math
from prepare_dual_chain import ROOT,sha,write
from vco_family import CV,BUS,H,CHANNELS,complex_coeff
from vco_family_receipts import read,logical_sha
ORACLE='evidence/vco_family_oracle03.json'
DATA='tools/vco_family_data.rs'
def image(r):
    assert r['passed'] and len(r['training'])==8
    for k,x in enumerate(r['training']):
        assert x['scenario']['keyboard_v']==CV[k//2] and x['scenario']['imposed_mixer_v']==BUS[k%2]
    # No reserved/method/native data are consulted by this function.
    text='//! Generated training-only stationary calibrated family, SVC-9 pp.5/19.\n'
    logs=[[math.log2(r['training'][2*i+j]['reduction']['frequency_hz']) for j in range(2)] for i in range(4)]
    text+='pub const LOG_FREQUENCY:[[f64;2];4]=[\n'+''.join('['+','.join(f'{v:.17e}' for v in a)+'],\n' for a in logs)+'];\n'
    text+='pub const COEFFICIENTS:[[[[[f64;2];65];7];2];4]=[\n'
    for i in range(4):
        text+='[\n'
        for j in range(2):
            text+='[\n'
            for row in complex_coeff(r['training'][2*i+j]['reduction']):text+='[\n'+''.join(f'[{v.real:.17e},{v.imag:.17e}],\n' for v in row)+'],\n'
            text+='],\n'
        text+='],\n'
    return text+'];\n'
def main():
    r=read(ORACLE);text=image(r)
    assert image(dict(passed=True,training=r['training']))==text
    p=ROOT/DATA;assert not p.exists();p.write_text(text,encoding='utf8',newline='\n')
    write(ROOT/'evidence/vco_family_generation01.json',dict(passed=True,oracle=ORACLE,oracle_sha256=logical_sha(ORACLE),data=DATA,data_sha256=sha(p),training_ids=list(range(8)),reserved_data_used=False,reserved_sections_absent_identical_data=True,channels=CHANNELS,harmonics=H))
    print('FAMILY_DATA',p.stat().st_size)
if __name__=='__main__':main()
