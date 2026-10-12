"""Independent graph/FD/Decimal217 admission, new capacitor memory and source loading."""
import argparse,inspect,json,math,re,struct,sys,time,traceback
from decimal import localcontext
from functools import lru_cache
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_c2_charge import START,SPAN,SOURCES
from c2_charge_reference import problem as driver_problem
from check_joint_loudness import problem as follower_problem,D
import check_joint_reference as original
from joint_cycles_analysis import require,TICK
CODEC=struct.Struct('<8sQII3dII434d')
def state(line):
 v=list(map(float,line.split(',')[1:]));require(len(v)==434,'217 high/low codec');return lift(v),v
def packed(v):return struct.pack('<434d',*v)
def lift(v):return [D(v[k])+D(v[k+217]) for k in range(217)]
def checkpoint(raw):
 require(len(raw)==3528,'217 checkpoint size');r=CODEC.unpack(raw);magic,ticks,half,phase,q25,driver,reset,on,reserved,*v=r;require(magic==b'RFLC2C01' and half in [65536,32768] and phase in range(5) and on in [0,1] and reserved==0 and START+phase*SPAN<=ticks<=START+(phase+1)*SPAN and (ticks-START)%half==0,'checkpoint metadata');require(struct.pack('<3d',q25,driver,reset)==struct.pack('<3d',*SOURCES[phase]) and CODEC.pack(*r)==raw,'source recipe/typed roundtrip');require(all(math.isfinite(x) for x in v),'finite state')
 for k in range(217):
  exact=D(v[k])+D(v[k+217]);h=float(exact);l=float(exact-D(h));require(struct.pack('<2d',h,l)==struct.pack('<2d',v[k],v[k+217]),'normalized high/low')
 return dict(ticks=ticks,half=half,phase=phase,sources=[q25,driver,reset],final_decay=bool(on),values=v,raw_sha256=__import__('hashlib').sha256(raw).hexdigest())
def ci(k):return original.ci(k) if k<68 else k+132
@lru_cache(None)
def problem(q25,driver,reset,on,r61,mask,sources):
 core,_,y=follower_problem(0.,reset,r61,mask,sources);_,network=driver_problem(q25,driver,on)
 def dc(x):
  r=np.zeros(85);r[:73]=core(x[:73]);r[68]-=x[73]/10000.;r[73:]=network(x[73:]);r[73]+=(x[73]-x[68])/10000.;return r
 def gradient(x):
  j=np.empty((85,85))
  for k in range(85):
   a=x.copy();b=x.copy();a[k]+=1e-6;b[k]-=1e-6;j[:,k]=(dc(a)-dc(b))/2e-6
  return j
 return dc,gradient,y
def scoped(q25,driver,reset,on):
 body=inspect.getsource(original.evaluate).replace('range(68)','range(85)').replace('Decimal(0)]*68','Decimal(0)]*85').replace('zeros((68,68))','zeros((85,85))');g=dict(original.__dict__,N=217,ci=ci,CAPS=[*original.CAPS,(73,None,10e-6)],problem=lambda r,m,s:problem(q25,driver,reset,on,r,m,tuple(s)));exec(compile(body,'<declared 217-node charge auditor>','exec'),g);return g['evaluate']
def currents(x,q25,driver,reset,on):
 vt=D(1.380649e-23*298.15/1.602176634e-19);nvt=D(1.5*1.380649e-23*298.15/1.602176634e-19);si=lambda a,b:D(1e-12)*(((a-b)/nvt).exp()-1)
 attack=(x[205]-x[208])/D(10000);decay=(x[205]-x[211])/D(100000);follower=(x[205]-x[200])/D(10000);fast=D(0) if on else si(x[205],x[216]);ib=D(1e-14)*(((D(q25)-x[209])/vt).exp()-1)/D(100)+D(1e-14)*(((D(q25)-D(9.3))/vt).exp()-1)/D(5);q25i=(D(q25)-x[206])/D(3300)+ib;driveri=(D(driver)-x[216])/D(1500)-si(x[214],D(driver));reseti=-D(1e-8)*(((x[204]-D(reset))/nvt).exp()-1);return [attack,decay,follower,fast,q25i,driveri,reseti]
