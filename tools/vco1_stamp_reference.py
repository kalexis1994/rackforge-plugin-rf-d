"""Full VCO1 Decimal100 incidence and fresh original ngspice snapshots."""
import argparse,json,math,subprocess,time,shutil
from decimal import Decimal,localcontext
from pathlib import Path
from vco1_native_inventory import inventory,rust_data
from vco1_circuit_reference import ROOT,Scenario,netlist,EXPECTED_EXE_SHA
import lm741_reference as op
import vco_bjt_vectors as bjt
import vco_jfet_vectors as jfet
sha=op.sha;N=134;NV=98;D=Decimal.from_float
EXE=op.EXE;BASE='d0c5b04c7d5f6ee6e4300cf9f15975db2da38a41'
SOURCES=['tools/vco1_stamp_reference.py','tools/vco1_native_inventory.py','tools/vco1_circuit_reference.py','tools/vco_bjt_vectors.py','tools/vco_jfet_vectors.py','tools/lm741_reference.py','crates/rf-d-circuit/src/vco1_stamp.rs','crates/rf-d-circuit/src/vco1_stamp_data.rs','docs/VCO1_STAMP_PROTOCOLO.md','evidence/vco1_ramp_graph.json','evidence/vco1_ca3046_parts.json','evidence/vco1_panel_pulse_width.json','evidence/vco1_laboratory_devices.json','crates/rf-d-circuit/src/lm741.rs','crates/rf-d-circuit/src/vco_bjt.rs','crates/rf-d-circuit/src/vco_jfet.rs','crates/rf-d-circuit/src/junction_charge.rs']
GATES=dict(residual_kcl_abs=2e-11,residual_constraint_abs=2e-10,residual_relative=3e-11,jac_abs=2e-10,jac_relative=3e-11,conservation_a=1e-11,fd_abs=2e-6,fd_relative=2e-5,dc_kcl_a=1e-11,dc_constraint_v=1e-11)

