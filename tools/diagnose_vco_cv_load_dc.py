"""Bounded original-deck diagnostics; solver iteration budget only, fixed error gates."""
import json,subprocess,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed,unpack
from check_vco_cv_load import Laboratory,AREA
from vco1_stamp_reference import EXE
from vco_cv_load_analysis import parse_roots
def main():
    path=ROOT/'evidence/vco_cv_load_dc_diagnostic01.json';assert not path.exists();s=Sources(['tools/diagnose_vco_cv_load_dc.py','tools/check_vco_cv_load.py']);r=dict(passed=False,**s.fields(),cases=[],plan='OP/sweep with itl1=itl2=1000, no tolerance/equation change',numerical_gates_unchanged=True)
    controls=json.loads((ROOT/'evidence/vco_cv_load_native02.json').read_text(encoding='utf8'));dc,_=parse_roots(unpack(controls['roots']['stdout']));target=dc[9][3:137]
    with Laboratory():
        for source in ['evidence/vco_cv_load_native02.json','evidence/vco_cv_load_native04.json']:
            old=json.loads((ROOT/source).read_text(encoding='utf8'));text=unpack(old['spice_failed_original']['deck']).decode();text=text.replace('.options temp=25','.options itl1=1000 itl2=1000 temp=25',1);deck=AREA/'dc.cir';out=AREA/'dc.txt';deck.write_text(text,encoding='utf8',newline='\n');cmd=[str(ROOT/EXE),'-n','-b',str(deck)];p=subprocess.run(cmd,cwd=(ROOT/EXE).parent,capture_output=True,timeout=180);x=dict(source=source,source_sha256=sha(ROOT/source),deck=packed(text.encode()),command=cmd,exit_code=p.returncode,stdout=packed(p.stdout),stderr=packed(p.stderr),passed=False)
            if out.exists():
                a=np.loadtxt(out,skiprows=1,ndmin=2);x['export']=packed(a.astype('<f8').tobytes());x['shape']=list(a.shape);nv=float(max(abs(a[-1,1:99]-target[:98])));na=float(max(abs(a[-1,99:135]-target[98:])));x.update(node_error_v=nv,branch_error_a=na,passed=nv<=2e-7 and na<=2e-10 and p.returncode==0 and b'error:' not in (p.stdout+p.stderr).lower());out.unlink()
            r['cases'].append(x);print('DC_DIAGNOSTIC',source,x['passed'],unpack(x['stderr']).decode()[-300:],flush=True)
    s.unchanged();r['temporary_area_empty']=not list(AREA.iterdir());r['passed']=any(x['passed'] for x in r['cases']);write(path,r)
if __name__=='__main__':main()