def ledger(before,after,integrals,ticks):
 seconds=D(ticks)*D(TICK);gate=D(1e-12)*seconds;caps=[]
 for name,c,a,b,k in [('C2',10e-6,205,None,0),('C18',100e-12,195,None,1),('C27',10e-6,139,12,2)]:
  delta=D(c)*(after[a]-before[a]-(after[b]-before[b] if b is not None else 0));error=abs(delta+D(integrals[k]));require(error<=gate,'charge ledger '+name);caps.append(dict(capacitor=name,charge_change_c=str(delta),native_dc_integral_c=integrals[k],error_c=str(error),gate_c=str(gate)))
 decomposition=abs(D(integrals[0])-sum(D(v) for v in integrals[6:]));require(decomposition<=gate,'C2 branch quadrature');return dict(capacitors=caps,duration_s=str(seconds),c2_branch_integrals_c=dict(zip(['attack','decay','follower','fast'],integrals[6:])),c2_decomposition_error_c=str(decomposition),source_integrals_c=dict(zip(['q25_collector','reset_driver','reset_base'],integrals[3:6])),not_independent_all_stage_quadrature=True)
def profile(p,inp):
 on,half=p['final_decay'],p['half_ticks'];directory=Path(p['command'][2]);lines=(directory/'selected.txt').read_text(encoding='utf8').splitlines();require(lines[0]==f'PROFILE,{int(on)},{half}','profile identity');initial,v=state(lines[1]);seed=next(s for s in inp['seeds'] if s['final_decay']==on and s['half_ticks']==half);seedcp=checkpoint((ROOT/seed['path']).read_bytes());require(packed(v)==packed(seedcp['values']),'own 434-coordinate seed');oldcp=__import__('check_loudness_control').checkpoint((ROOT/seed['origin_path']).read_bytes());require(struct.pack('<410d',*v[:205],*v[217:422])==struct.pack('<410d',*oldcp['values']),'all inherited205 coordinates by bits');require(v[205]==3.2 and v[422]==0.,'new C2 initial charge hypothesis')
 raw=(directory/'checkpoints.bin').read_bytes();require(len(raw)==11*3528,'complete checkpoints');points=[checkpoint(raw[k:k+3528]) for k in range(0,len(raw),3528)];require(points[0]['raw_sha256']==seed['sha256'],'initial checkpoint bytes');phases=[];roots=[];ports=[];last=initial;last_raw=v;i=2
 for phase,(q25,driver,reset) in enumerate(SOURCES):
  row=lines[i].split(',');require(row[0]=='BOUNDARY' and int(row[1])==phase and int(row[2])==START+phase*SPAN and list(map(float,row[3:]))==[q25,driver,reset],'boundary recipe');before,br=state(lines[i+1]);require(packed(br)==packed(last_raw),'source boundary preserves434 components');i+=2;checks=[];obs=[];endpoint=None
  while not lines[i].startswith('LEDGER,'):
   if lines[i].startswith('JOINT_ROOT,'):
    _,mask,h,res,corr=lines[i].split(',');states=[state(line)[0] for line in lines[i+1:i+6]];require(float(h)==half*TICK,'fixed step time');checks.append(scoped(q25,driver,reset,on)((int(mask),float(h),*states)));endpoint=states[-1];i+=6
   else:
    row=lines[i].split(',');require(row[0]=='OBS','endpoint');ob=list(map(float,row[1:]));require(int(ob[1])==phase and len(ob)==12,'endpoint codec');obs.append(ob);k=len(obs)-1
    if k in [0,SPAN//half-1]:
     require(endpoint is not None,'selected endpoint');expected=currents(endpoint,q25,driver,reset,on);errors=[abs(float(a)-b) for a,b in zip(expected,ob[5:])];require(max(errors)<=1e-9 and [float(endpoint[j]) for j in [205,203,194]]==ob[2:5],'actual native currents/voltages');ports.append(dict(phase=phase,step=k,port_errors_a=errors))
    i+=1
  require(len(obs)==SPAN//half and len(checks)==2 and [int(o[0]) for o in obs]==[START+phase*SPAN+(k+1)*half for k in range(SPAN//half)],'complete observed clocks');row=lines[i].split(',');require(row[0]=='LEDGER' and int(row[1])==phase and int(row[2])==START+(phase+1)*SPAN and len(row)==13,'ledger codec');integrals=list(map(float,row[3:]));after,ar=state(lines[i+1]);balance=ledger(before,after,integrals,SPAN);i+=2;a,b=points[1+2*phase:3+2*phase];require(a['phase']==b['phase']==phase and a['ticks']==START+phase*SPAN and b['ticks']==START+(phase+1)*SPAN and packed(a['values'])==packed(br) and packed(b['values'])==packed(ar),'checkpoint boundaries')
  for suffix,k in [('start',0),('middle',SPAN//half//2)]:
   cp=checkpoint((directory/f'phase{phase}-{suffix}.ckp').read_bytes());require(cp['phase']==phase and cp['ticks']==START+phase*SPAN+k*half,'restore positions')
   if k==0:require(cp==a,'restore source boundary by bytes')
  phases.append(dict(phase=phase,sources=[q25,driver,reset],end_ticks=b['ticks'],steps=len(obs),final_high_low=ar,final_c2_v=obs[-1][2],final_loudness_v=obs[-1][3],final_j7_v=obs[-1][4],final_currents_a=dict(zip(['attack','decay','follower','fast','q25_collector','reset_driver','reset_base'],obs[-1][5:])),native_integrals_c=integrals,ledger=balance));roots.extend(checks);last,last_raw=after,ar
 row=lines[i].split(',');require(row[0]=='TOTAL' and len(row)==11 and i+2==len(lines),'total completeness');total=list(map(float,row[1:]));final,fr=state(lines[i+1]);require(packed(fr)==packed(last_raw),'final state');full=ledger(initial,final,total,5*SPAN);require(checkpoint((directory/'final.ckp').read_bytes())==points[-1],'final checkpoint')
 for k in range(10):require(abs(sum(D(p['native_integrals_c'][k]) for p in phases)-D(total[k]))<=D(1e-18),'ledger composition')
 summary=re.search(r'COMPLETED,on=(\d+),half=(\d+),steps=(\d+),restores=(\d+),replay_steps=(\d+),corruptions=(\d+)',p['stderr']);require(summary is not None and tuple(map(int,summary.groups()))==(int(on),half,5*SPAN//half,10,15*SPAN//half//2,4),'phase replay coverage')
 return dict(final_decay=on,half_ticks=half,seed_high_low=v,phases=phases,total_ledger=full,root_checks=roots,port_checks=ports,steps=5*SPAN//half,restore_phase_replays=10,replayed_steps=15*SPAN//half//2,rejected_corruptions=4,input_sha256={f.relative_to(ROOT).as_posix():sha(f) for f in directory.iterdir() if f.is_file()})
def compare(a,b):
 x,y=lift(a),lift(b);ratio=max(float(abs(u-v)/D(2e-9 if 98<=k<133 else 2e-6)) for k,(u,v) in enumerate(zip(x,y)));require(ratio<=1,'217 same-clock refinement');return dict(gate_ratio=ratio,max_voltage_error_v=max(float(abs(x[k]-y[k])) for k in range(217) if not 98<=k<133))
def audit():
 native=json.loads((ROOT/'evidence/voice_c2_charge_native02.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_c2_charge_inputs02.json').read_text(encoding='utf8'));require(native['passed'] and len(native['profiles'])==4,'four complete profiles');profiles=[profile(p,inp) for p in native['profiles']];refinement=[];effects=[]
 for on in [True,False]:
  a,b=[next(p for p in profiles if p['final_decay']==on and p['half_ticks']==h) for h in [65536,32768]];refinement.append(dict(final_decay=on,ticks=START,**compare(a['seed_high_low'],b['seed_high_low'])));refinement.extend(dict(final_decay=on,ticks=START+(k+1)*SPAN,**compare(x['final_high_low'],y['final_high_low'])) for k,(x,y) in enumerate(zip(a['phases'],b['phases'])))
 for half in [65536,32768]:
  a,b=[next(p for p in profiles if p['final_decay']==on and p['half_ticks']==half) for on in [True,False]];effects.append(dict(half_ticks=half,fast_off_minus_on_c2_v=b['phases'][-1]['final_c2_v']-a['phases'][-1]['final_c2_v'],off_fast_branch_integral_c=b['total_ledger']['c2_branch_integrals_c']['fast'],on_fast_branch_integral_c=a['total_ledger']['c2_branch_integrals_c']['fast']))
 return dict(profiles=profiles,same_clock_refinement=refinement,final_decay_effects=effects,independent_candidates=80,independent_nonlinear_rows=17360,native_current_endpoint_vectors=40,native_current_values=280,new_steps=2400,restore_phase_replays=40,replayed_steps=3600,rejected_corruptions=16,inherited_bit_coordinates=410,source_boundary_bit_coordinates=434,dynamic_c2_admitted=True,full_contour_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args();names={'tools/check_c2_charge.py','evidence/voice_c2_charge_native02.json','evidence/voice_c2_charge_inputs02.json','docs/VOZ_C2_CARGA_PROTOCOLO.md'}
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=before);t=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(audit())
  require(time.perf_counter()-t<=300,'oracle budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_c2_charge.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};r['wall_s']=time.perf_counter()-t;require(before==r['source_sha256_after'],'unchanged oracle');write(f'evidence/voice_c2_charge_reference{args.attempt:02d}.json',r);print('C2_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