def config(s):return [s.r8_fraction,s.r11_active_ohm,s.c4_f,s.imposed_mixer_v,s.external_neg4_load_a,s.other_control_v,s.other_control_v,s.keyboard_v,s.other_control_v,s.other_control_v,s.other_control_v]
def scenario(c):return Scenario(r8_fraction=c[0],r11_active_ohm=c[1],c4_f=c[2],imposed_mixer_v=c[3],external_neg4_load_a=c[4],other_control_v=c[5],keyboard_v=c[7])
def reference(x,previous,dt,c):
 inv=inventory(scenario(c));names=inv['names'];ix=lambda n:N if n=='0' else inv['nodes'].index(n)
 z=list(map(D,x));zero=Decimal(0);one=Decimal(1);r=[zero]*N;j=[[zero]*N for _ in range(N)];ground=zero
 def add(row,i):
  nonlocal ground
  if row==N:ground+=i
  else:r[row]+=i
 def derivative(row,col,g):
  if row!=N and col!=N:j[row][col]+=g
 def branch(a,b,i,grad):
  for row,sign in ((a,1),(b,-1)):
   add(row,sign*i)
   for col,g in grad:derivative(row,col,sign*g)
 def val(n):return zero if n==N else z[n]
 trims=['RR8_HIGH','RR8_LOW','RR11_ACTIVE'];vs=0
 for w in inv['lines']:
  k=w[0][0]
  if w[0] in ('VR8_HIGH','VR8_LOW','VR11_ACTIVE'):w=['R'+w[0][1:],*w[1:]];k='R'
  if k in 'RCVI':
   a,b=ix(w[1]),ix(w[2]);v=float(w[3])
   if k=='V' and w[0] in ('VBEND','VTUNE','VKEYBOARD','VMOD','VEXT','VOSC1_RANGE'):v=c[5+['VBEND','VTUNE','VKEYBOARD','VMOD','VEXT','VOSC1_RANGE'].index(w[0])]
   if k=='R' and w[0] not in trims:
    g=one/D(v);branch(a,b,(val(a)-val(b))*g,[(a,g),(b,-g)])
   elif k=='C' and dt:
    # Explicit binary64 voltage-difference interface shared by all accepted memories.
    now=(0. if a==N else x[a])-(0. if b==N else x[b]);old=(0. if a==N else previous[a])-(0. if b==N else previous[b]);g=D(v)/D(dt)
    branch(a,b,g*(D(now)-D(old)),[(a,g),(b,-g)])
   elif k=='V' or (k=='R' and w[0] in trims):
    row=NV+vs if k=='V' else 131+trims.index(w[0]);vs+=int(k=='V');branch(a,b,z[row],[(row,one)])
    resistance=zero if k=='V' else D(v);r[row]=val(a)-val(b)-(D(v) if k=='V' else zero)-resistance*z[row]
    derivative(row,a,one);derivative(row,b,-one);derivative(row,row,-resistance)
   elif k=='I':branch(a,b,D(v),[])
  elif k in 'QJ':
   m=[ix(n) for n in w[1:4]]+([N] if k=='Q' else [])
   node=[0. if n==N else x[n] for n in m];old=[0. if n==N else previous[n] for n in m]
   out=bjt.reference(1 if w[4]=='LAB_NPN' else -1,node,old,dt or 125e-9) if k=='Q' else jfet.reference(node,old,dt or 125e-9)
   size=len(m);cur=out[size:2*size] if dt else out[:size];start=3*size+(size*size if dt else 0);jac=out[start:start+size*size]
   for ri,row in enumerate(m):
    add(row,D(cur[ri]))
    for ci,col in enumerate(m):derivative(row,col,D(jac[ri*size+ci]))
 for m in inv['opamp_maps']:
  q=[0. if n==N else x[n] for n in m];old=[0. if n==N else previous[n] for n in m]
  h=[old[op.NODES.index(a)]-old[op.NODES.index(b)] for a,b in [(5,6),(98,9),(98,15)]]+old[35:37]
  v=op.reference(q,dt,h)
  for ri,row in enumerate(m):
   add(row,D(v[ri]))
   for ci,col in enumerate(m):derivative(row,col,D(v[op.N+ri*op.N+ci]))
  ground+=D(v[-1])
 return list(map(float,r)),[[float(g) for g in row] for row in j],float(ground)

def expressions(inv):
 result=['v('+n+')' for n in inv['nodes']]
 amps=[w[0].lower() for w in inv['lines'] if w[0][0]=='X']
 result+=['v('+a+'.'+str(n)+')' for a in amps for n in op.NODES[5:]]
 result+=['real(i('+w[0].lower()+'))' for w in inv['lines'] if w[0][0]=='V']
 for a in amps:
  result+=['real(-@q.'+a+'.q2[ib])' if n=='EOS' else 'real(i('+('e' if n in ('EH','E1') else 'v')+'.'+a+'.'+n.lower()+'))' for n in op.V_NAMES]
  result+=['real(i(l.'+a+'.'+n.lower()+'))' for n in op.L_NAMES]
 result+=['real(@'+n+'[i])' for n in ('rr8_high','rr8_low','rr11_active')]
 if len(result)!=N:raise ValueError('all original unknowns exported')
 return result

