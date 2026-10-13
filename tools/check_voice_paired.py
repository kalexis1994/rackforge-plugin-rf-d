"""Bind the paired exact trajectory to the admitted prefix and nine charges."""
import argparse,base64,json,re,struct,time,traceback
from decimal import localcontext
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require,TICK
from check_latch_charge import lift,ledger,packed
START=14911799296;SPAN=2097152000;CUT=419430400
CODEC=struct.Struct('<8sQ6IdQd458d')

def audit(kind,attempt):
 name=f'evidence/voice_block_{kind}{attempt:02d}.json';native=json.loads((ROOT/name).read_text(encoding='utf8'));require(native['passed'],'paired campaign');profiles=[];private={};matched_fields=0
 for p in native['profiles']:
  maximum=p['maximum_half_ticks'];directory=Path(p['command'][2]);a=(directory/'baseline.txt').read_bytes();b=(directory/'candidate.txt').read_bytes();require(a==b,'every emitted field by bytes');lines=a.decode('utf8').splitlines();admitted=ROOT/f'references-local/decay-voice02/{maximum}/selected.txt';old=admitted.read_text(encoding='utf8').splitlines();want=[];states={};i=0
  while i<len(old):
   l=old[i]
   if l.startswith(('STEP,','OBS,')):
    tick=int(l.split(',')[3] if l.startswith('STEP,') else l.split(',')[1])
    if tick<=START+SPAN:want.append(l)
   if l.startswith('GRID,'):
    tick=int(l.split(',')[2]);states[tick]=old[i+1]
    if tick<=START+SPAN:want.extend([l,old[i+1]])
   i+=1
  require(lines==want,'entire admitted 4 ms prefix');raw=(directory/'grids.bin').read_bytes();require(len(raw)==6*3728,'six complete grid checkpoints');points=[CODEC.unpack(raw[k:k+3728]) for k in range(0,len(raw),3728)];entry=ROOT/f'references-local/decay-voice02/{maximum}/phase0-start.ckp';require(raw[:3728]==entry.read_bytes() and (directory/'entry.ckp').read_bytes()==entry.read_bytes(),'own input bits');
  for k,q in enumerate(points):
   require(q[0]==b'RFDCY001' and q[1]==START+k*CUT and q[2]==maximum and q[3]==20 and q[5:8]==(0,1,1) and q[8]==0. and q[9]==0 and q[10]==1000.,'typed grid metadata')
   if k:require(packed(q[11:])==packed(list(map(float,states[q[1]].split(',')[1:]))),'all inherited 458 grid values')
  require((directory/'final.ckp').read_bytes()==(directory/'candidate-final.ckp').read_bytes()==raw[-3728:],'final checkpoint identity');integrals=struct.unpack('<9d',(directory/'integrals.bin').read_bytes());balance=ledger(lift(points[0][11:]),lift(points[-1][11:]),integrals,SPAN)
  match=re.search(r'PAIRED_PASSED,(\d+),count=(\d+),baseline_ns=(\d+),candidate_ns=(\d+)',p['stderr']);require(match is not None,'runtime scope');m,n,t,u=map(int,match.groups());require(m==maximum and n==sum(l.startswith('STEP,') for l in lines),'runtime accepted count');obs=sum(l.startswith('OBS,') for l in lines);require(obs==2*n,'every fine endpoint');matched_fields+=sum(len(l.split(','))-1 for l in lines);profiles.append(dict(maximum_half_ticks=maximum,accepted_steps=n,fine_endpoints=obs,duration_ticks=SPAN,duration_s=SPAN*TICK,grid_states=6,oriented_ledger=balance,baseline_kernel_ns=t,candidate_kernel_ns=u,kernel_ratio=u/t,all_accepted_fields_compared_by_native_caller=True,admitted_prefix_identical=True))
  for f in directory.iterdir():
   if f.is_file():private[f.relative_to(ROOT).as_posix()]=sha(f)
  private[admitted.relative_to(ROOT).as_posix()]=sha(admitted);private[entry.relative_to(ROOT).as_posix()]=sha(entry)
 if kind=='portable':
  parent=json.loads((ROOT/'evidence/voice_block_paired_reference02.json').read_text(encoding='utf8'));require(parent['passed'],'laboratory paired comparison')
  for p in native['profiles']:
   for n in ['baseline.txt','candidate.txt','grids.bin','integrals.bin','final.ckp','candidate-final.ckp']:
    a=ROOT/f"references-local/voice-block-paired02/{p['maximum_half_ticks']}/{n}";b=Path(p['command'][2])/n;require(a.read_bytes()==b.read_bytes(),'promoted ABI/logical output and lab by bits');private[a.relative_to(ROOT).as_posix()]=sha(a)
 return dict(profiles=profiles,private_used_sha256=private,every_accepted_bits_identical=True,admitted_prefix_identical=True,public_portable=kind=='portable',duration_per_profile_s=.004,accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_endpoints=sum(p['fine_endpoints'] for p in profiles),exported_fields_matched=matched_fields,grid_states=12,new_independent_nonlinear_rows=0,original_graph_coverage_inherited_by_prefix=True,new_audio=False,physical_fidelity=False,real_time=False)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['paired','portable'],default='paired');parser.add_argument('--attempt',type=int,default=2);args=parser.parse_args();out=f'evidence/voice_block_{args.kind}_reference{args.attempt:02d}.json';require(not (ROOT/out).exists(),'exclusive prefix audit');names={'tools/check_voice_paired.py',f'evidence/voice_block_{args.kind}{args.attempt:02d}.json','docs/VOZ_COSTO_PIVOTE_PROTOCOLO.md','docs/VOZ_COSTO_BLOQUES_PROTOCOLO.md','evidence/voice_decay_tests01.json'}
 import sys
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 if args.kind=='portable':names.add('evidence/voice_block_paired_reference02.json')
 sources={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=sources);start=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(audit(args.kind,args.attempt))
  require(time.perf_counter()-start<=600,'oracle budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']=base64.b64encode((ROOT/'tools/check_voice_paired.py').read_bytes()).decode()
  try:
   with localcontext() as ctx:ctx.prec=100;audit(args.kind,args.attempt)
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in names},wall_s=time.perf_counter()-start);require(sources==r['source_sha256_after'],'stable prefix auditor');write(out,r);print('PAIRED_REFERENCE',args.kind,r['passed'],r.get('failure',''));require(r['passed'],'exact prefix and charges')
if __name__=='__main__':main()
