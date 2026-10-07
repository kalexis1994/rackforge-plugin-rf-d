"""Fresh independent ngspice46 four-terminal DC/charge/AC probes."""
import argparse,base64,json,math,shutil,subprocess,time
from decimal import localcontext
from pathlib import Path
from vco_bjt_vectors import ROOT,PRIVATE,sha,reference
GATES={'i':(2e-14,1e-7),'q':(1e-20,1e-7),'c':(1e-19,1e-7),'y':(2e-12,1e-7)}
BIAS=((0.,0.),(.65,-1.),(-.2,.65),(.65,.62),(.3,.28),(-.2,-1.))
def table(p,columns):
 lines=p.read_text(encoding='utf8').splitlines()
 if len(lines)!=2 or len(lines[0].split())!=columns:raise ValueError('complete single-point named table')
 row=list(map(float,lines[1].split()))
 if len(row)!=columns or any(not math.isfinite(v) for v in row):raise ValueError('finite complete table')
 return row

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);number=parser.parse_args().attempt
 if not 1<=number<=99:raise ValueError('attempt domain')
 out=ROOT/f'evidence/voice_vco_bjt_spice{number:02d}.json';txt=out.with_suffix('.txt');work=ROOT/f'references-local/vco-bjt-spice{number:02d}'
 if out.exists() or txt.exists() or work.exists():raise ValueError('preserve all SPICE attempts')
 v=json.loads((ROOT/'evidence/voice_vco_bjt_vectors01.json').read_text(encoding='utf8'))
 for n,h in v['source_sha256'].items():
  if sha(ROOT/n)!=h:raise ValueError('bound oracle input')
 names=set(v['source_sha256'])|{'evidence/voice_vco_bjt_vectors01.json','evidence/voice_vco_bjt_vectors01.txt','evidence/voice_vco_bjt_neighbors01.txt','tools/vco_bjt_spice.py'}
 before={n:sha(ROOT/n) for n in sorted(names)};private={n:sha(ROOT/n) for n in PRIVATE}
 exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe'
 expected='86c9ea5f645ca919e305639fa7bdb522355364c424d14e197f1ade617feb3453'
 if sha(exe)!=expected:raise ValueError('pinned official executable')
 free=shutil.disk_usage(ROOT).free;estimate=8*1024**2;margin=2*1024**3
 report=dict(schema='rf-d/vco-bjt-spice/v1',passed=False,source_sha256=before,private_input_sha256=private,executable_sha256=expected,available_free_bytes=free,estimated_export_bytes=estimate,margin_bytes=margin,resource_passed=free>=estimate+margin,gates=GATES,cases=[],unchanged_replays=[],new_audio=False)
 def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 write()
 if not report['resource_passed']:raise ValueError('SPICE storage admission')
 work.mkdir();cards=json.loads((ROOT/'evidence/vco1_laboratory_devices.json').read_text(encoding='utf8'))['bjt'];rows=[];start=time.perf_counter()
 try:
  for polarity in (1,-1):
   for be,bc in BIAS:
    case=work/f'case{len(rows):02d}';case.mkdir();base=.17
    node=[base-polarity*bc,base,base-polarity*be,.125];sources=('vc','vb','ve','vs')
    paths={label:case/(label+'.txt') for label in ('dc','q','y0','y1','y2','y3')}
    if any(any(c.isspace() or c in '";$' for c in p.as_posix()) for p in paths.values()):raise ValueError('literal ngspice path')
    model=' '.join(f'{k}={v:.17g}' for k,v in cards.items())
    deck=['RF-D nominal BJT four-terminal independent probe',*[f'{src} {pin} 0 {value:.17g}' for src,pin,value in zip(sources,('c','b','e','s'),node)],'q1 c b e s m',f'.model m {"npn" if polarity==1 else "pnp"} ({model})','.options temp=25 tnom=25 gmin=1e-12 reltol=1e-10 abstol=1e-16 vntol=1e-12','.control','set numdgt=17','set wr_singlescale','set wr_vecnames','op',f'wrdata {paths["dc"].as_posix()} '+ ' '.join(f'-i({src})' for src in sources),'ac lin 1 1000 1000',f'wrdata {paths["q"].as_posix()} @q1[qbe] @q1[qbc] @q1[cpi] @q1[cmu]']
    for col in range(4):
     deck += [f'alter {src} acmag={int(j==col)}' for j,src in enumerate(sources)]
     deck += ['ac lin 1 1000 1000',f'wrdata {paths[f"y{col}"].as_posix()} '+ ' '.join(f'real(-i({src})) imag(-i({src}))' for src in sources)]
    deck+=['quit','.endc','.end',''];dp=case/'probe.cir';dp.write_text('\n'.join(deck),encoding='utf8',newline='\n')
    command=[str(exe),'-n','-b',str(dp)];entry=dict(polarity=polarity,terminal_v=node,command=command,deck_sha256=sha(dp),passed=False);report['cases'].append(entry);write()
    run=subprocess.run(command,cwd=exe.parent,capture_output=True,text=True,encoding='utf8',timeout=30)
    entry.update(exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr)
    (case/'probe.log').write_text(run.stdout+run.stderr,encoding='utf8',newline='\n');write()
    try:
     if run.returncode or 'error' in (run.stdout+run.stderr).lower():raise ValueError('SPICE process/log failure')
     dc=table(paths['dc'],5)[1:];q=table(paths['q'],5)
     if q[0]!=1000.:raise ValueError('charge AC point')
     matrices=[[[0.]*4 for _ in range(4)] for _ in range(2)]
     for col in range(4):
      y=table(paths[f'y{col}'],9)
      if y[0]!=1000.:raise ValueError('AC frequency')
      for i in range(4):matrices[0][i][col]=y[1+2*i];matrices[1][i][col]=y[2+2*i]
     with localcontext() as ctx:ctx.prec=100;ref=reference(polarity,node,node,125e-9)
     checks=[]
     def check(kind,actual,expected):
      absolute,relative=GATES[kind];ratios=[abs(a-e)/(absolute+relative*abs(e)) for a,e in zip(actual,expected)]
      item=dict(kind=kind,max_abs=max(abs(a-e) for a,e in zip(actual,expected)),max_gate_ratio=max(ratios),passed=max(ratios)<=1);checks.append(item)
     check('i',dc,ref[0:4]);check('q',q[1:3],ref[62:64]);check('c',q[3:5],[ref[44+2*4+2],ref[44]])
     yref=[complex(ref[12+i],2*math.pi*1000.*ref[44+i]) for i in range(16)]
     yactual=[complex(matrices[0][i][j],matrices[1][i][j]) for i in range(4) for j in range(4)]
     check('y',yactual,yref)
     entry.update(checks=checks,ngspice_current_a=dc,ngspice_oriented_charge_c=q[1:3],ngspice_junction_cap_f=q[3:5],admittance_real_s=matrices[0],admittance_imag_s=matrices[1],passed=all(c['passed'] for c in checks));write()
     if not entry['passed']:raise ValueError('independent numerical gate failed')
    except Exception:
     # Preserve all original outputs before exact deck/command replay.
     snapshot={p.name:base64.b64encode(p.read_bytes()).decode() for p in case.iterdir() if p.is_file()}
     entry['failed_original_bytes_base64']=snapshot;entry['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in before if n.endswith(('.py','.rs','.md'))};write()
     replay=subprocess.run(command,cwd=exe.parent,capture_output=True,text=True,encoding='utf8',timeout=30)
     report['unchanged_replays'].append(dict(command=command,exit_code=replay.returncode,stdout=replay.stdout,stderr=replay.stderr,deck_sha256_after=sha(dp),source_sha256={n:sha(ROOT/n) for n in before}));write();raise
    flat=lambda m:[v for row in m for v in row]
    rows.append([polarity,*node,*q[1:5],*dc,*flat(matrices[0]),*flat(matrices[1])])
    print('SPICE BJT cases:',len(rows),flush=True)
  report['passed']=len(rows)==12
 except Exception as exc:report['error']=str(exc)
 report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},executable_sha256_after=sha(exe),outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()])
 report['passed']=report['passed'] and before==report['source_sha256_after'] and private==report['private_input_sha256_after'] and expected==report['executable_sha256_after']
 if report['passed']:
  txt.write_text('\n'.join(' '.join(format(v,'.17e') for v in r) for r in rows)+'\n',encoding='utf8',newline='\n');report.update(rows=12,columns=45,text_sha256=sha(txt),new_spice_processes=12)
 write();print('SPICE BJT admission:',report['passed'],flush=True)
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
