"""Independent ngspice46 nominal NJF DC, held-bias charge and AC probes."""
import argparse,base64,json,math,re,shutil,subprocess,time
from decimal import localcontext
from vco_jfet_vectors import ROOT,PRIVATE,sha,reference,table as numeric_table
GATES={'i':(2e-14,1e-7),'q':(1e-20,1e-7),'c':(1e-19,1e-7),'y':(2e-12,1e-7)}
BIAS=((0.,0.),(-3.,-4.),(-4.,-3.),(-1.,-1.5),(-1.5,-1.),(-1.,-2.5),(-2.5,-1.),(-1.,-4.),(-4.,-1.),(.5,.2),(.2,.5),(-.2,-1.))
def read_table(p,columns,single=True):
 lines=p.read_text(encoding='utf8').splitlines()
 if len(lines)<2 or len(lines[0].split())!=columns or (single and len(lines)!=2):raise ValueError('complete named export')
 rows=[list(map(float,line.split())) for line in lines[1:]]
 if any(len(row)!=columns or any(not math.isfinite(v) for v in row) for row in rows):raise ValueError('finite complete export')
 return rows[0] if single else rows

def measure(case,stdout,node):
 dc=read_table(case/'dc.txt',4)[1:];hold=read_table(case/'hold.txt',4,False)
 if len(hold)<2 or hold[0][0]!=0. or abs(hold[-1][0]-250e-9)>1e-20 or any(not 0<b[0]-a[0]<=125e-9*(1+1e-12) for a,b in zip(hold,hold[1:])):raise ValueError('complete held-bias transient clock')
 if any(abs(v-e)>1e-12 for row in hold for v,e in zip(row[1:],node)):raise ValueError('held terminal voltage')
 q=[]
 for label in ('qgs','qgd'):
  found=re.findall(r'@j1\['+label+r'\]\s*=\s*([-+\d.eE]+)',stdout)
  if len(found)!=1 or not math.isfinite(float(found[0])):raise ValueError('one final held-state charge query')
  q.append(float(found[0]))
 cap=read_table(case/'cap.txt',3)
 if cap[0]!=1000.:raise ValueError('capacitance queried after AC')
 matrices=[[[0.]*3 for _ in range(3)] for _ in range(2)]
 for col in range(3):
  y=read_table(case/f'y{col}.txt',7)
  if y[0]!=1000.:raise ValueError('AC frequency')
  for i in range(3):matrices[0][i][col]=y[1+2*i];matrices[1][i][col]=y[2+2*i]
 with localcontext() as ctx:ctx.prec=100;ref=reference(node,node,125e-9)
 checks=[]
 def check(kind,actual,expected):
  absolute,relative=GATES[kind];ratios=[abs(a-e)/(absolute+relative*abs(e)) for a,e in zip(actual,expected)]
  checks.append(dict(kind=kind,max_abs=max(abs(a-e) for a,e in zip(actual,expected)),max_gate_ratio=max(ratios),passed=max(ratios)<=1))
 check('i',dc,ref[:3]);check('q',q,ref[38:40]);check('c',cap[1:],[ref[35],ref[27]])
 expected_y=[complex(ref[9+k],2*math.pi*1000*ref[27+k]) for k in range(9)]
 actual_y=[complex(matrices[0][i][j],matrices[1][i][j]) for i in range(3) for j in range(3)]
 check('y',actual_y,expected_y)
 return dict(ngspice_current_a=dc,ngspice_junction_charge_c=q,ngspice_junction_cap_f=cap[1:],admittance_real_s=matrices[0],admittance_imag_s=matrices[1],held_bias_rows=len(hold),held_bias_first_s=hold[0][0],held_bias_last_s=hold[-1][0],checks=checks,passed=all(c['passed'] for c in checks))

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);number=parser.parse_args().attempt
 if not 1<=number<=99:raise ValueError('attempt domain')
 out=ROOT/f'evidence/voice_vco_jfet_spice{number:02d}.json';txt=out.with_suffix('.txt');work=ROOT/f'references-local/vco-jfet-spice{number:02d}'
 if out.exists() or txt.exists() or work.exists():raise ValueError('preserve all attempts')
 v=json.loads((ROOT/'evidence/voice_vco_jfet_vectors01.json').read_text(encoding='utf8'))
 if not v['passed']:raise ValueError('oracle admission')
 for n,h in v['source_sha256'].items():
  if sha(ROOT/n)!=h:raise ValueError('bound oracle input '+n)
 names=set(v['source_sha256'])|{'evidence/voice_vco_jfet_vectors01.json','evidence/voice_vco_jfet_vectors01.txt','evidence/voice_vco_jfet_neighbors01.txt','tools/vco_jfet_spice.py'}
 before={n:sha(ROOT/n) for n in sorted(names)};private={n:sha(ROOT/n) for n in PRIVATE}
 exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe';expected='86c9ea5f645ca919e305639fa7bdb522355364c424d14e197f1ade617feb3453'
 if sha(exe)!=expected:raise ValueError('official executable identity')
 free=shutil.disk_usage(ROOT).free;estimate=8*1024**2;margin=2*1024**3
 report=dict(schema='rf-d/vco-jfet-spice/v1',passed=False,source_sha256=before,private_input_sha256=private,executable_sha256=expected,available_free_bytes=free,estimated_export_bytes=estimate,margin_bytes=margin,resource_passed=free>=estimate+margin,gates=GATES,cases=[],unchanged_replays=[],new_audio=False)
 def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 write()
 if not report['resource_passed']:raise ValueError('resource admission')
 work.mkdir();cards=json.loads((ROOT/'evidence/vco1_laboratory_devices.json').read_text(encoding='utf8'))['jfet'];start=time.perf_counter();rows=[]
 try:
  for gs,gd in BIAS:
   case=work/f'case{len(rows):02d}';case.mkdir();gate=.17;node=[gate-gd,gate,gate-gs];sources=('vd','vg','vs')
   paths={n:case/(n+'.txt') for n in ('dc','hold','cap','y0','y1','y2')}
   if any(any(c.isspace() or c in '";$' for c in p.as_posix()) for p in paths.values()):raise ValueError('literal export paths')
   model=' '.join(f'{k}={v:.17g}' for k,v in cards.items())
   deck=['RF-D nominal NJF held-bias independent probe',*[f'{src} {pin} 0 {v:.17g}' for src,pin,v in zip(sources,('d','g','s'),node)],'j1 d g s m',f'.model m njf ({model})','.options temp=25 tnom=25 gmin=1e-12 reltol=1e-10 abstol=1e-16 vntol=1e-12','.control','set numdgt=17','set wr_singlescale','set wr_vecnames','op',f'wrdata {paths["dc"].as_posix()} '+ ' '.join(f'real(-i({src}))' for src in sources),'tran 125n 250n 0 125n',f'wrdata {paths["hold"].as_posix()} v(d) v(g) v(s)','print @j1[qgs] @j1[qgd]','ac lin 1 1000 1000',f'wrdata {paths["cap"].as_posix()} @j1[qgs] @j1[qgd]']
   for col in range(3):
    deck += [f'alter {src} acmag={int(j==col)}' for j,src in enumerate(sources)]
    deck += ['ac lin 1 1000 1000',f'wrdata {paths[f"y{col}"].as_posix()} '+ ' '.join(f'real(-i({src})) imag(-i({src}))' for src in sources)]
   deck+=['quit','.endc','.end',''];dp=case/'probe.cir';dp.write_text('\n'.join(deck),encoding='utf8',newline='\n')
   command=[str(exe),'-n','-b',str(dp)];entry=dict(terminal_v=node,command=command,deck_sha256=sha(dp),passed=False);report['cases'].append(entry);write()
   run=subprocess.run(command,cwd=exe.parent,capture_output=True,text=True,encoding='utf8',timeout=30)
   entry.update(exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr);(case/'probe.log').write_text(run.stdout+run.stderr,encoding='utf8',newline='\n');write()
   try:
    if run.returncode or 'error' in (run.stdout+run.stderr).lower():raise ValueError('SPICE process/log failure')
    measurement=measure(case,run.stdout,node);entry.update(measurement);write()
    if not entry['passed']:raise ValueError('independent numerical gate failed')
   except Exception:
    entry['failed_original_bytes_base64']={p.name:base64.b64encode(p.read_bytes()).decode() for p in case.iterdir() if p.is_file()};entry['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in before if n.endswith(('.rs','.py','.md'))};write()
    replay=subprocess.run(command,cwd=exe.parent,capture_output=True,text=True,encoding='utf8',timeout=30)
    report['unchanged_replays'].append(dict(command=command,exit_code=replay.returncode,stdout=replay.stdout,stderr=replay.stderr,deck_sha256_after=sha(dp),source_sha256={n:sha(ROOT/n) for n in before}));write();raise
   flat=lambda m:[v for row in m for v in row]
   rows.append([*node,*entry['ngspice_junction_charge_c'],*entry['ngspice_junction_cap_f'],*entry['ngspice_current_a'],*flat(entry['admittance_real_s']),*flat(entry['admittance_imag_s'])]);print('SPICE JFET cases:',len(rows),flush=True)
  report['passed']=len(rows)==12
 except Exception as exc:report['error']=str(exc)
 report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},executable_sha256_after=sha(exe),outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()])
 report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after'] and expected==report['executable_sha256_after']
 if report['passed']:txt.write_text(numeric_table(rows),encoding='utf8',newline='\n');report.update(rows=12,columns=28,text_sha256=sha(txt),new_spice_processes=12)
 write();print('SPICE JFET admission:',report['passed'],flush=True)
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
