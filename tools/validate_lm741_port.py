"""Admit bounded LM741 port solves, fixed-history tangents and trajectory scope."""
import base64,hashlib,json,math,re,subprocess
from decimal import localcontext
from pathlib import Path
import lm741_port_reference as oracle
from validate_mixer_on_native import native_source_identity
ROOT=oracle.ROOT;sha=oracle.sha;BASE=oracle.BASE
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
EXPORT=b'\npub mod lm741_port;\n'
ATTRS=b'/crates/rf-d-circuit/src/lm741_port.rs text eol=lf\n/crates/rf-d-circuit/tests/lm741_port.rs text eol=lf\n/crates/rf-d-circuit/tests/lm741_port_no_alloc.rs text eol=lf\n/evidence/voice_lm741_port*.txt -text\n'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def archive_sources(receipts):
 # Every historically measured source version must be recoverable, including successes.
 candidates={}
 def add(data):
  if isinstance(data,str):data=data.encode()
  candidates[hashlib.sha256(data).hexdigest()]=data
 for t in receipts:
  for n in t['source_sha256']:
   if (ROOT/n).exists():add((ROOT/n).read_bytes())
  for text in t.get('failed_source_text',{}).values():add(text)
 module=(ROOT/'crates/rf-d-circuit/src/lm741_port.rs').read_text(encoding='utf8')
 guard=' if p.iter().any(|v|!v.is_finite()||v.abs()>40.) || p[3]+1.63-0.65>p[2]-1.63+0.65 {return [f64::NAN;N];}\n'
 if module.count(guard)!=1:raise ValueError('exact additive seed guard')
 add(module.replace(guard,''))
 protocol=(ROOT/'docs/VCO_741_PUERTO_PROTOCOLO.md').read_text(encoding='utf8')
 add(protocol.split('\nLa API de semilla')[0]);add(protocol.split('\n## Integridad de los intentos')[0])
 helper=(ROOT/'tools/lm741_port_reference.py').read_text(encoding='utf8')
 backup="     if data.exists():\n      original=folder/'trajectory-failed-original.txt';shutil.copyfile(data,original)\n      entry['failed_export_before_replay']=dict(path=original.relative_to(ROOT).as_posix(),sha256=sha(original),bytes=original.stat().st_size);write()\n"
 add(helper.replace(backup,'').replace('D(h[3])','D(h[4-1])'))
 old_helper=helper.replace(backup,'').replace('D(h[3])','D(h[4-1])')
 old_helper=old_helper.replace('private=dict(json.loads','private=json.loads').replace("['private_input_sha256'])\n control='references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/analysis/cktdojob.c';private[control]=sha(ROOT/control)\n","['private_input_sha256']\n")
 add(old_helper)
 texts=list(candidates.values())
 for b in texts:
  if b'targets = (' in b or b'fn own_dc_and_672' in b:
   s=b.decode()
   for old in range(7,13):
    for new in range(7,13):
     add(s.replace(f'voice_lm741_port_reference{old:02d}',f'voice_lm741_port_reference{new:02d}').replace(f'voice_lm741_port_spice{old:02d}',f'voice_lm741_port_spice{new:02d}').replace(f'voice_lm741_port_trajectory{old:02d}',f'voice_lm741_port_trajectory{new:02d}'))
 needed={h:n for t in receipts for n,h in t['source_sha256'].items()}
 missing=[(n,h) for h,n in needed.items() if h not in candidates]
 if missing:raise ValueError(('historical source not recovered',missing))
 folder=ROOT/'references-local/lm741-port-source-identity01'
 if folder.exists():raise ValueError('preserve source identity archive')
 folder.mkdir();outputs=[]
 for h,n in sorted(needed.items()):
  p=folder/(h+'.blob');p.write_bytes(candidates[h]);outputs.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size,source_name=n))
 return outputs

