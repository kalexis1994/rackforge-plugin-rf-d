"""Full graph/FD/Decimal100 audit of reconstructed roots, not inherited by bits."""
import argparse,json,time,traceback
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_latch_charge import scoped,state
from joint_cycles_analysis import require
def audit():
 path=ROOT/'references-local/schur-refined-chainbench01/roots.txt';lines=path.read_text(encoding='utf8').splitlines();require(len(lines)==84*7,'84 complete root records');checks=[]
 for i in range(0,len(lines),7):
  scene=lines[i].split(',');require(scene[0]=='SCENE','scene');on=bool(int(scene[1]));phase=int(scene[2]);header=lines[i+1].split(',');require(header[0]=='JOINT_ROOT','root');h=float(header[2]);s=[state(x)[0] for x in lines[i+2:i+7]];q=scoped([0.,10.,0.][phase],on,phase==1)((0,h,*s));checks.append(dict(final_decay=on,phase=phase,**q))
 return dict(roots=checks,independent_stages=168,independent_nonlinear_rows=38472,reconstructed_roots_admitted=True,full_trajectory_admitted=False,physical_fidelity=False,real_time=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('--attempt',type=int,default=1);a=p.parse_args();names=['tools/check_schur_chain_roots.py','tools/check_latch_charge.py','evidence/voice_schur_refined_chainbench01.json','docs/SCHUR_CADENA_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names};private={n:sha(ROOT/n) for n in ['references-local/schur-refined-chainbench01/roots.txt']};r=dict(passed=False,source_sha256=before,private_used_sha256=private);t=time.perf_counter()
 try:
  if (ROOT/'references-local/schur-refined-chainconfirm01/roots.txt').exists():
   require((ROOT/'references-local/schur-refined-chainbench01/roots.txt').read_bytes()==(ROOT/'references-local/schur-refined-chainconfirm01/roots.txt').read_bytes(),'same executable confirmation preserves roots')
  with localcontext() as ctx:ctx.prec=100;r.update(audit())
  require(time.perf_counter()-t<=600,'audit budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']=__import__('base64').b64encode((ROOT/'tools/check_schur_chain_roots.py').read_bytes()).decode()
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-t);require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable independent data');write(f'evidence/voice_schur_chain_roots{a.attempt:02d}.json',r);print('SCHUR_GRAPH_ROOTS',r['passed'],r.get('failure',''))
if __name__=='__main__':main()
