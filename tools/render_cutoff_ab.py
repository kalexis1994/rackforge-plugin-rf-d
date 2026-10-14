"""Finite same-origin cutoff A/B: preserve clocks, levels, DC and feedback."""
import base64,json,struct,sys,time,traceback
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_cutoff_ab import START,SPAN
from joint_cycles_analysis import require,TICK
from render_conditioned_recipe import adapt,filtered,save,RATE,VOLTS_PER_FS
CODEC=struct.Struct('<8sQ6IdQ2d458d')
def inputs(opened,closed):return [opened,opened.with_name('incoming-original.ckp'),opened.with_name('final.ckp'),closed,*[closed.with_name(n) for n in ['event1-before.ckp','event1-after.ckp','event2-before.ckp']]]
def state(line):
 require(line.startswith('JOINT_STATE,'),'full A/B state');v=list(map(float,line.split(',')[1:]));require(len(v)==458 and np.isfinite(v).all(),'finite complete A/B state');return v
def recipe(raw,tick,phase,alpha,values):
 require(len(raw)==3736,'complete A/B recipe');q=CODEC.unpack(raw);m=q[2];require(q[:2]==(b'RFCTF001',tick) and m in [1048576,524288] and q[3]==20 and 8<=q[4]<=2*m and q[4]&(q[4]-1)==0 and q[5:12]==(phase,1,1,0.,0,1000.,alpha) and raw[72:]==struct.pack('<458d',*values),'A/B clock controls and state recipe');return q
def read_pair(opened,closed):
 a=opened.read_text(encoding='utf8').splitlines();b=closed.read_text(encoding='utf8').splitlines();require(a[0]==b[0],'A/B matching resolution');initial=state(a[1]);boundary=next(i for i,line in enumerate(b) if line.startswith('BOUNDARY,1,'));closed_initial=state(b[boundary+1]);require(struct.pack('<458d',*initial)==struct.pack('<458d',*closed_initial),'same initial A/B state');require(b[boundary].split(',')[1:]==['1',str(START),'0.00000000000000000e0','0'] and a[2].split(',')[1:]==['0',str(START),'0.00000000000000000e0','0'],'common A/B source clock')
 ob=[list(map(float,line.split(',')[1:])) for line in a if line.startswith('OBS,')];cb=[list(map(float,line.split(',')[1:])) for line in b if line.startswith('OBS,') and int(line.split(',')[2])==1];require(ob and cb and all(len(row)==24 for row in ob+cb),'complete A/B observations');traces=[];final_open=state(a[-1]);end_boundary=next(i for i,line in enumerate(b) if line.startswith('BOUNDARY,2,'));final_closed=state(b[end_boundary-1]);require(a[-2].startswith('TOTAL,') and a[-1].startswith('JOINT_STATE,') and b[end_boundary-2].startswith('LEDGER,1,'),'complete A/B phase endpoints')
 before=closed.with_name('event1-before.ckp').read_bytes();after=closed.with_name('event1-after.ckp').read_bytes();incoming=opened.with_name('incoming-original.ckp').read_bytes();require(before==incoming and before[:28]==after[:28] and before[32:64]==after[32:64] and before[72:]==after[72:],'same A/B origin recipe clock and proposal');q=recipe(before,START,0,1.,initial);m=q[2];require(recipe(after,START,1,.5,initial)[2]==m,'closed branch alpha');require(recipe(opened.with_name('final.ckp').read_bytes(),START+SPAN,0,1.,final_open)[2]==m and recipe(closed.with_name('event2-before.ckp').read_bytes(),START+SPAN,1,.5,final_closed)[2]==m,'complete A/B final recipes')
 for rows,phase,final in [(ob,0,final_open),(cb,1,final_closed)]:
  ticks=np.array([int(row[0]) for row in rows],dtype='<u8');volts=np.array([row[4] for row in rows]);require(np.isfinite(np.array(rows)).all() and all(row[1]==phase for row in rows) and ticks[0]>START and ticks[-1]==START+SPAN and np.all(np.diff(ticks)>0),'complete monotonic A/B window');require(np.float64(volts[-1]).tobytes()==np.float64(final[194]+final[423]).tobytes(),'final A/B J7 by bits');t=np.r_[0.,(ticks-START).astype(float)*TICK];v=np.r_[initial[194]+initial[423],volts];traces.append((t,v))
 return m,traces
