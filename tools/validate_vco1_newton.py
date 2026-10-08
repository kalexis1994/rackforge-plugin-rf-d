"""Admit the coupled short VCO1 solve; own initial seed and full periods remain open."""
import base64,hashlib,json,math,re,subprocess
from pathlib import Path
import vco1_newton_reference as oracle
from validate_mixer_on_native import native_source_identity
ROOT=oracle.ROOT;sha=oracle.sha;BASE='e92b8ee0302ee15d1780f6ef9513b71910d6216a'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md');LIB='crates/rf-d-circuit/src/lib.rs'
EXPORT=b'\npub mod vco1_newton;\n'
ATTRS=b'/crates/rf-d-circuit/src/vco1_newton.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_newton.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_newton_no_alloc.rs text eol=lf\n/evidence/voice_vco1_newton*.txt -text\n'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
 out=ROOT/'evidence/voice_vco1_newton_tests01.json'
 if out.exists():raise ValueError('preserve release')
 qp=ROOT/'evidence/voice_vco1_stamp_tests01.json';q=read(qp);vp=ROOT/'evidence/voice_vco1_newton_reference01.json';v=read(vp);ap=ROOT/'evidence/voice_vco1_newton_native01.json';a=read(ap)
 if not all(t['passed'] for t in (q,v,a)) or q['covered_test_count']!=217:raise ValueError('217 inherited plus three new')
 snapshot=read(ROOT/'evidence/voice_vco1_newton_documentation01.json')
 if snapshot['previous_qa_sha256']!=sha(qp) or set(snapshot['previous_bytes_base64'])!=set(DOCS):raise ValueError('documentation snapshot')
 for n,h in q['source_sha256'].items():
  if n in DOCS:native_source_identity(n,h,base64.b64decode(snapshot['previous_bytes_base64'][n]))
  elif n in (LIB,'.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT);native_source_identity(n,h,old)
   if (ROOT/n).read_bytes()!=old+(EXPORT if n==LIB else ATTRS):raise ValueError('exact new export/policy')
  elif sha(ROOT/n)!=h:raise ValueError('inherited input '+n)
 for t in (v,a):
  if t['source_sha256']!=t['source_sha256_after'] or t['private_input_sha256']!=t['private_input_sha256_after'] or t['unchanged_replays']:raise ValueError('measured attempt changed/failed')
  for n,h in t['source_sha256'].items():
   if sha(ROOT/n)!=h:raise ValueError('latest measured source '+n)
 if v['gates']!=oracle.GATES or v['trajectory_rows']!=224 or v['profiles']!=6 or v['startup_rows']!=2 or v['duration_s']!=8e-6 or not v['startup_seeds_imported_from_original_spice'] or v['native_own_startup_seed_admitted'] or v['native_full_period_admitted']:raise ValueError('fixed scope/gates')
 seedp=ROOT/'evidence/voice_vco1_stamp_startup08.txt';seeds=[list(map(float,l.split())) for l in seedp.read_text().splitlines()]
 dc,tr,it=oracle.fixtures(seeds,lambda s:print('QA '+s,flush=True));dcp=ROOT/'evidence/voice_vco1_newton_startup01.txt';trp=ROOT/'evidence/voice_vco1_newton_trajectory01.txt'
 if dcp.read_text()!=oracle.stamp.op.table(dc) or trp.read_text()!=oracle.stamp.op.table(tr) or sha(dcp)!=v['startup_text_sha256'] or sha(trp)!=v['trajectory_text_sha256'] or it!=v['max_independent_iterations']:raise ValueError('independent complete-root reconstruction')
 groups={}
 for row in tr:
  if len(row)!=147 or any(not math.isfinite(x) for x in row):raise ValueError('finite trajectory shape')
  key=(row[2],row[11]);groups.setdefault(key,[]).append(int(row[12]))
 if len(groups)!=6 or any(indices!=list(range(1,round(8e-6/k[1])+1)) for k,indices in groups.items()):raise ValueError('whole short coverage')
 compiler=a['compiler'];stdout='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 if sha(Path(compiler['path']))!=compiler['sha256'] or a['compiler_sha256_after']!=compiler['sha256'] or any(c['exit_code'] for c in a['commands']) or len(a['outputs'])!=3:raise ValueError('native compiler/outputs')
 if any('opt-level=2' not in c['command'] for c in a['commands'] if c['kind']=='compile'):raise ValueError('fixed optimized build')
 if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',stdout)!=['2','1'] or stdout.count('VCO1_NEWTON_ALLOCATION,solves=128,allocations=0')!=1:raise ValueError('three executed tests and no heap')
 m=re.search(r'VCO1_NEWTON,dc=2,profiles=6,steps=224,max_node_v=([^,\s]+),max_branch_a=([^,\s]+),max_iterations=(\d+),max_trials=(\d+)',stdout)
 if not m:raise ValueError('full captured numerical maxima')
 maxima=dict(zip(['node_v','branch_a','iterations','trials'],map(float,m.groups())))
 if maxima['node_v']>2e-7 or maxima['branch_a']>2e-10 or maxima['iterations']>64:raise ValueError('native comparison gates')
 private=dict(q['private_input_sha256']);private.update(v['private_input_sha256']);private.update(a['private_input_sha256'])
 for item in a['outputs']:
  p=ROOT/item['path']
  if not p.resolve().is_relative_to((ROOT/'references-local').resolve()) or sha(p)!=item['sha256'] or p.stat().st_size!=item['bytes']:raise ValueError('native retained output')
  private[item['path']]=item['sha256']
 pool={h:n for t in (v,a) for n,h in t['source_sha256'].items()};folder=ROOT/'references-local/vco1-newton-source-identity01'
 if folder.exists():raise ValueError('preserve measured-source archive')
 folder.mkdir();archive=[]
 for h,n in sorted(pool.items()):
  data=(ROOT/n).read_bytes()
  if hashlib.sha256(data).hexdigest()!=h:raise ValueError('measured source before archive')
  p=folder/(h+'.blob');p.write_bytes(data);item=dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size,source_name=n);archive.append(item);private[item['path']]=item['sha256']
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('private corpus identity '+n)
 if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/oracle.stamp.EXE)!=q['official_executable_sha256']:raise ValueError('previous audio/official simulator')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(q['source_sha256'])|{qp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 local=[]
 for n in (*DOCS,'docs/VCO1_NEWTON_PROTOCOLO.md','docs/VCO1_NEWTON_RESULTADOS.md'):
  p=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve()
   if target!=out.resolve() and not target.exists():raise ValueError('missing publication '+link)
   local.append(target.relative_to(ROOT).as_posix())
 if sources!={n:sha(ROOT/n) for n in names}:raise ValueError('publication changed')
 report=dict(schema='rf-d/vco1-coupled-short-release/v1',passed=True,base_commit=BASE,previous_qa_sha256=sha(qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,historical_source_archive=archive,covered_test_count=220,inherited_test_count=217,native_test_count=3,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,native_coupled_newton_admitted=True,native_conditioned_dc_admitted=True,native_short_euler_continuation_admitted=True,trajectory_profile_count=6,trajectory_step_count=224,trajectory_duration_s=8e-6,native_own_startup_seed_admitted=False,native_full_period_admitted=False,native_reset_event_admitted=False,native_frequency_refinement_admitted=False,calibrated_startup_admitted=False,free_dc_admitted=False,numerical_maxima=maxima,new_spice_processes=0,new_audio=False,temperature_c=25,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],checked_local_targets=sorted(set(local)),long_note_admitted_locally=False,physical_fidelity=False,real_time=False)
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('VCO1 coupled Newton: 220 covered, three new+217 inherited;',len(sources),'public;',len(private),'private;',len(archive),'measured source versions',flush=True)
if __name__=='__main__':main()