def fixtures(samples):
 cases=[]
 with localcontext() as ctx:
  ctx.prec=100
  for c,states in samples:
   for x in states:
    old=[v+(((k%3)-1)*(5e-6 if k<NV else 1e-10)) for k,v in enumerate(x)]
    for dt,history in [(0.,x),(125e-9,x),(125e-9,old),(250e-9,old),(500e-9,old)]:
     r,j,g=reference(x,history,dt,c);cases.append((c,x,history,dt,r,j,g))
   for a,b in [(0.,0.),(0.,1000.),(1.,0.),(1.,1000.)]:
    cc=list(c);cc[0]=a;cc[1]=b;x=states[0];r,j,g=reference(x,x,125e-9,cc);cases.append((cc,x,x,125e-9,r,j,g))
    cc=list(c);cc[0]=.26134047;cc[1]=521.31266;cc[3]=.125;cc[4]=1e-6;cc[5:]=[-3.1,-2.1,-1.1,-.1,.125,-.25]
   x=states[-1];r,j,g=reference(x,x,250e-9,cc);cases.append((cc,x,x,250e-9,r,j,g))
 pattern=sorted({(r,col) for v in cases for r in range(N) for col in range(N) if v[5][r][col]!=0.})
 rows=[[*c,*x,*p,dt,*r,g,*[j[a][b] for a,b in pattern]] for c,x,p,dt,r,j,g in cases]
 return pattern,rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,required=True);a=ap.parse_args().attempt
 if not 1<=a<=99:raise ValueError('attempt')
 out=ROOT/f'evidence/voice_vco1_stamp_reference{a:02d}.json';work=ROOT/f'references-local/vco1-stamp-reference{a:02d}'
 if out.exists() or work.exists():raise ValueError('preserve attempt')
 if (ROOT/'crates/rf-d-circuit/src/vco1_stamp_data.rs').read_bytes()!=rust_data().encode():raise ValueError('native inventory exact documentary expansion')
 inherited=json.loads((ROOT/'evidence/voice_lm741_port_tests01.json').read_text(encoding='utf8'))
 before={n:sha(ROOT/n) for n in SOURCES};private=dict(inherited['private_input_sha256']);private[EXE]=sha(ROOT/EXE)
 if private[EXE]!=EXPECTED_EXE_SHA:raise ValueError('official simulator identity')
 free=shutil.disk_usage(ROOT).free
 report=dict(schema='rf-d/vco1-full-stamp-oracle/v1',passed=False,base_commit=BASE,gates=GATES,source_sha256=before,private_input_sha256=private,commands=[],unchanged_replays=[],outputs=[],new_audio=False,resource_passed=free>2*1024**3+256*1024**2,estimated_bytes=256*1024**2,available_free_bytes=free,estimates_are_not_bounds=True)
 def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 write()
 if not report['resource_passed']:return
 work.mkdir();samples=[];startup=[];start=time.perf_counter()
 try:
  for index,s in enumerate([Scenario(c4_f=10e-12),Scenario(c4_f=100e-12)]):
   folder=work/f'case{index:02d}';folder.mkdir();dc=folder/'dc.txt';tr=folder/'transient.txt';deck=folder/'probe.cir';log=folder/'probe.log'
   inv=inventory(s);ex=' '.join(expressions(inv));startup_current=None
   for mode,data in [('startup',dc),('transient',tr)]:
    deck=folder/(mode+'.cir');log=folder/(mode+'.log')
    text,_=netlist(s,tr);base=text.split('.ic ')[0]
    if mode=='startup':base=base.replace('reltol=1e-7 abstol=1e-13 vntol=1e-8','reltol=1e-10 abstol=1e-15 vntol=1e-12')
    if mode=='startup':
     text=base+'Vstartup RAMP_C1 0 0\n.control\nop\n'
    else:
     text=base+'.ic v(RAMP_C1)=0\n.control\nsave all @q.xic1.q2[ib] @q.xic3.q2[ib] @rr8_high[i] @rr8_low[i] @rr11_active[i]\ntran 5e-7 2e-4 0 5e-7\n'
    text+='set numdgt=17\nset wr_vecnames\nset wr_singlescale\nwrdata '+data.as_posix()+' '+ex+(' real(i(vstartup))' if mode=='startup' else '')+'\nquit\n.endc\n.end\n'
    deck.write_text(text,encoding='utf8',newline='\n');command=[str(ROOT/EXE),'-b',str(deck)]
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=60);log.write_text(p.stdout+p.stderr,encoding='utf8',newline='\n')
    entry=dict(command=command,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,deck_sha256=sha(deck),mode=mode);report['commands'].append(entry);write()
    try:
     if p.returncode or any(q in (p.stdout+p.stderr).lower() for q in ('error:','fatal','simulation(s) aborted')):raise ValueError('original circuit process')
     if mode=='startup':
      row=list(map(float,data.read_text().splitlines()[1].split()));root=row[1:-1];startup_current=row[-1]
      if len(root)!=N or any(not math.isfinite(v) for v in row):raise ValueError('startup export')
      with localcontext() as ctx:
       ctx.prec=100;r,j,g=reference(root,root,0.,config(s))
      r[inv['nodes'].index('RAMP_C1')]+=startup_current
      if max(map(abs,r[:NV]))>=1e-11 or max(map(abs,r[NV:]))>=1e-11 or root[inv['nodes'].index('RAMP_C1')]!=0.:raise ValueError(('constrained startup DC residual',max(map(abs,r[:NV])),max(map(abs,r[NV:]))))
      entry.update(dc_kcl_a=max(map(abs,r[:NV])),dc_constraint_v=max(map(abs,r[NV:])),forcing_current_a=startup_current)
     else:
      transient=[list(map(float,line.split())) for line in data.read_text().splitlines()[1:]]
      if any(len(row)!=N+1 or any(not math.isfinite(v) for v in row) for row in transient):raise ValueError('complete finite export')
      if transient[0][0]!=0. or abs(transient[-1][0]-2e-4)>1e-15 or any(b[0]<=a[0] for a,b in zip(transient,transient[1:])):raise ValueError('whole SPICE clock')
      entry.update(transient_rows=len(transient),complete_end_s=transient[-1][0])
     write()
    except Exception:
     originals=[]
     if data.exists():
      copy=folder/(data.stem+'-failed-original.txt');shutil.copyfile(data,copy);originals.append(dict(path=copy.relative_to(ROOT).as_posix(),sha256=sha(copy),bytes=copy.stat().st_size))
     entry['failed_export_before_replay']=originals;write()
     rp=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=60);report['unchanged_replays'].append(dict(command=command,exit_code=rp.returncode,stdout=rp.stdout,stderr=rp.stderr,source_sha256={n:sha(ROOT/n) for n in before}));write();raise
   startup.append([*config(s),*root,startup_current])
   samples.append((config(s),[root,transient[len(transient)//2][1:],transient[-1][1:]]))
  pattern,rows=fixtures(samples)
  pp=ROOT/f'evidence/voice_vco1_stamp_pattern{a:02d}.txt';vp=ROOT/f'evidence/voice_vco1_stamp_vectors{a:02d}.txt'
  sp=ROOT/f'evidence/voice_vco1_stamp_startup{a:02d}.txt'
  for p in (pp,vp,sp):
   if p.exists():raise ValueError('preserve fixture')
  pp.write_text(''.join(f'{i} {j}\n' for i,j in pattern),encoding='utf8',newline='\n');vp.write_text(op.table(rows),encoding='utf8',newline='\n')
  sp.write_text(op.table(startup),encoding='utf8',newline='\n')
  report.update(startup_text_sha256=sha(sp),passed=True,samples=samples,rows=len(rows),columns=len(rows[0]),pattern_entries=len(pattern),unknowns=N,node_voltages=NV,board_device_count=100,expanded_device_count=180,decimal_precision=100,native_seeds_used=False,text_sha256=sha(vp),pattern_sha256=sha(pp),new_spice_processes=len(report['commands']),native_autonomous_trajectory=False,free_dc_admitted=False,startup_dc_ramp_imposed=True)
 except Exception as exc:report.update(error=repr(exc),failed_source_text={n:(ROOT/n).read_text(encoding='utf8') for n in before if n.endswith(('.py','.rs','.md'))})
 report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private})
 report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in work.rglob('*') if p.is_file()]
 report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after'];write();print('VCO1 full-stamp reference:',report['passed'],report.get('error',''),flush=True)
if __name__=='__main__':main()
