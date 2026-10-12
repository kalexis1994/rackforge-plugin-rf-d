"""Own control continuations, binary checkpoint seam and independent 205-node equations."""
import argparse,json,math,re,struct,sys,time,traceback
from decimal import localcontext
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_loudness_control import START,SPAN,SOURCES
from check_joint_loudness import state,D,scoped
from joint_cycles_analysis import require,TICK
CODEC=struct.Struct('<8sQII2d410d')
def packed(v):return struct.pack('<410d',*v)
def checkpoint(raw):
 require(len(raw)==3320,'205 checkpoint size');row=CODEC.unpack(raw);magic,ticks,half,phase,c2,reset,*v=row;require(magic==b'RFLCTL01' and phase in range(5) and half in [65536,32768] and START+phase*SPAN<=ticks<=START+(phase+1)*SPAN and (ticks-START)%half==0,'checkpoint metadata');require(struct.pack('<2d',c2,reset)==struct.pack('<2d',*SOURCES[phase]),'checkpoint recipe');require(CODEC.pack(*row)==raw,'typed binary roundtrip')
 require(all(math.isfinite(x) for x in v),'finite checkpoint')
 for k in range(205):
  exact=D(v[k])+D(v[k+205]);hi=float(exact);lo=float(exact-D(hi));require(struct.pack('<2d',hi,lo)==struct.pack('<2d',v[k],v[k+205]),'normalized checkpoint pair')
 return dict(ticks=ticks,half=half,phase=phase,c2=c2,reset=reset,values=v,raw_sha256=__import__('hashlib').sha256(raw).hexdigest())
def lift(v):return [D(v[k])+D(v[k+205]) for k in range(205)]
def ledger(before,after,integrals,ticks):
 seconds=D(ticks)*D(TICK);gate=D(1e-12)*seconds;out=[]
 for name,c,a,b,k in [('C18',100e-12,195,None,0),('C27',10e-6,139,12,1)]:
  voltage=after[a]-before[a]-(after[b]-before[b] if b is not None else 0);delta=D(c)*voltage;error=abs(delta+D(integrals[k]));require(error<=gate,'charge ledger '+name);out.append(dict(capacitor=name,charge_change_c=str(delta),native_dc_integral_c=integrals[k],error_c=str(error),gate_c=str(gate)))
 return dict(duration_s=str(seconds),capacitors=out,native_c2_source_charge_c=integrals[2],native_reset_source_charge_c=integrals[3],source_integrals_are_not_c2_capacitor_charge=True,not_independent_all_stage_quadrature=True)