def code_hashes():
 names=set()
 for module in list(sys.modules.values()):
  f=getattr(module,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 return {n:sha(ROOT/n) for n in sorted(names)}
def pair_audio(opened,closed):
 m,traces=read_pair(opened,closed);pcm=[];signals=[];metadata=[]
 for t,v in traces:
  p,meta=adapt(t,v,1);require(meta['frames']==384,'eight real milliseconds');pcm.append(p);metadata.append(meta);signals.append(filtered(t,v,(np.arange(384)+.5)/RATE,16))
 x,y=signals;metrics=dict(mean_open_v=float(np.mean(x)),mean_closed_v=float(np.mean(y)),rms_open_v=float(np.sqrt(np.mean(x*x))),rms_closed_v=float(np.sqrt(np.mean(y*y))),rms_difference_v=float(np.sqrt(np.mean((x-y)**2))),max_difference_v=float(np.max(abs(x-y))),peak_open_v=float(np.max(abs(x))),peak_closed_v=float(np.max(abs(y))),rms_about_mean_open_v=float(np.std(x)),rms_about_mean_closed_v=float(np.std(y)))
 return m,pcm,metadata,signals,metrics
def derive():
 rows=[]
 for m in [1048576,524288]:rows.append(pair_audio(ROOT/f'references-local/cutoff-ab01/{m}/selected.txt',ROOT/f'references-local/voice-cutoff01/{m}/selected.txt'))
 errors=[]
 for branch in range(2):
  voltage=float(np.max(abs(rows[0][3][branch]-rows[1][3][branch])));pcm=int(np.max(abs(rows[0][1][branch].astype(int)-rows[1][1][branch].astype(int))));require(voltage<=2e-6 and pcm<=7,'same-branch resolution gate');errors.append(dict(branch=['open','closed'][branch],max_error_v=voltage,max_error_pcm_lsb=pcm))
 return rows,errors
def main():
 ref='evidence/cutoff_ab_reference01.json';out='evidence/cutoff_ab_listening01.json';folder=ROOT/'artifacts/cutoff-ab01';require(json.loads((ROOT/ref).read_text(encoding='utf8'))['passed'] and not folder.exists() and not (ROOT/out).exists(),'admitted reference and exclusive A/B audio');before={**code_hashes(),ref:sha(ROOT/ref),'docs/VOZ_CUTOFF_AB_PROTOCOLO.md':sha(ROOT/'docs/VOZ_CUTOFF_AB_PROTOCOLO.md')};private={}
 for m in [1048576,524288]:
  for p in inputs(ROOT/f'references-local/cutoff-ab01/{m}/selected.txt',ROOT/f'references-local/voice-cutoff01/{m}/selected.txt'):private[p.relative_to(ROOT).as_posix()]=sha(p)
 start=time.perf_counter();r=dict(passed=False,source_sha256=before,private_used_sha256=private,files=[],new_continuous_history_duration_s=0,new_open_branch_duration_s=.008,sample_rate_hz=48000,resampling_cutoff_hz=18000,volts_per_full_scale=VOLTS_PER_FS,dc_removed=False,peak_normalization=False,fades=False,repeated=False,physical_fidelity=False,real_time=False)
 try:
  a,e=derive();b,e2=derive();require(e==e2 and all(x[0]==y[0] and x[2]==y[2] and x[4]==y[4] and all(np.array_equal(u,v) for u,v in zip(x[1]+x[3],y[1]+y[3])) for x,y in zip(a,b)),'full A/B derivation replay');folder.mkdir(parents=True)
  for m,pcm,meta,_,metrics in a:
   for branch,p,md in zip(['open','closed'],pcm,meta):
    path=folder/f'rf-d-cutoff-ab-{branch}-8ms-{m}.wav';save(path,p);r['files'].append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size,branch=branch,maximum_half_ticks=m,**md))
  r.update(passed=True,identical_derived_replay=True,refinement=e,ab_metrics=[dict(maximum_half_ticks=x[0],**x[4]) for x in a])
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in before if n.endswith('.py')}
  try:derive();r['replay']='unexpected pass or publication failure'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in before},private_used_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start);require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable A/B inputs');write(out,r);print('CUTOFF_AB_AUDIO',r['passed'],r.get('failure',''));require(r['passed'],'paired branch audio')
if __name__=='__main__':main()