def main():
 out=ROOT/'evidence/voice_lm741_port_tests01.json'
 if out.exists():raise ValueError('preserve publication')
 qp=ROOT/'evidence/voice_lm741_tests01.json';q=read(qp)
 vp=ROOT/'evidence/voice_lm741_port_reference12.json';v=read(vp)
 ap=ROOT/'evidence/voice_lm741_port_native05.json';a=read(ap)
 sp=ROOT/'evidence/voice_lm741_port_documentation01.json';snapshot=read(sp)
 if not all(t['passed'] for t in (q,v,a)) or q['covered_test_count']!=209:raise ValueError('209 inherited plus four new')
 if snapshot['previous_qa_sha256']!=sha(qp) or set(snapshot['previous_bytes_base64'])!=set(DOCS):raise ValueError('documentation lineage')
 for n,b in snapshot['previous_bytes_base64'].items():
  if hashlib.sha256(base64.b64decode(b,validate=True)).hexdigest()!=q['source_sha256'][n]:raise ValueError('exact parent document')
 for n,h in q['source_sha256'].items():
  if n in DOCS:continue
  if n in ('crates/rf-d-circuit/src/lib.rs','.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT);native_source_identity(n,h,old)
   if (ROOT/n).read_bytes()!=old+(EXPORT if n.endswith('lib.rs') else ATTRS):raise ValueError('only additive exports/policies')
  elif sha(ROOT/n)!=h:raise ValueError('inherited input changed '+n)
 for receipt in (v,a):
  if receipt['source_sha256']!=receipt['source_sha256_after'] or receipt['private_input_sha256']!=receipt['private_input_sha256_after']:raise ValueError('measured inputs changed')
  for n,h in receipt['source_sha256'].items():
   if sha(ROOT/n)!=h:raise ValueError('final measured source '+n)
  for n,h in receipt['private_input_sha256'].items():
   if sha(ROOT/n)!=h:raise ValueError('final primary input '+n)
  if not receipt['resource_passed'] or receipt['available_free_bytes']<receipt['estimated_export_bytes' if receipt is v else 'estimated_build_bytes']+receipt['margin_bytes']:raise ValueError('resource gate')
 if v['gates']!=oracle.GATES or (v['trajectory_rows'],v['trajectory_columns'],v['local_spice_rows'],v['local_spice_columns'],v['decimal_precision'],v['native_seeds_used'],v['xtrtol'],v['new_spice_processes'])!=(672,50,371,80,100,False,1000000000,9) or v['unchanged_replays']:raise ValueError('frozen final bank')
 rows=[];profiles=[]
 for scene in range(3):
  for dt in oracle.DTS:
   index=len(profiles);folder=ROOT/f'references-local/lm741-port-reference12/case{index:02d}';c=v['commands'][index];raw=[list(map(float,l.split())) for l in (folder/'trajectory.txt').read_text().splitlines()[1:]]
   if c['exit_code'] or sha(folder/'probe.cir')!=c['deck_sha256'] or (folder/'probe.log').read_text()!=c['stdout']+c['stderr']:raise ValueError('original complete deck/log')
   if raw[0][0]!=0 or abs(raw[-1][0]-oracle.DURATION)>1e-15 or any(len(r)!=43 or not all(math.isfinite(x) for x in r) for r in raw) or any(x[0]>=y[0] for x,y in zip(raw,raw[1:])):raise ValueError('finite increasing coverage')
   eligible=excluded=0
   for previous,current in zip(raw,raw[1:]):
    interval=current[0]-previous[0]
    if 125e-9<=interval<=1e-3:rows.append([interval,*previous[1:38],*current[1:]]);eligible+=1
    else:excluded+=1
   if eligible<20:raise ValueError('fixed minimum eligible intervals')
   profiles.append(dict(scene=scene,maxstep_s=dt,rows=len(raw),eligible_intervals=eligible,excluded_intervals=excluded,begin_s=raw[0][0],end_s=raw[-1][0]))
 if profiles!=v['profiles'] or sum(p['excluded_intervals'] for p in profiles)!=458:raise ValueError('exact temporal scope')
 st=ROOT/'evidence/voice_lm741_port_spice12.txt'
 if st.read_bytes()!=oracle.table(rows).encode() or sha(st)!=v['spice_text_sha256']:raise ValueError('raw interval replay')
 roots=[list(map(float,l.split())) for l in (ROOT/'evidence/voice_lm741_roots09.txt').read_text().splitlines()];trajectory=[]
 with localcontext() as ctx:
  ctx.prec=100;x0,_=oracle.decimal_solve(oracle.ports(0,0.),0.,[0.]*5,roots[0][:37])
  for scene in range(3):
   for dt in oracle.DTS:
    x=list(x0)
    for k in range(1,round(oracle.DURATION/dt)+1):
     t=k*dt;p=oracle.ports(scene,t);h=oracle.memory(x);x,i=oracle.decimal_solve(p,dt,h,x);trajectory.append([scene,dt,t,*p,*map(float,x),*map(float,i)])
 tt=ROOT/'evidence/voice_lm741_port_trajectory12.txt'
 if tt.read_bytes()!=oracle.table(trajectory).encode() or sha(tt)!=v['text_sha256']:raise ValueError('all 672 independent Decimal100 steps replay')
 refs=[read(ROOT/f'evidence/voice_lm741_port_reference{k:02d}.json') for k in range(1,13)]
 native=[read(ROOT/f'evidence/voice_lm741_port_native{k:02d}.json') for k in range(1,6)]
 if [t['passed'] for t in refs]!=[False]*6+[True]*6 or [t['passed'] for t in native]!=[False,False,True,True,True]:raise ValueError('historical outcomes')
 for first,second in ((refs[2],refs[3]),(refs[4],refs[5])):
  if first['source_sha256']!=second['source_sha256'] or first['error']!=second['error']:raise ValueError('whole oracle failure unchanged replay')
 for k in range(7,12):
  for kind in ('spice','trajectory'):
   if (ROOT/f'evidence/voice_lm741_port_{kind}{k:02d}.txt').read_bytes()!=(st if kind=='spice' else tt).read_bytes():raise ValueError('post-predictor exact vectors retained')
 for receipt in refs+native:
  if receipt['source_sha256']!=receipt['source_sha256_after'] or receipt['private_input_sha256']!=receipt['private_input_sha256_after']:raise ValueError('historical measured input mutation')
  for n,text in receipt.get('failed_source_text',{}).items():
   if hashlib.sha256(text.encode()).hexdigest()!=receipt['source_sha256'][n]:raise ValueError('failed source bytes')
 for t in refs[:2]+native[:2]:
  if len(t['unchanged_replays'])!=1 or t['unchanged_replays'][0]['command']!=t['commands'][-1]['command']:raise ValueError('same failing command replay')
 compiler=a['compiler']
 if sha(Path(compiler['path']))!=compiler['sha256'] or a['compiler_sha256_after']!=compiler['sha256'] or a['unchanged_replays'] or len(a['outputs'])!=3 or any(c['exit_code'] for c in a['commands']):raise ValueError('compiler and production')
 tests='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',tests)!=['3','1'] or tests.count('LM741_PORT_ALLOCATION,solves=1000,rhs=5,allocations=0')!=1:raise ValueError('four production tests')
 maxima={}
 for label,prefix in [('trajectory','LM741_PORT_TRAJECTORY,dc=6,profiles=9,steps=672,'),('spice','LM741_PORT_SPICE,intervals=371,')]:
  m=re.search(re.escape(prefix)+r'max_node_v=([^,\s]+),max_branch_a=([^,\s]+),max_port_a=([^,\s]+),max_iterations=(\d+)',tests)
  if not m:raise ValueError('captured numerical maxima')
  maxima[label]=dict(zip(['node_v','branch_a','port_a','iterations'],map(float,m.groups())))
  if any(not math.isfinite(x) or x<0 for x in maxima[label].values()):raise ValueError('finite maxima')
 private=dict(q['private_input_sha256']);private.update(v['private_input_sha256'])
 for receipt in refs+native:
  for item in receipt['outputs']:
   p=ROOT/item['path']
   if not p.resolve().is_relative_to((ROOT/'references-local').resolve()) or sha(p)!=item['sha256'] or p.stat().st_size!=item['bytes']:raise ValueError('retained measured output')
   private[item['path']]=item['sha256']
 for folder in ['lm741-port-reference04','lm741-port-native01','lm741-port-native02']:
  for p in (ROOT/'references-local'/folder).rglob('*'):
   if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('inherited/measured private input '+n)
 archive=archive_sources(refs+native)
 for item in archive:private[item['path']]=item['sha256']
 if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/oracle.EXE)!=q['official_executable_sha256']:raise ValueError('previous audio/executable')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(q['source_sha256'])|{qp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 local=[]
 for name in (*DOCS,'docs/VCO_741_PUERTO_PROTOCOLO.md','docs/VCO_741_PUERTO_RESULTADOS.md'):
  p=ROOT/name
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve()
   if target!=out.resolve() and not target.exists():raise ValueError('missing publication target '+link)
   local.append(target.relative_to(ROOT).as_posix())
 if sources!={n:sha(ROOT/n) for n in names}:raise ValueError('publication changed')
 processes=sum(len(t['commands'])+len(t['unchanged_replays']) for t in refs)
 if processes!=97:raise ValueError('exact launched SPICE count')
 report=dict(schema='rf-d/lm741-port-release/v1',passed=True,base_commit=BASE,previous_qa_sha256=sha(qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,historical_source_archive=archive,documentation_snapshot_sha256=sha(sp),oracle_sha256=sha(vp),production_sha256=sha(ap),numerical_maxima=maxima,covered_test_count=213,inherited_test_count=209,native_test_count=4,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,lm741_imposed_port_solver_admitted=True,own_euler_trajectory_count=9,own_euler_step_count=672,independent_local_spice_intervals=371,excluded_spice_intervals=458,continuous_accuracy_admitted=False,adaptive_spice_trajectory_identity=False,failed02_original_export_identity_proven=False,loaded_tangent_dimension=[5,5],node_gradient_dimension=[37,5],native_vco_admitted=False,new_spice_processes=processes,admitted_spice_case_count=9,temperature_c=25,tnom_c=25,other_temperatures_admitted=False,new_audio=False,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],checked_local_targets=sorted(set(local)),long_note_admitted_locally=False,physical_fidelity=False,real_time=False)
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('LM741 port: 213 covered, four new+209 inherited;',len(sources),'public;',len(private),'private;',len(archive),'historical source versions',flush=True)
if __name__=='__main__':main()
