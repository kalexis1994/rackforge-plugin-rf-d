"""225-node graph/FD/Decimal reference, loaded driver and explicit C4 source current."""
import argparse,inspect,json,math,re,struct,sys,time,traceback
from decimal import localcontext
from functools import lru_cache
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_trigger_charge import START,SPAN,SOURCES,SHORT
from trigger_charge_reference import network as trigger_network
from c2_charge_reference import network as charge_network
from check_joint_loudness import problem as follower_problem,D
import check_joint_reference as original
from check_c2_charge import checkpoint as previous_checkpoint,currents as charge_currents
from joint_cycles_analysis import require,TICK
CODEC=struct.Struct('<8sQII4dII450d')
def packed(v):return struct.pack('<450d',*v)
def lift(v):return [D(v[k])+D(v[k+225]) for k in range(225)]
def state(line):
 v=list(map(float,line.split(',')[1:]));require(len(v)==450,'225 high/low codec');return lift(v),v
def checkpoint(raw):
 require(len(raw)==3664,'225 checkpoint size');r=CODEC.unpack(raw);magic,ticks,half,phase,q25,key,reset,set_base,flags,reserved,*v=r;require(magic==b'RFLTRG01' and phase in range(5) and half in [65536,32768] and flags in range(4) and reserved==0 and START+phase*SPAN<=ticks<=START+(phase+1)*SPAN and (ticks-START)%half==0,'checkpoint metadata');require(struct.pack('<3d',q25,key,reset)==struct.pack('<3d',*SOURCES[phase]) and set_base==.01 and bool(flags&2)==SHORT[phase] and CODEC.pack(*r)==raw,'recipe/typed roundtrip');require(all(math.isfinite(x) for x in v),'finite state')
 for k in range(225):
  exact=D(v[k])+D(v[k+225]);h=float(exact);l=float(exact-D(h));require(struct.pack('<2d',h,l)==struct.pack('<2d',v[k],v[k+225]),'normalized pairs')
 return dict(ticks=ticks,half=half,phase=phase,sources=[q25,key,reset],set_base=set_base,short=bool(flags&2),final_decay=bool(flags&1),values=v,raw_sha256=__import__('hashlib').sha256(raw).hexdigest())
def ci(k):return original.ci(k) if k<68 else k+132
@lru_cache(None)
def problem(q25,key,reset,on,short,r61,mask,sources):
 core,_,y=follower_problem(0.,reset,r61,mask,sources);driver=charge_network(q25,0.,on);trigger=trigger_network(reset,short)
 def dc(x):
  r=np.zeros(93);r[:73]=core(x[:73]);r[68]-=x[73]/10000.;driver.rails['RESET_DRIVER']=float(x[85]);r[73:85]=driver.evaluate(x[73:85].tolist(),0.,jacobian=False)[0];r[73]+=(x[73]-x[68])/10000.;r[85:]=trigger.evaluate(x[85:].tolist(),key,jacobian=False)[0];scale=1.5*1.380649e-23*298.15/1.602176634e-19;r[85]+=(x[85]-x[84])/1500.-1e-12*math.expm1((x[82]-x[85])/scale);return r
 def gradient(x):
  j=np.empty((93,93))
  for k in range(93):
   a=x.copy();b=x.copy();a[k]+=1e-6;b[k]-=1e-6;j[:,k]=(dc(a)-dc(b))/2e-6
  return j
 return dc,gradient,y
def scoped(q25,key,reset,on,short):
 body=inspect.getsource(original.evaluate).replace('range(68)','range(93)').replace('Decimal(0)]*68','Decimal(0)]*93').replace('zeros((68,68))','zeros((93,93))');g=dict(original.__dict__,N=225,ci=ci,CAPS=[*original.CAPS,(73,None,10e-6),(89,None,1e-7),(91,None,1e-8)],problem=lambda r,m,s:problem(q25,key,reset,on,short,r,m,tuple(s)));exec(compile(body,'<declared225-node auditor>','exec'),g);return g['evaluate']
def currents(x,q25,key,reset,on,states,h):
 vt=D(1.380649e-23*298.15/1.602176634e-19);scale=D(1.5*1.380649e-23*298.15/1.602176634e-19);germ=lambda a,b:D(1e-8)*(((a-b)/scale).exp()-1)
 old=charge_currents(x,q25,float(x[217]),reset,on);driver=(x[217]-x[216])/D(1500)-D(1e-12)*(((x[214]-x[217])/scale).exp()-1);reset_total=old[-1]-germ(x[224],D(reset));keyboard=germ(D(key),x[222]);c4=-D(1e-8)/D(h)*(D(-4.5)*states[1][223]+D(2.5)*states[2][223])
 def bjt(sign,b,c,e):
  f=D(1e-14)*((D(sign)*(b-e)/vt).exp()-1);r=D(1e-14)*((D(sign)*(b-c)/vt).exp()-1);ib=D(sign)*(f/D(100)+r/D(5));ic=D(sign)*(f-D(1.2)*r);return ib,ic,-ib-ic
 supply=(D(9.3)-x[206])/D(560)+(D(9.3)-x[214])/D(27000)+bjt(-1,x[206],x[207],D(9.3))[2]+bjt(1,D(q25),D(9.3),x[209])[1]+(D(9.3)-x[202])/D(560)+(D(9.3)-x[217])/D(3300)+(D(9.3)-x[218])/D(3300)
 return [*old[:5],driver,reset_total,keyboard,c4,supply]