def profile(p,inp):
 half=p['half_ticks'];directory=ROOT/f'references-local/loudness-control01/{half}';lines=(directory/'selected.txt').read_text(encoding='utf8').splitlines();require(lines[0]==f'PROFILE,{half}','profile identity');initial,v=state(lines[1]);seed=next(s for s in inp['seeds'] if s['half_ticks']==half);seedcp=checkpoint((ROOT/seed['path']).read_bytes());require(packed(v)==packed(seedcp['values']),'own complete 410-coordinate seed');last=initial;last_raw=v;i=2;phases=[];roots=[];ports=[]
 raw=(directory/'checkpoints.bin').read_bytes();require(len(raw)==11*3320,'initial/five boundaries/five ends');points=[checkpoint(raw[j:j+3320]) for j in range(0,len(raw),3320)];require(points[0]['raw_sha256']==seed['sha256'],'initial checkpoint by bytes')
 for phase,(c2,reset) in enumerate(SOURCES):
  row=lines[i].split(',');require(row[0]=='BOUNDARY' and int(row[1])==phase and int(row[2])==START+phase*SPAN and list(map(float,row[3:]))==[c2,reset],'source boundary');boundary,br=state(lines[i+1]);require(packed(br)==packed(last_raw),'change preserves 410 components');i+=2;old=boundary;checks=[];obs=[];selected_endpoint=None
  while not lines[i].startswith('LEDGER,'):
   if lines[i].startswith('JOINT_ROOT,'):
    _,mask,h,res,corr=lines[i].split(',');values=[state(line)[0] for line in lines[i+1:i+6]];require(float(h)==half*TICK,'fixed step clock');checks.append(scoped(c2,reset)((int(mask),float(h),*values)));selected_endpoint=values[-1];i+=6
   else:
    row=lines[i].split(',');require(row[0]=='OBS' and int(row[2])==phase,'native endpoint record');ob=list(map(float,row[1:]));obs.append(ob);k=len(obs)-1
    if k in [0,SPAN//half-1]:
     x=selected_endpoint;require(x is not None,'selected native endpoint');nvt=1.5*1.380649e-23*298.15/1.602176634e-19;currents=[(D(c2)-x[200])/D(10000),-D(1e-8)*(((x[204]-D(reset))/D(nvt)).exp()-1),(x[203]-x[165])/D(68000)];errors=[abs(float(a)-b) for a,b in zip(currents,ob[4:])];require(max(errors)<=1e-9 and float(x[203])==ob[2] and float(x[194])==ob[3],'actual native ports/voltages');ports.append(dict(half_ticks=half,phase=phase,step=k,port_errors_a=errors))
    i+=1
  require(len(obs)==SPAN//half and len(checks)==2 and [int(o[0]) for o in obs]==[START+phase*SPAN+(k+1)*half for k in range(SPAN//half)],'complete endpoint clocks');row=lines[i].split(',');require(int(row[1])==phase and int(row[2])==START+(phase+1)*SPAN and len(row)==7,'phase ledger codec');integrals=list(map(float,row[3:]));after,ar=state(lines[i+1]);balance=ledger(old,after,integrals,SPAN);i+=2
  a,b=points[1+2*phase:3+2*phase];require(a['phase']==b['phase']==phase and a['ticks']==START+phase*SPAN and b['ticks']==START+(phase+1)*SPAN and packed(a['values'])==packed(br) and packed(b['values'])==packed(ar),'checkpoint/source boundary/end')
  for suffix,k in [('start',0),('middle',SPAN//half//2)]:
   cp=checkpoint((directory/f'phase{phase}-{suffix}.ckp').read_bytes());require(cp['phase']==phase and cp['ticks']==START+phase*SPAN+k*half,'restore position')
   if k==0:require(cp==a,'start restore matches boundary')
  phases.append(dict(phase=phase,c2_v=c2,reset_v=reset,start_ticks=a['ticks'],end_ticks=b['ticks'],steps=len(obs),source_change_bit_coordinates=410,final_high_low=ar,final_loudness_v=obs[-1][2],final_j7_v=obs[-1][3],final_c2_a=obs[-1][4],final_reset_a=obs[-1][5],final_r59_a=obs[-1][6],native_integrals_c=integrals,ledger=balance));roots.extend(checks);last,last_raw=after,ar
 row=lines[i].split(',');require(row[0]=='TOTAL' and len(row)==5 and i+2==len(lines),'total complete');total=list(map(float,row[1:]));final,fr=state(lines[i+1]);require(packed(fr)==packed(last_raw),'same final state');full=ledger(initial,final,total,5*SPAN);finalcp=checkpoint((directory/'final.ckp').read_bytes());require(finalcp==points[-1] and packed(finalcp['values'])==packed(fr),'final checkpoint exact')
 for k in range(4):require(abs(sum(D(phase['native_integrals_c'][k]) for phase in phases)-D(total[k]))<=D(1e-18),'phase/total ledger composition')
 summary=re.search(r'COMPLETED,half=(\d+),steps=(\d+),restores=(\d+),replay_steps=(\d+),corruptions=(\d+)',p['stderr']);require(summary is not None and tuple(map(int,summary.groups()))==(half,5*SPAN//half,10,15*SPAN//half//2,4),'native full phase replay coverage');private={p.relative_to(ROOT).as_posix():sha(p) for p in directory.iterdir() if p.is_file()}
 return dict(half_ticks=half,seed_high_low=v,phases=phases,total_ledger=full,root_checks=roots,port_checks=ports,steps=5*SPAN//half,restore_phase_replays=10,replayed_steps=15*SPAN//half//2,rejected_corruptions=4,input_sha256=private)
def compare(a,b):
 x,y=lift(a),lift(b);ratio=max(float(abs(u-v)/D(2e-9 if 98<=k<133 else 2e-6)) for k,(u,v) in enumerate(zip(x,y)));require(ratio<=1,'205 same-clock refinement');return dict(gate_ratio=ratio,max_voltage_error_v=max(float(abs(x[k]-y[k])) for k in range(205) if not 98<=k<133),max_current_error_a=max(float(abs(x[k]-y[k])) for k in range(98,133)))
def audit():
 native=json.loads((ROOT/'evidence/voice_loudness_control_native01.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_loudness_control_inputs01.json').read_text(encoding='utf8'));require(native['passed'] and len(native['profiles'])==2,'two complete profiles');profiles=[profile(p,inp) for p in native['profiles']];a,b=profiles;refinement=[dict(ticks=START,**compare(a['seed_high_low'],b['seed_high_low']))]+[dict(ticks=START+(k+1)*SPAN,**compare(x['final_high_low'],y['final_high_low'])) for k,(x,y) in enumerate(zip(a['phases'],b['phases']))]
 return dict(profiles=profiles,same_clock_refinement=refinement,independent_candidates=40,independent_nonlinear_rows=8200,native_port_endpoint_vectors=20,native_port_current_values=60,new_steps=240,restore_phase_replays=20,replayed_steps=360,rejected_corruptions=8,source_change_bit_coordinates=410,temporal_follower_controls_admitted=True,full_contour_admitted=False,adaptive_controller_admitted=False,new_audio=False,physical_fidelity=False,real_time=False)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args()
 names={'tools/check_loudness_control.py','evidence/voice_loudness_control_native01.json','evidence/voice_loudness_control_inputs01.json','docs/VOZ_SEGUIDOR_CONTROL_PROTOCOLO.md'}
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=before);t=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(audit())
  require(time.perf_counter()-t<=300,'reference budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_loudness_control.py').read_text(encoding='utf8')
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r['source_sha256_after']={n:sha(ROOT/n) for n in sorted(names)};r['wall_s']=time.perf_counter()-t;require(before==r['source_sha256_after'],'unchanged oracle');write(f'evidence/voice_loudness_control_reference{args.attempt:02d}.json',r);print('LOUDNESS_CONTROL_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
if __name__=='__main__':main()
