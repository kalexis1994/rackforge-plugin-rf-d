"""Bind every public advance to the own late-release interval and oriented Decimal charge."""
import base64,json,re,struct,sys,time,traceback
from decimal import localcontext
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from promote_assembly_voice import START,SPAN,CUT
from joint_cycles_analysis import require,TICK
from decay_control_reference import lift,ledger,packed
CODEC=struct.Struct('<8sQ6IdQd458d')
def audit():
 native=json.loads((ROOT/'evidence/voice_assembly_paired01.json').read_text(encoding='utf8'));require(native['passed'],'public paired campaign');profiles=[];private={};fields=0;inherited=0
 for p in native['profiles']:
  maximum=p['maximum_half_ticks'];directory=Path(p['command'][2]);a=(directory/'baseline.txt').read_bytes();b=(directory/'candidate.txt').read_bytes();require(a==b,'all exported fields by bytes');lines=a.decode('utf8').splitlines();admitted=ROOT/f'references-local/extended-release01/{maximum}/selected.txt';old=admitted.read_text(encoding='utf8').splitlines();want=[];states={};tick=0
  for i,l in enumerate(old):
   if l.startswith('STEP,'):
    r=l.split(',');t0,t1=int(r[2]),int(r[3]);tick=t1
    if START<=t0<t1<=START+SPAN:want.append(l)
    require(not(t0<START<t1 or t0<START+SPAN<t1),'existing Accepted aligns with both boundaries')
   elif l.startswith('OBS,'):
    t=int(l.split(',')[1])
    if START<t<=START+SPAN:want.append(l)
   elif l.startswith('GRID,'):
    t=int(l.split(',')[2]);states[t]=old[i+1]
    if START<t<=START+SPAN:want.extend([l,old[i+1]])
   elif l.startswith('SELECT,') and START<tick<=START+SPAN:inherited+=1374
  require(lines==want,'complete own late-release segment');raw=(directory/'grids.bin').read_bytes();require(len(raw)==6*3728,'six complete grids');points=[CODEC.unpack(raw[k:k+3728]) for k in range(0,len(raw),3728)];entry=ROOT/f'references-local/voice-assembly-seeds01/{maximum}.ckp';require(raw[:3728]==entry.read_bytes()==(directory/'entry.ckp').read_bytes(),'own input by bits')
  for k,q in enumerate(points):
   require(q[0]==b'RFDCY001' and q[1]==START+k*CUT and q[2]==maximum and q[3]==20 and q[5:8]==(0,1,1) and q[8]==0. and q[9]==0 and q[10]==1000.,'same typed grid recipe');require(packed(q[11:])==packed(list(map(float,states[q[1]].split(',')[1:]))),'all 458 inherited state values')
  require((directory/'final.ckp').read_bytes()==(directory/'candidate-final.ckp').read_bytes()==raw[-3728:],'final full identity');integrals=struct.unpack('<9d',(directory/'integrals.bin').read_bytes());balance=ledger(lift(points[0][11:]),lift(points[-1][11:]),integrals,SPAN);m=re.search(r'PAIRED_PASSED,(\d+),count=(\d+),baseline_ns=(\d+),candidate_ns=(\d+)',p['stderr']);require(m is not None,'runtime coverage');maximum2,count,t,u=map(int,m.groups());require(maximum2==maximum and count==sum(l.startswith('STEP,') for l in lines) and sum(l.startswith('OBS,') for l in lines)==2*count,'complete temporal output');fields+=sum(len(l.split(','))-1 for l in lines);profiles.append(dict(maximum_half_ticks=maximum,accepted_steps=count,fine_endpoints=2*count,grid_states=6,oriented_ledger=balance,baseline_kernel_ns=t,candidate_kernel_ns=u,kernel_ratio=u/t,all_accepted_fields_compared_by_native_caller=True,admitted_interval_identical=True))
  for f in directory.iterdir():
   if f.is_file():private[f.relative_to(ROOT).as_posix()]=sha(f)
  for f in [admitted,entry]:private[f.relative_to(ROOT).as_posix()]=sha(f)
 return dict(profiles=profiles,private_used_sha256=private,every_accepted_bits_identical=True,admitted_interval_identical=True,public_portable=True,duration_per_profile_s=.004,start_ticks=START,end_ticks=START+SPAN,accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_endpoints=sum(p['fine_endpoints'] for p in profiles),exported_fields_matched=fields,grid_states=12,new_independent_nonlinear_rows=0,inherited_independent_nonlinear_rows=inherited,new_circuit_duration_s=0,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 out='evidence/voice_assembly_reference01.json';require(not (ROOT/out).exists(),'exclusive interval audit');names={'tools/check_assembly_paired.py','tools/promote_assembly_voice.py','evidence/voice_assembly_paired01.json','docs/VOZ_ENSAMBLADO_PROTOCOLO.md','evidence/voice_extended_reference01.json','evidence/voice_zero_tests01.json'}
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=before);started=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(audit())
  require(time.perf_counter()-started<=600,'audit wall budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith('.py')}
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},wall_s=time.perf_counter()-started);require(before==r['source_sha256_after'],'stable auditor sources');write(out,r);print('ASSEMBLY_REFERENCE',r['passed'],r.get('failure',''),flush=True);require(r['passed'],'own interval and charges')
if __name__=='__main__':main()