def ledger(before,after,v,ticks):
 seconds=D(ticks)*D(TICK);gate=D(1e-12)*seconds;caps=[]
 for name,c,a,b,k in [('C2',10e-6,205,None,0),('C18',100e-12,195,None,1),('C27',10e-6,139,12,2),('C7',1e-7,221,None,10),('C4',1e-8,223,None,11)]:
  delta=D(c)*(after[a]-before[a]-(after[b]-before[b] if b is not None else 0));error=abs(delta+D(v[k]));require(error<=gate,'charge ledger '+name);caps.append(dict(capacitor=name,charge_change_c=str(delta),native_dc_integral_c=v[k],error_c=str(error),gate_c=str(gate),fixed_set_base_cancels=name=='C4'))
 decomposition=abs(D(v[0])-sum(D(x) for x in v[6:10]));set_identity=abs(D(v[11])-D(v[13]));require(max(decomposition,set_identity)<=gate,'C2 decomposition/C4 source identity');return dict(capacitors=caps,duration_s=str(seconds),c2_branch_integrals_c=dict(zip(['attack','decay','follower','fast'],v[6:10])),interface_integrals_c=dict(zip(['q25','internal_reset_driver','reset_base'],v[3:6])),keyboard_integral_c=v[12],set_base_integral_c=v[13],supply_integral_c=v[14],c2_decomposition_error_c=str(decomposition),c4_source_identity_error_c=str(set_identity),not_independent_all_stage_quadrature=True)
