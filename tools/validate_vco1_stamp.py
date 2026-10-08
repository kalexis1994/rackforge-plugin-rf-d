"""Release full VCO1 incidence only, preserving all gates and historical attempts."""
import base64,hashlib,json,math,re,subprocess,sys,types
from decimal import localcontext
from pathlib import Path
import vco1_stamp_reference as oracle
from validate_mixer_on_native import native_source_identity
ROOT=oracle.ROOT;sha=oracle.sha
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md');LIB='crates/rf-d-circuit/src/lib.rs'
EXPORT=b'\npub mod vco1_stamp;\n'
ATTRS=b'/crates/rf-d-circuit/src/vco1_stamp.rs text eol=lf\n/crates/rf-d-circuit/src/vco1_stamp_data.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_stamp.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_stamp_no_alloc.rs text eol=lf\n/evidence/voice_vco1_stamp*.txt -text\n'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def archive(receipts):
 pool={}
 def add(b):
  if isinstance(b,str):b=b.encode()
  pool[hashlib.sha256(b).hexdigest()]=b
 for t in receipts:
  for n in t['source_sha256']:
   if (ROOT/n).exists():add((ROOT/n).read_bytes())
  for s in t.get('failed_source_text',{}).values():add(s)
 # Recover successful reference06 by its sole adapter addition to the retained reference05 source.
 t=receipts[4]['failed_source_text']['tools/vco1_stamp_reference.py']
 t=t.replace("k=w[0][0]\n  if k in", "k=w[0][0]\n  if w[0] in ('VR8_HIGH','VR8_LOW','VR11_ACTIVE'):w=['R'+w[0][1:],*w[1:]];k='R'\n  if k in");add(t)
 needed={h:n for r in receipts for n,h in r['source_sha256'].items()}
 missing=[(n,h) for h,n in needed.items() if h not in pool]
 if missing:raise ValueError(('historical source not recovered',missing))
 folder=ROOT/'references-local/vco1-stamp-source-identity01'
 if folder.exists():raise ValueError('preserve historical archive')
 folder.mkdir();outputs=[]
 for h,n in sorted(needed.items()):
  p=folder/(h+'.blob');p.write_bytes(pool[h]);outputs.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size,source_name=n))
 return outputs,pool

