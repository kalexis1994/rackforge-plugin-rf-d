"""Explain retained NG-46 AC/DC substrate GMIN discrepancy without new solves."""
import json,math
from decimal import localcontext
from vco_bjt_vectors import ROOT,sha,reference
SOURCE='references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/devices/bjt/bjtacld.c'
def audit():
 p=ROOT/'evidence/voice_vco_bjt_spice02.json';r=json.loads(p.read_text(encoding='utf8'));cases=[]
 if not r['passed']:raise ValueError('complete independent probes')
 for row in r['cases']:
  with localcontext() as ctx:ctx.prec=100;expected=reference(row['polarity'],row['terminal_v'],row['terminal_v'],125e-9)
  target=0 if row['polarity']==1 else 1;inc=[0.]*4;inc[target]=1.;inc[3]=-1.
  direct=[];completed=[]
  for i in range(4):
   for j in range(4):
    native=complex(expected[12+4*i+j],2*math.pi*1000*expected[44+4*i+j]);raw=complex(row['admittance_real_s'][i][j],row['admittance_imag_s'][i][j]);missing=1e-12*inc[i]*inc[j]
    direct.append(abs(raw-native));completed.append(abs(raw+missing-native))
  cases.append(dict(polarity=row['polarity'],terminal_v=row['terminal_v'],max_direct_error_s=max(direct),max_after_explicit_missing_ac_branch_s=max(completed)))
 return dict(schema='rf-d/vco-bjt-ac-audit/v1',spice_receipt_sha256=sha(p),source_sha256={SOURCE:sha(ROOT/SOURCE),'tools/vco_bjt_ac_audit.py':sha(ROOT/'tools/vco_bjt_ac_audit.py')},cases=cases,explanation='bjtload.c includes gdsub in DC/transient; bjtacld.c loads substrate charge only and omits gdsub real stamp. Native retains full DC/Euler derivative. Raw AC data and gates unchanged.',new_spice_processes=0,raw_or_kernel_modified=False,maximum_direct_error_s=max(c['max_direct_error_s'] for c in cases),maximum_after_explicit_missing_ac_branch_s=max(c['max_after_explicit_missing_ac_branch_s'] for c in cases))
def main():
 p=ROOT/'evidence/voice_vco_bjt_ac_audit01.json'
 if p.exists():raise ValueError('preserve audit')
 r=audit();p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print(r['maximum_direct_error_s'],r['maximum_after_explicit_missing_ac_branch_s'])
if __name__=='__main__':main()