def profile(p,inp):
 on,half=p['final_decay'],p['half_ticks'];directory=Path(p['command'][2]);lines=(directory/'selected.txt').read_text(encoding='utf8').splitlines();require(lines[0]==f'PROFILE,{int(on)},{half}','profile');initial,v=state(lines[1]);seed=next(s for s in inp['seeds'] if s['final_decay']==on and s['half_ticks']==half);seedcp=checkpoint((ROOT/seed['path']).read_bytes());require(packed(v)==packed(seedcp['values']),'own450-coordinate seed');old=previous_checkpoint((ROOT/seed['origin_path']).read_bytes());require(struct.pack('<434d',*v[:217],*v[225:442])==struct.pack('<434d',*old['values']),'inherited217 by bits');require(v[221]==0 and v[446]==0 and v[223]-.01==seed['new_c4_initial_v'],'new C7/C4 conditions');raw=(directory/'checkpoints.bin').read_bytes();require(len(raw)==11*3664,'all checkpoint records');points=[checkpoint(raw[k:k+3664]) for k in range(0,len(raw),3664)];require(points[0]['raw_sha256']==seed['sha256'],'initial checkpoint');last_raw=v;i=2;phases=[];roots=[];ports=[]
 for phase,(q25,key,reset) in enumerate(SOURCES):
  row=lines[i].split(',');require(row[0]=='BOUNDARY' and int(row[1])==phase and int(row[2])==START+phase*SPAN and list(map(float,row[3:6]))==[q25,key,reset] and int(row[6])==int(SHORT[phase]),'boundary recipe');before,br=state(lines[i+1]);require(packed(br)==packed(last_raw),'boundary preserves450');i+=2;checks=[];obs=[];states=None;h=None
  while not lines[i].startswith('LEDGER,'):
   if lines[i].startswith('JOINT_ROOT,'):
    _,mask,h,res,corr=lines[i].split(',');h=float(h);states=[state(line)[0] for line in lines[i+1:i+6]];require(h==half*TICK,'step clock');checks.append(scoped(q25,key,reset,on,SHORT[phase])((int(mask),h,*states)));i+=6
   else:
    row=lines[i].split(',');require(row[0]=='OBS','endpoint');ob=list(map(float,row[1:]));require(len(ob)==18 and int(ob[1])==phase,'endpoint codec');obs.append(ob);k=len(obs)-1
    if k in [0,SPAN//half-1]:
     require(states is not None,'selected endpoint');x=states[-1];expected=currents(x,q25,key,reset,on,states,h);errors=[abs(float(a)-b) for a,b in zip(expected,ob[5:15])];require(max(errors)<=1e-9 and [float(x[j]) for j in [205,203,194]]==ob[2:5] and [float(x[221]),float(x[217]),float(x[223])-float(D(.01))]==ob[15:18],'actual native currents/voltages');ports.append(dict(phase=phase,step=k,current_errors_a=errors))
    i+=1
  require(len(obs)==SPAN//half and len(checks)==2 and [int(x[0]) for x in obs]==[START+phase*SPAN+(k+1)*half for k in range(SPAN//half)],'complete endpoint clocks');row=lines[i].split(',');require(row[0]=='LEDGER' and len(row)==18 and int(row[1])==phase and int(row[2])==START+(phase+1)*SPAN,'ledger codec');integrals=list(map(float,row[3:]));after,ar=state(lines[i+1]);balance=ledger(before,after,integrals,SPAN);i+=2;a,b=points[1+2*phase:3+2*phase];require(a['phase']==b['phase']==phase and packed(a['values'])==packed(br) and packed(b['values'])==packed(ar),'checkpoint boundaries')
  for suffix,k in [('start',0),('middle',SPAN//half//2)]:
   cp=checkpoint((directory/f'phase{phase}-{suffix}.ckp').read_bytes());require(cp['phase']==phase and cp['ticks']==START+phase*SPAN+k*half,'restore positions')
   if k==0:require(cp==a,'start restore matches boundary')
  phases.append(dict(phase=phase,sources=[q25,key,reset],short=SHORT[phase],end_ticks=b['ticks'],steps=len(obs),final_high_low=ar,final_c2_v=obs[-1][2],final_loudness_v=obs[-1][3],final_j7_v=obs[-1][4],final_c7_v=obs[-1][15],final_reset_driver_v=obs[-1][16],final_c4_v=obs[-1][17],final_currents_a=dict(zip(['attack','decay','follower','fast','q25','internal_driver','reset_base','keyboard','set_base','supply'],obs[-1][5:15])),native_integrals_c=integrals,ledger=balance));last_raw=ar;roots.extend(checks)
 row=lines[i].split(',');require(row[0]=='TOTAL' and len(row)==16 and i+2==len(lines),'total completeness');total=list(map(float,row[1:]));final,fr=state(lines[i+1]);require(packed(fr)==packed(last_raw) and checkpoint((directory/'final.ckp').read_bytes())==points[-1],'final identity');full=ledger(initial,final,total,5*SPAN)
 for k in range(15):require(abs(sum(D(x['native_integrals_c'][k]) for x in phases)-D(total[k]))<=D(1e-18),'phase/total composition')
 summary=re.search(r'COMPLETED,on=(\d+),half=(\d+),steps=(\d+),restores=(\d+),replay_steps=(\d+),corruptions=(\d+)',p['stderr']);require(summary is not None and tuple(map(int,summary.groups()))==(int(on),half,5*SPAN//half,10,15*SPAN//half//2,4),'native replay coverage');return dict(final_decay=on,half_ticks=half,seed_high_low=v,phases=phases,total_ledger=full,root_checks=roots,port_checks=ports,input_sha256={f.relative_to(ROOT).as_posix():sha(f) for f in directory.iterdir() if f.is_file()})
def compare(a,b):
 x,y=lift(a),lift(b);ratio=max(float(abs(u-v)/D(2e-9 if 98<=k<133 else 2e-6)) for k,(u,v) in enumerate(zip(x,y)));require(ratio<=1,'225 refinement');return dict(gate_ratio=ratio,max_voltage_error_v=max(float(abs(x[k]-y[k])) for k in range(225) if not 98<=k<133))
def audit():
 native=json.loads((ROOT/'evidence/voice_trigger_charge_native02.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_trigger_charge_inputs02.json').read_text(encoding='utf8'));require(native['passed'] and len(native['profiles'])==4,'four profiles');profiles=[profile(p,inp) for p in native['profiles']];refinement=[]
 for on in [True,False]:
  a,b=[next(p for p in profiles if p['final_decay']==on and p['half_ticks']==h) for h in [65536,32768]];refinement.append(dict(final_decay=on,ticks=START,**compare(a['seed_high_low'],b['seed_high_low'])));refinement.extend(dict(final_decay=on,ticks=START+(k+1)*SPAN,**compare(x['final_high_low'],y['final_high_low'])) for k,(x,y) in enumerate(zip(a['phases'],b['phases'])))
 for name in ['selected.txt','checkpoints.bin']:
  a=ROOT/'references-local/trigger-charge01/1-65536'/name;b=ROOT/'references-local/trigger-charge02/1-65536'/name;require(b.read_bytes().startswith(a.read_bytes()),'unchanged nominal prefix by bytes')
 return dict(profiles=profiles,same_clock_refinement=refinement,independent_candidates=80,independent_nonlinear_rows=18000,native_current_endpoint_vectors=40,native_current_values=400,new_steps=480,restore_phase_replays=40,replayed_steps=720,rejected_corruptions=16,inherited_bit_coordinates=434,source_boundary_bit_coordinates=450,loaded_trigger_admitted=True,old_nominal_prefix_bit_equal=True,full_contour_admitted=False,causal_latch_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args();names={'tools/check_trigger_charge.py','evidence/voice_trigger_charge_native02.json','evidence/voice_trigger_charge_inputs02.json','docs/VOZ_GATILLO_CARGADO_PROTOCOLO.md','docs/VOZ_GATILLO_SEMILLA_PROTOCOLO.md'}
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
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_trigger_charge.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};r['wall_s']=time.perf_counter()-t;require(before==r['source_sha256_after'],'stable oracle');write(f'evidence/voice_trigger_charge_reference{args.attempt:02d}.json',r);print('TRIGGER_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