def main():
 out=ROOT/'evidence/voice_vco1_stamp_tests01.json'
 if out.exists():raise ValueError('preserve publication')
 qp=ROOT/'evidence/voice_lm741_port_tests01.json';q=read(qp)
 refs=[read(ROOT/f'evidence/voice_vco1_stamp_reference{k:02d}.json') for k in range(1,9)]
 native=[read(ROOT/f'evidence/voice_vco1_stamp_native{k:02d}.json') for k in (1,2)];v=refs[-1];a=native[-1]
 if not q['passed'] or q['covered_test_count']!=213 or [t['passed'] for t in refs]!=[False]*5+[True]*3 or [t['passed'] for t in native]!=[False,True]:raise ValueError('exact inherited and new admission')
 snap=read(ROOT/'evidence/voice_vco1_stamp_documentation01.json')
 if snap['previous_qa_sha256']!=sha(qp) or set(snap['previous_bytes_base64'])!=set(DOCS):raise ValueError('documentation identity')
 for n,h in q['source_sha256'].items():
  if n in DOCS:
   old=base64.b64decode(snap['previous_bytes_base64'][n]);native_source_identity(n,h,old)
  elif n in (LIB,'.gitattributes'):
   old=subprocess.check_output(['git','show',oracle.BASE+':'+n],cwd=ROOT);native_source_identity(n,h,old)
   if (ROOT/n).read_bytes()!=old+(EXPORT if n==LIB else ATTRS):raise ValueError('exact additive graph export/policy')
  elif sha(ROOT/n)!=h:raise ValueError('inherited input changed '+n)
 for receipt in refs+native:
  if receipt['source_sha256']!=receipt['source_sha256_after'] or receipt['private_input_sha256']!=receipt['private_input_sha256_after']:raise ValueError('attempt changed measured source')
  for n,s in receipt.get('failed_source_text',{}).items():
   if hashlib.sha256(s.encode()).hexdigest()!=receipt['source_sha256'][n]:raise ValueError('failed source bytes')
 for t in refs[:4]+native[:1]:
  if len(t['unchanged_replays'])!=1 or t['unchanged_replays'][0]['command']!=t['commands'][-1]['command']:raise ValueError('same failed command replay')
 for n,h in v['source_sha256'].items():
  if sha(ROOT/n)!=h:raise ValueError('current oracle source '+n)
 for n,h in a['source_sha256'].items():
  if sha(ROOT/n)!=h:raise ValueError('current production source '+n)
 if (ROOT/'crates/rf-d-circuit/src/vco1_stamp_data.rs').read_bytes()!=oracle.rust_data().encode():raise ValueError('exact documentary incidence')
 inv=oracle.inventory();amp_maps=inv['opamp_maps']
 if amp_maps[0][2]!=134 or amp_maps[0][3]!=14 or amp_maps[1][1]!=15:raise ValueError('IC1 ground and shared rail mapping')
 pattern,rows=oracle.fixtures(v['samples'])
 pp=ROOT/'evidence/voice_vco1_stamp_pattern08.txt';vp=ROOT/'evidence/voice_vco1_stamp_vectors08.txt';sp=ROOT/'evidence/voice_vco1_stamp_startup08.txt'
 if v['gates']!=oracle.GATES or len(rows)!=40 or len(pattern)!=534 or len(rows[0])!=949:raise ValueError('frozen dimensions/gates')
 if vp.read_text(encoding='utf8')!=oracle.op.table(rows) or pp.read_text()!= ''.join(f'{r} {c}\n' for r,c in pattern):raise ValueError('Decimal whole-bank reproduction')
 if sha(vp)!=v['text_sha256'] or sha(pp)!=v['pattern_sha256'] or sha(sp)!=v['startup_text_sha256']:raise ValueError('fixture hashes')
 startup=[]
 for index,(c,states) in enumerate(v['samples']):
  folder=ROOT/f'references-local/vco1-stamp-reference08/case{index:02d}'
  dc=list(map(float,(folder/'dc.txt').read_text().splitlines()[1].split()));tr=[list(map(float,l.split())) for l in (folder/'transient.txt').read_text().splitlines()[1:]]
  if dc[1:-1]!=states[0] or tr[len(tr)//2][1:]!=states[1] or tr[-1][1:]!=states[2]:raise ValueError('samples exact original exports')
  if len(tr)!=(515,513)[index] or tr[0][0]!=0. or abs(tr[-1][0]-2e-4)>1e-15 or any(len(l)!=135 or any(not math.isfinite(x) for x in l) for l in tr) or any(b[0]<=a[0] for a,b in zip(tr,tr[1:])):raise ValueError('complete finite clock')
  with localcontext() as ctx:
   ctx.prec=100;r,j,g=oracle.reference(states[0],states[0],0.,c)
  r[inv['nodes'].index('RAMP_C1')]+=dc[-1]
  if max(map(abs,r[:98]))>=1e-11 or max(map(abs,r[98:]))>=1e-11:raise ValueError('constrained DC unchanged gate')
  startup.append([*c,*states[0],dc[-1]])
 if sp.read_text()!=oracle.op.table(startup):raise ValueError('forcing current identity')
 compiler=a['compiler'];stdout='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 if sha(Path(compiler['path']))!=compiler['sha256'] or a['compiler_sha256_after']!=compiler['sha256'] or any(c['exit_code'] for c in a['commands']) or len(a['outputs'])!=3:raise ValueError('production binaries/compiler')
 if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',stdout)!=['3','1'] or stdout.count('VCO1_ALLOCATION,stamps=1000,allocations=0')!=1 or stdout.count('VCO1_FD,columns=5360,history=fixed')!=1:raise ValueError('four tests, all columns and no heap')
 m=re.search(r'max_residual=([^,\s]+),max_jacobian=([^,\s]+),max_balance_a=([^,\s]+)',stdout)
 if not m:raise ValueError('captured numerical maxima')
 maxima=dict(zip(['residual','jacobian','balance_a'],map(float,m.groups())))
 private=dict(q['private_input_sha256'])
 for t in refs+native:
  for o in t['outputs']:
   p=ROOT/o['path']
   if not p.resolve().is_relative_to((ROOT/'references-local').resolve()) or sha(p)!=o['sha256'] or p.stat().st_size!=o['bytes']:raise ValueError('private output changed')
   private[o['path']]=o['sha256']
 for folder in ('vco1-stamp-syntax01','vco1-stamp-admission-failure01'):
  for p in (ROOT/'references-local'/folder).rglob('*'):
   if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
 source_archive,pool=archive(refs+native)
 for item in source_archive:private[item['path']]=item['sha256']
 # Replay the exact failed fixture stage of reference05 against its original source bytes.
 oldinv=types.ModuleType('vco1_native_inventory');oldinv.__file__=str(ROOT/'tools/vco1_native_inventory.py')
 exec(pool[refs[4]['source_sha256']['tools/vco1_native_inventory.py']],oldinv.__dict__)
 live=sys.modules['vco1_native_inventory'];sys.modules['vco1_native_inventory']=oldinv
 helper=types.ModuleType('vco1_stamp_reference_historical');helper.__file__=str(ROOT/'tools/vco1_stamp_reference.py')
 try:exec(pool[refs[4]['source_sha256']['tools/vco1_stamp_reference.py']],helper.__dict__)
 finally:sys.modules['vco1_native_inventory']=live
 samples=[]
 for index in (0,1):
  folder=ROOT/f'references-local/vco1-stamp-reference05/case{index:02d}';dc=list(map(float,(folder/'dc.txt').read_text().splitlines()[1].split()))[1:-1];tr=[list(map(float,l.split())) for l in (folder/'transient.txt').read_text().splitlines()[1:]]
  samples.append((helper.config(helper.Scenario(c4_f=(1e-11,1e-10)[index])),[dc,tr[len(tr)//2][1:],tr[-1][1:]]))
 try:helper.fixtures(samples)
 except ValueError as exc:
  if repr(exc)!=refs[4]['error']:raise ValueError('different fixture failure')
  replay=dict(stage='fixtures(samples)',error=repr(exc),source_sha256={n:refs[4]['source_sha256'][n] for n in ('tools/vco1_native_inventory.py','tools/vco1_stamp_reference.py')},samples_sha256=hashlib.sha256(json.dumps(samples,sort_keys=True,separators=(',',':')).encode()).hexdigest())
 else:raise ValueError('original failed fixture unexpectedly passes')
 rp=ROOT/'references-local/vco1-stamp-source-identity01/fixture05-replay.json';rp.write_text(json.dumps(replay,indent=2)+'\n',encoding='utf8',newline='\n');private[rp.relative_to(ROOT).as_posix()]=sha(rp)
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('private identity '+n)
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(q['source_sha256'])|{qp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 local=[]
 for name in (*DOCS,'docs/VCO1_STAMP_PROTOCOLO.md','docs/VCO1_STAMP_RESULTADOS.md'):
  p=ROOT/name
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve()
   if target!=out.resolve() and not target.exists():raise ValueError('publication target '+link)
   local.append(target.relative_to(ROOT).as_posix())
 if sources!={n:sha(ROOT/n) for n in names}:raise ValueError('publication changed')
 processes=sum(len(t['commands'])+len(t['unchanged_replays']) for t in refs)
 if processes!=27:raise ValueError('launched SPICE count')
 report=dict(schema='rf-d/vco1-full-stamp-release/v1',passed=True,base_commit=oracle.BASE,previous_qa_sha256=sha(qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,historical_source_archive=source_archive,fixture05_unchanged_replay=replay,covered_test_count=217,inherited_test_count=213,native_test_count=4,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,native_full_vco1_stamp_admitted=True,native_joint_solver_admitted=False,native_autonomous_vco_admitted=False,free_dc_admitted=False,calibrated_startup_admitted=False,constrained_startup_ramp_v=0.,unknown_count=134,node_count=98,board_device_count=100,expanded_device_count=180,fixture_rows=40,jacobian_entries_checked=718240,fd_columns_checked=5360,numerical_maxima=maxima,new_spice_processes=processes,latest_spice_case_count=4,temperature_c=25,new_audio=False,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],checked_local_targets=sorted(set(local)),long_note_admitted_locally=False,physical_fidelity=False,real_time=False)
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('VCO1 full stamp: 217 covered, four new+213 inherited;',len(sources),'public;',len(private),'private;',len(source_archive),'historical source versions',flush=True)
if __name__=='__main__':main()
