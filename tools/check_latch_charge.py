"""Full original graph/FD, Decimal100 nonlinear latch Q and native evidence."""
import argparse,copy,inspect,json,math,re,struct,sys,time,traceback
from decimal import localcontext
from functools import lru_cache
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_latch_charge import START,SPAN,KEY,SHORT,NEW
from latch_charge_reference import network,charges,D
from check_joint_loudness import problem as follower_problem
from check_trigger_charge import checkpoint as previous_checkpoint
import check_joint_reference as original
from joint_cycles_analysis import require,TICK
CODEC=struct.Struct('<8sQII2dII458d')
def packed(v):return struct.pack('<458d',*v)
def lift(v):return [D(v[k])+D(v[k+229]) for k in range(229)]
def state(line):
 v=list(map(float,line.split(',')[1:]));require(len(v)==458,'229 codec');return lift(v),v
def checkpoint(raw):
 require(len(raw)==3712,'229 checkpoint size');r=CODEC.unpack(raw);magic,ticks,half,phase,key,model,flags,reserved,*v=r;require(magic==b'RFLATCH1' and phase in range(5) and half in [8192,4096] and model==1. and flags in range(4) and reserved==0 and START+phase*SPAN<=ticks<=START+(phase+1)*SPAN and (ticks-START)%half==0,'checkpoint metadata');require(struct.pack('<d',key)==struct.pack('<d',KEY[phase]) and bool(flags&2)==SHORT[phase] and CODEC.pack(*r)==raw,'recipe/typed roundtrip');require(all(math.isfinite(x) for x in v),'finite state')
 for k in range(229):
  exact=D(v[k])+D(v[k+229]);h=float(exact);l=float(exact-D(h));require(struct.pack('<2d',h,l)==struct.pack('<2d',v[k],v[k+229]),'normalized pairs')
 return dict(ticks=ticks,half=half,phase=phase,key=key,short=bool(flags&2),final_decay=bool(flags&1),values=v,raw_sha256=__import__('hashlib').sha256(raw).hexdigest())
def ci(k):return original.ci(k) if k<68 else k+132
@lru_cache(None)
def problem(key,on,short,r61,mask,sources):
 core,_,y=follower_problem(0.,0.,r61,mask,sources);n=network(on,short);n.alias['EXTERNAL_S_TRIGGER']='GROUND'
 if on:n.resistors.append(('LHC_FAST_DECAY','FAST_DIODE_K','RESET_DRIVER',1500.))
 def dc(x):
  r=np.zeros(97);r[:68]=core(np.array([*x[:68],0.,0.,0.,0.,0.]))[:68];r[32]-=x[71]/68000.;n.rails['VCA_CONTROL_LOAD']=float(x[32]);r[68:]=n.evaluate(x[68:].tolist(),key,jacobian=False)[0];return r
 def gradient(x):
  j=np.empty((97,97))
  for k in range(97):
   a=x.copy();b=x.copy();a[k]+=1e-6;b[k]-=1e-6;j[:,k]=(dc(a)-dc(b))/2e-6
  return j
 return dc,gradient,y
EXTRA='''        nq,nm=charges(state);oq,_=charges(old)
        for a in range(200,229):cq[a-132]+=(nq[a]-oq[a])/D(h)
        for (a,b),v in nm.items():cm[a-132,b-132]+=float(v)/h
'''
def scoped(key,on,short):
 body=inspect.getsource(original.evaluate).replace('range(68)','range(97)').replace('Decimal(0)]*68','Decimal(0)]*97').replace('zeros((68,68))','zeros((97,97))');body=body.replace('        ff=[Decimal(0)]*N;',EXTRA+'        ff=[Decimal(0)]*N;');g=dict(original.__dict__,N=229,ci=ci,charges=charges,CAPS=[*original.CAPS,(73,None,1e-5),(89,None,1e-7),(91,93,1e-8)],problem=lambda r,m,s:problem(key,on,short,r,m,tuple(s)));exec(compile(body,'<declared229-node auditor>','exec'),g);return g['evaluate']
def currents(x,key,on,short):
 n=network(on,short);n.rails['VCA_CONTROL_LOAD']=float(x[165]);volts=dict(n.rails,KEYBOARD_TRIGGER=key);volts.update({name:float(x[200+k]) for k,name in enumerate(n.nodes)});ports={k:0. for k in n.rails}
 def row(k,i):
  if k in ports:ports[k]+=i
 for _,a,b,r in n.resistors:
  i=(volts[a]-volts[b])/r;row(a,i);row(b,-i)
 vt=1.380649e-23*298.15/1.602176634e-19
 for p in n.bjts:
  b,c,e=[p[k] for k in ['base','collector','emitter']];sign=1 if p['kind']=='NPN' else -1;f=1e-14*math.expm1(sign*(volts[b]-volts[e])/vt);r=1e-14*math.expm1(sign*(volts[b]-volts[c])/vt);ib=sign*(f/100+r/5);ic=sign*(f-1.2*r);row(b,ib);row(c,ic);row(e,-ib-ic)
 for p in n.diodes:
  a,b=p['anode'],p['cathode'];i=(1e-8 if p['marking']=='1N34A' else 1e-12)*math.expm1((volts[a]-volts[b])/(1.5*vt));row(a,i);row(b,-i)
 return [ports['KEYBOARD_TRIGGER'],ports['CONTOUR_SUPPLY'],float((x[203]-x[165])/D(68000))]
