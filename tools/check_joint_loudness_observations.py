"""Compare actual native endpoint observations to independent Decimal port currents."""
import json,time
from decimal import localcontext
from check_joint_loudness import state,D
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def audit():
 name='references-local/joint-loudness02/selected.txt';lines=(ROOT/name).read_text(encoding='utf8').splitlines();checks=[];c2=reset=count=None;endpoint=None;h=None
 for i,line in enumerate(lines):
  if line.startswith('PROFILE,'):
   _,c2,reset,h,count=line.split(',');c2,reset,h=float(c2),float(reset),float(h);count=int(count)
  if line.startswith('JOINT_ROOT,'):endpoint=state(lines[i+5])[0]
  if line.startswith('OBS,'):
   obs=list(map(float,line.split(',')[1:]));k=int(obs[0])
   if k not in [0,count-1]:continue
   require(endpoint is not None,'observed native endpoint');nvt=1.5*1.380649e-23*298.15/1.602176634e-19
   values=[(D(c2)-endpoint[200])/D(10000),-D(1e-8)*(((endpoint[204]-D(reset))/D(nvt)).exp()-1),(endpoint[203]-endpoint[165])/D(68000)]
   errors=[abs(float(x)-obs[col]) for x,col in zip(values,[3,4,5])];require(max(errors)<=1e-9,'actual native currents,1nA');require(float(endpoint[203])==obs[1] and float(endpoint[194])==obs[2],'actual native voltages')
   checks.append(dict(c2_v=c2,reset_v=reset,h_s=h,step=k,port_errors_a=errors))
 require(len(checks)==24,'24 native endpoint vectors');return dict(passed=True,endpoint_vectors=24,current_values=72,checks=checks,private_input_sha256={name:sha(ROOT/name)})
def main():
 names=['tools/check_joint_loudness_observations.py','tools/check_joint_loudness.py','evidence/voice_loudness_reference01.json'];before={n:sha(ROOT/n) for n in names};start=time.perf_counter()
 with localcontext() as ctx:ctx.prec=100;r=audit()
 r.update(source_sha256=before,source_sha256_after={n:sha(ROOT/n) for n in names},wall_s=time.perf_counter()-start);require(r['source_sha256']==r['source_sha256_after'],'source identity');write('evidence/voice_loudness_observations01.json',r);print('LOUDNESS_OBSERVATIONS',r['endpoint_vectors'],r['current_values'])
if __name__=='__main__':main()
