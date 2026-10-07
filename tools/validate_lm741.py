"""Publication admission: full stamp, immutable failures, prior algorithms and raw roots."""
import base64,hashlib,json,math,re,subprocess
from decimal import localcontext
from pathlib import Path
import lm741_reference as oracle
from validate_mixer_on_native import native_source_identity
ROOT=oracle.ROOT;sha=oracle.sha;BASE='b7f5a898df245ea29b8f26de02f982386513b8ae'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
EXPORT=b'\npub mod lm741;\n'
ATTRS=b'/crates/rf-d-circuit/src/lm741.rs text eol=lf\n/crates/rf-d-circuit/tests/lm741.rs text eol=lf\n/crates/rf-d-circuit/tests/lm741_no_alloc.rs text eol=lf\n/evidence/voice_lm741*.txt -text\n'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
 out=ROOT/'evidence/voice_lm741_tests01.json'
 if out.exists():raise ValueError('preserve publication')
 qp=ROOT/'evidence/voice_vco_jfet_tests01.json';q=read(qp)
 vp=ROOT/'evidence/voice_lm741_reference09.json';v=read(vp)
 ap=ROOT/'evidence/voice_lm741_native02.json';a=read(ap)
 sp=ROOT/'evidence/voice_lm741_documentation01.json';snapshot=read(sp)
 if not all(t['passed'] for t in (q,v,a)) or q['covered_test_count']!=205:raise ValueError('205 inherited/four new required')
 if snapshot['previous_qa_sha256']!=sha(qp) or set(snapshot['previous_bytes_base64'])!=set(DOCS):raise ValueError('documentation lineage')
 for n,b in snapshot['previous_bytes_base64'].items():
  if hashlib.sha256(base64.b64decode(b,validate=True)).hexdigest()!=q['source_sha256'][n]:raise ValueError('exact prior document')
 for n,h in q['source_sha256'].items():
  if n in DOCS:continue
  if n in ('crates/rf-d-circuit/src/lib.rs','.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT);native_source_identity(n,h,old)
   if (ROOT/n).read_bytes()!=old+(EXPORT if n.endswith('lib.rs') else ATTRS):raise ValueError('additive exports/policies only')
  elif sha(ROOT/n)!=h:raise ValueError('inherited source changed '+n)
 private=dict(q['private_input_sha256'])
 for receipt in (v,a):
  if receipt['source_sha256']!=receipt['source_sha256_after'] or receipt['private_input_sha256']!=receipt['private_input_sha256_after']:raise ValueError('measured inputs changed')
  for n,h in receipt['source_sha256'].items():
   if sha(ROOT/n)!=h:raise ValueError('measured source identity '+n)
  private.update(receipt['private_input_sha256'])
  for output in receipt['outputs']:
   path=ROOT/output['path']
   if not path.resolve().is_relative_to((ROOT/'references-local').resolve()) or sha(path)!=output['sha256'] or path.stat().st_size!=output['bytes']:raise ValueError('private measured output')
   private[output['path']]=output['sha256']
  if not receipt['resource_passed'] or receipt['available_free_bytes']<receipt['estimated_export_bytes' if receipt is v else 'estimated_build_bytes']+receipt['margin_bytes']:raise ValueError('resource gate')
 if v['gates']!=oracle.GATES or (v['row_count'],v['column_count'],v['decimal_precision'],v['native_seeds_used'],v['primary_device_count'],v['unknown_count'],v['nodes'])!=(60,1455,100,False,41,37,oracle.NODES):raise ValueError('frozen complete oracle')
 roots=[]
 for index,bias in enumerate(oracle.BIAS):
  folder=ROOT/f'references-local/lm741-reference09/case{index:02d}';root=list(map(float,(folder/'root.txt').read_text().splitlines()[1].split()))[1:]
  c=v['commands'][index]
  if any(abs(x-y)>oracle.GATES['dc_constraint_absolute'] for x,y in zip(root[:5],bias)) or len(root)!=42 or c['exit_code'] or (folder/'probe.log').read_text()!=c['stdout']+c['stderr'] or sha(folder/'probe.cir')!=c['deck_sha256']:raise ValueError('complete raw fresh root')
  with localcontext() as ctx:
   ctx.prec=100;r=oracle.reference(root[:37],0.,[0.]*5)
  if max(map(abs,r[5:26]))>1e-11 or max(map(abs,r[26:37]))>1e-11 or any(abs(r[k]-root[37+k])>2e-14+1e-7*abs(root[37+k]) for k in range(5)):raise ValueError('unchanged independent root gates')
  roots.append(root)
 if roots!=v['roots'] or v['new_spice_processes']!=6 or v['unchanged_replays']:raise ValueError('six admitted fresh roots')
 text=oracle.table(oracle.fixtures(roots));tp=ROOT/'evidence/voice_lm741_vectors09.txt';rp=ROOT/'evidence/voice_lm741_roots09.txt'
 if tp.read_bytes()!=text.encode() or sha(tp)!=v['text_sha256'] or rp.read_bytes()!=oracle.table(roots).encode() or sha(rp)!=v['roots_text_sha256']:raise ValueError('exact Decimal100 replay')
 if tp.read_bytes()!=(ROOT/'evidence/voice_lm741_vectors08.txt').read_bytes() or rp.read_bytes()!=(ROOT/'evidence/voice_lm741_roots08.txt').read_bytes():raise ValueError('syntax-only repair numerical identity')
 refs=[read(ROOT/f'evidence/voice_lm741_reference{k:02d}.json') for k in range(1,9)]
 if refs[0]['source_sha256']!=refs[1]['source_sha256'] or refs[0]['error']!=refs[1]['error'] or any(t['commands'] for t in refs[:2]):raise ValueError('unchanged inventory replay')
 for index,receipt in enumerate(refs,1):
  if receipt['source_sha256']!=receipt['source_sha256_after'] or receipt['private_input_sha256']!=receipt['private_input_sha256_after'] or receipt['gates']!=oracle.GATES:raise ValueError('historical fixed inputs/gates')
  if index<8:
   if receipt['passed']:raise ValueError('failed extraction mislabeled')
   for n,text in receipt['failed_source_text'].items():
    if hashlib.sha256(text.encode()).hexdigest()!=receipt['source_sha256'][n]:raise ValueError('failure source exact bytes')
   if index>=3:
    if len(receipt['commands'])!=1 or len(receipt['unchanged_replays'])!=1 or receipt['commands'][0]['command']!=receipt['unchanged_replays'][0]['command']:raise ValueError('unchanged failed process replay')
  elif not receipt['passed']:raise ValueError('pre-syntax oracle admission')
  for item in receipt['outputs']:
   path=ROOT/item['path']
   if sha(path)!=item['sha256'] or path.stat().st_size!=item['bytes']:raise ValueError('failed original output preserved')
   private[item['path']]=item['sha256']
 failed=read(ROOT/'evidence/voice_lm741_native01.json')
 if failed['passed'] or len(failed['commands'])!=1 or len(failed['unchanged_replays'])!=1 or failed['commands'][0]['command']!=failed['unchanged_replays'][0]['command'] or not all(c['exit_code'] for c in failed['commands']+failed['unchanged_replays']):raise ValueError('compile failure and exact replay')
 for n,text in failed['failed_source_text'].items():
  if hashlib.sha256(text.encode()).hexdigest()!=failed['source_sha256'][n]:raise ValueError('failed native sources preserved')
 for name in ['diagnostic.cir','diagnostic.log']:
  p=ROOT/'references-local/lm741-reference03/case00'/name;private[p.relative_to(ROOT).as_posix()]=sha(p)
 for number in (1,2):
  failure=read(ROOT/f'evidence/voice_lm741_admission_failure{number:02d}.json')
  if hashlib.sha256(failure['source_text'].encode()).hexdigest()!=failure['source_sha256'] or len(failure['unchanged_command_runs'])!=2 or not all(c['exit_code'] for c in failure['unchanged_command_runs']):raise ValueError('audit failure preserved and replayed')
 compiler=a['compiler']
 if sha(Path(compiler['path']))!=compiler['sha256'] or a['compiler_sha256_after']!=compiler['sha256'] or a['unchanged_replays'] or len(a['outputs'])!=3:raise ValueError('compiler/outputs identity')
 if [c['kind'] for c in a['commands']]!=['compile','compile','test','compile','test'] or any(c['exit_code'] for c in a['commands']):raise ValueError('full production commands')
 tests='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',tests)!=['3','1'] or tests.count('LM741_ALLOCATION,stamps=10000,allocations=0')!=1:raise ValueError('four executed tests and isolated zero heap')
 m=re.search(r'LM741_ORACLE,rows=60,spice=6,max_kcl_a=([^,\s]+),max_constraint_v=([^,\s]+),max_jac_kcl=([^,\s]+),max_jac_constraint=([^,\s]+),max_port_a=([^,\s]+)',tests)
 if not m:raise ValueError('captured maxima')
 maxima=dict(zip(['kcl_a','constraint_v','jacobian_kcl','jacobian_constraint','port_a'],map(float,m.groups())))
 if any(not math.isfinite(x) or x<0 for x in maxima.values()):raise ValueError('finite maxima')
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('private inherited/measured input changed '+n)
 if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/oracle.EXE)!=q['official_executable_sha256']:raise ValueError('prior audio/executable')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
 names=sorted(set(q['source_sha256'])|{qp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 local=[]
 for name in (*DOCS,'docs/VCO_741_NATIVO_PROTOCOLO.md','docs/VCO_741_NATIVO_RESULTADOS.md'):
  p=ROOT/name
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve()
   if target!=out.resolve() and not target.exists():raise ValueError('missing publication target '+link)
   local.append(target.relative_to(ROOT).as_posix())
 if sources!={n:sha(ROOT/n) for n in names}:raise ValueError('publication changed during validation')
 out.write_text(json.dumps(dict(schema='rf-d/lm741-full-stamp-release/v1',passed=True,base_commit=BASE,previous_qa_sha256=sha(qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,documentation_snapshot_sha256=sha(sp),oracle_sha256=sha(vp),production_sha256=sha(ap),numerical_maxima=maxima,vector_count=60,unknown_count=37,memory_count=5,covered_test_count=209,inherited_test_count=205,native_test_count=4,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,lm741_full_stamp_admitted=True,lm741_native_solver_admitted=False,native_vco_admitted=False,temperature_c=25,tnom_c=25,other_temperatures_admitted=False,checked_local_targets=sorted(set(local)),previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],admitted_spice_case_count=6,new_spice_processes=23,new_audio=False,long_note_admitted_locally=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
 print('LM741 release: 209 covered, four new +205 inherited;',len(sources),'public inputs;',len(private),'private',flush=True)
if __name__=='__main__':main()