def ledger(before,after,v,ticks):
 gate=D(1e-12)*D(ticks)*D(TICK);q0,_=charges(before);q1,_=charges(after);d4=D(1e-8)*(after[223]-before[223]-after[225]+before[225]);changes=[D(1e-5)*(after[205]-before[205]),D(1e-10)*(after[195]-before[195]),D(1e-5)*(after[139]-before[139]-after[12]+before[12]),D(1e-7)*(after[221]-before[221]),d4,q1[225]-q0[225]-d4,*[q1[k]-q0[k] for k in [226,227,228]]];out=[]
 for name,q,i in zip(['C2','C18','C27','C7','C4_LEFT','Q25_B_plus_C4_return','Q25_C','Q15_B','Q15_C'],changes,v):
  error=abs(q+D(i));require(error<=gate,'charge ledger '+name);out.append(dict(row=name,charge_change_c=str(q),native_dc_integral_c=i,error_c=str(error),gate_c=str(gate)))
 return dict(rows=out,not_independent_all_stage_quadrature=True)
def profile(p,inp):
 on,half=p['final_decay'],p['half_ticks'];directory=Path(p['command'][2]);lines=(directory/'selected.txt').read_text(encoding='utf8').splitlines();require(lines[0]==f'PROFILE,{int(on)},{half}','profile');initial,v=state(lines[1]);seed=next(s for s in inp['seeds'] if s['final_decay']==on and s['half_ticks']==half);seedcp=checkpoint((ROOT/seed['path']).read_bytes());require(packed(v)==packed(seedcp['values']),'own458-coordinate seed');old=previous_checkpoint((ROOT/seed['origin_path']).read_bytes());require(struct.pack('<450d',*v[:225],*v[229:454])==struct.pack('<450d',*old['values']),'inherited225 by bits');require(v[225:229]==NEW and v[454:]==[0.]*4,'new bias');require(initial[223]-initial[225]==D(old['values'][223])+D(old['values'][448])-D(.01),'inherited C4 oriented history');raw=(directory/'checkpoints.bin').read_bytes();require(len(raw)==11*3712,'checkpoint records');points=[checkpoint(raw[k:k+3712]) for k in range(0,len(raw),3712)];require(points[0]['raw_sha256']==seed['sha256'],'initial checkpoint');last_raw=v;i=2;phases=[];roots=[];ports=[]
 for phase,(key,short) in enumerate(zip(KEY,SHORT)):
  row=lines[i].split(',');require(row[0]=='BOUNDARY' and int(row[1])==phase and int(row[2])==START+phase*SPAN and float(row[3])==key and int(row[4])==int(short),'boundary recipe');before,br=state(lines[i+1]);require(packed(br)==packed(last_raw),'boundary preserves458');i+=2;checks=[];obs=[];states=None;h=None
  while not lines[i].startswith('LEDGER,'):
   if lines[i].startswith('JOINT_ROOT,'):
    _,mask,h,res,corr=lines[i].split(',');h=float(h);states=[state(line)[0] for line in lines[i+1:i+6]];require(h==half*TICK,'step clock');checks.append(scoped(key,on,short)((int(mask),h,*states)));i+=6
   else:
    row=lines[i].split(',');require(row[0]=='OBS','endpoint');ob=list(map(float,row[1:]));require(len(ob)==15 and int(ob[1])==phase,'endpoint codec');obs.append(ob);k=len(obs)-1
    if k in [0,SPAN//half-1]:
     require(states is not None,'selected endpoint');x=states[-1];expected=currents(x,key,on,short);errors=[abs(a-b) for a,b in zip(expected,ob[12:])];values=[float(x[k]) for k in [205,203,194,221,217]]+[float(x[223])-float(x[225])]+[float(x[k]) for k in range(225,229)];require(max(errors)<=1e-9 and values==ob[2:12],'native currents/voltage');ports.append(dict(phase=phase,step=k,current_errors_a=errors))
    i+=1
  require(len(obs)==SPAN//half and len(checks)==2 and [int(x[0]) for x in obs]==[START+phase*SPAN+(k+1)*half for k in range(SPAN//half)],'complete endpoint clocks');row=lines[i].split(',');require(len(row)==12 and int(row[1])==phase and int(row[2])==START+(phase+1)*SPAN,'ledger codec');integrals=list(map(float,row[3:]));after,ar=state(lines[i+1]);balance=ledger(before,after,integrals,SPAN);i+=2;a,b=points[1+2*phase:3+2*phase];require(a['phase']==b['phase']==phase and packed(a['values'])==packed(br) and packed(b['values'])==packed(ar),'checkpoint boundaries')
  for suffix,k in [('start',0),('middle',SPAN//half//2)]:
   cp=checkpoint((directory/f'phase{phase}-{suffix}.ckp').read_bytes());require(cp['phase']==phase and cp['ticks']==START+phase*SPAN+k*half,'restore positions')
   if k==0:require(cp==a,'start restore matches boundary')
  phases.append(dict(phase=phase,key=key,short=short,end_ticks=b['ticks'],steps=len(obs),final_high_low=ar,final_voltages_v=dict(zip(['C2','LOUDNESS','J7','C7','RESET_DRIVER','C4','Q25_B','Q25_C','Q15_B','Q15_C'],obs[-1][2:12])),final_currents_a=dict(zip(['KEY','SUPPLY','R59'],obs[-1][12:])),native_integrals_c=integrals,ledger=balance));last_raw=ar;roots.extend(checks)
 row=lines[i].split(',');require(row[0]=='TOTAL' and len(row)==10 and i+2==len(lines),'total completeness');total=list(map(float,row[1:]));final,fr=state(lines[i+1]);require(packed(fr)==packed(last_raw) and checkpoint((directory/'final.ckp').read_bytes())==points[-1],'final identity');full=ledger(initial,final,total,5*SPAN)
 for k in range(9):require(abs(sum(D(x['native_integrals_c'][k]) for x in phases)-D(total[k]))<=D(1e-18),'phase/total composition')
 summary=re.search(r'COMPLETED,on=(\d+),half=(\d+),steps=(\d+),restores=(\d+),replay_steps=(\d+),corruptions=(\d+)',p['stderr']);require(summary is not None and tuple(map(int,summary.groups()))==(int(on),half,5*SPAN//half,10,15*SPAN//half//2,4),'native replay coverage');return dict(final_decay=on,half_ticks=half,seed_high_low=v,phases=phases,total_ledger=full,root_checks=roots,port_checks=ports,input_sha256={f.relative_to(ROOT).as_posix():sha(f) for f in directory.iterdir() if f.is_file()})
def compare(a,b):
 x,y=lift(a),lift(b);ratio=max(float(abs(u-v)/D(2e-9 if 98<=k<133 else 2e-6)) for k,(u,v) in enumerate(zip(x,y)));require(ratio<=1,'229 refinement');return dict(gate_ratio=ratio,max_voltage_error_v=max(float(abs(x[k]-y[k])) for k in range(229) if not 98<=k<133))
def audit():
 native=json.loads((ROOT/'evidence/voice_latch_charge_native04.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_latch_charge_inputs04.json').read_text(encoding='utf8'));require(native['passed'] and len(native['profiles'])==4,'four profiles');profiles=[profile(p,inp) for p in native['profiles']];refinement=[]
 for on in [True,False]:
  a,b=[next(p for p in profiles if p['final_decay']==on and p['half_ticks']==h) for h in [8192,4096]];refinement.append(dict(final_decay=on,ticks=START,**compare(a['seed_high_low'],b['seed_high_low'])));refinement.extend(dict(final_decay=on,ticks=START+(k+1)*SPAN,**compare(x['final_high_low'],y['final_high_low'])) for k,(x,y) in enumerate(zip(a['phases'],b['phases'])))
 for on in [1,0]:
  for name in ['selected.txt','checkpoints.bin']:
   a=ROOT/f'references-local/latch-charge03/{on}-8192'/name;b=ROOT/f'references-local/latch-charge04/{on}-8192'/name;require(b.read_bytes()==a.read_bytes(),'same complete finer history by bytes')
 return dict(profiles=profiles,same_clock_refinement=refinement,independent_candidates=80,independent_nonlinear_rows=18320,native_current_endpoint_vectors=40,native_current_values=120,new_steps=3840,restore_phase_replays=40,replayed_steps=5760,rejected_corruptions=16,inherited_bit_coordinates=450,source_boundary_bit_coordinates=458,board2_local_closure_admitted=True,old_nominal_prefix_bit_equal=True,full_contour_trajectory_admitted=False,all_board2_junction_charge_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args();names={'tools/check_latch_charge.py','evidence/voice_latch_charge_native04.json','evidence/voice_latch_charge_inputs04.json','docs/VOZ_BIESTABLE_CARGADO_PROTOCOLO.md','docs/VOZ_BIESTABLE_SEMILLA_PROTOCOLO.md','docs/VOZ_BIESTABLE_CONTACTO_PROTOCOLO.md'}
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
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_latch_charge.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};r['wall_s']=time.perf_counter()-t;require(before==r['source_sha256_after'],'stable oracle');write(f'evidence/voice_latch_charge_reference{args.attempt:02d}.json',r);print('LATCH_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
