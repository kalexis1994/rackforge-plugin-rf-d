"""Full original graph/FD, Decimal100 nonlinear latch Q and native evidence."""
import argparse,copy,inspect,json,math,re,struct,sys,time,traceback
from decimal import localcontext
from functools import lru_cache
from pathlib import Path
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from prepare_latch_charge import START,SPAN,KEY,SHORT,NEW
from latch_charge_reference import network as nominal_network,charges,D
from check_joint_loudness import problem as follower_problem
from check_trigger_charge import checkpoint as previous_checkpoint
import check_joint_reference as original
from joint_cycles_analysis import require,TICK
from prepare_decay_control import DECAY
def network(on,short):
 n=nominal_network(on,short);require(sum(r[0]=='PANEL_R16' for r in n.resistors)==1,'one documentary panel decay branch');n.resistors=[(ref,a,b,DECAY if ref=='PANEL_R16' else ohm) for ref,a,b,ohm in n.resistors];return n
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
