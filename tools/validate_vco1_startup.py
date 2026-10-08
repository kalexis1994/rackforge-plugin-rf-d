"""Admit own startup only; retain complete-cycle rejections and scoped diagnostics."""
import base64,hashlib,json,re,subprocess
from pathlib import Path
from decimal import localcontext
import vco1_newton_reference as ref
from validate_mixer_on_native import native_source_identity
ROOT=ref.ROOT;sha=ref.sha;BASE='3191073143a47f66aaa0a6b4f2627edafad92775'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
EXPORT=b'\npub mod vco1_startup;\n'
ATTRS=b'/crates/rf-d-circuit/src/vco1_startup.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_startup.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_startup_no_alloc.rs text eol=lf\n/tools/vco1_native_trajectory.rs text eol=lf\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def main():
 out=ROOT/'evidence/voice_vco1_startup_tests01.json'
 if out.exists():raise ValueError('preserve release QA')
 qp='evidence/voice_vco1_newton_tests01.json';q=read(qp);a=read('evidence/voice_vco1_startup_native01.json');v=read('evidence/voice_vco1_startup_reference01.json');d=read('evidence/voice_vco1_reset_diagnostics01.json');cycle=read('evidence/voice_vco1_native_cycles01.json');snapshot=read('evidence/voice_vco1_startup_documentation01.json')
 if not all(t['passed'] for t in (q,a,v,d)) or q['covered_test_count']!=220 or cycle['passed'] or d['production_full_cycles_admitted']:raise ValueError('fixed scope/counts')
 if snapshot['previous_qa_sha256']!=sha(ROOT/qp):raise ValueError('snapshot parent')
 for n,h in q['source_sha256'].items():
  if n in DOCS:native_source_identity(n,h,base64.b64decode(snapshot['previous_bytes_base64'][n]))
  elif n in ('crates/rf-d-circuit/src/lib.rs','.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT);native_source_identity(n,h,old)
   if (ROOT/n).read_bytes()!=old+(EXPORT if n.endswith('lib.rs') else ATTRS):raise ValueError('exact additive exports/policies')
  elif sha(ROOT/n)!=h:raise ValueError('inherited protected input '+n)
 private=dict(q['private_input_sha256']);private.update(d['private_input_sha256']);private.update(a['private_input_sha256'])
 # Recover measured old documentation/policy bytes from their retained exact snapshots.
 archive=ROOT/'references-local/vco1-startup-measured-source01';historical=[]
 for t in (a,v,cycle):
  if t['source_sha256']!=t['source_sha256_after']:raise ValueError('changed measurement inputs')
  for n,h in t['source_sha256'].items():
   target=archive/(h+'.blob')
   if not target.exists():
    data=(ROOT/n).read_bytes()
    if hashlib.sha256(data).hexdigest()!=h:raise ValueError('unrecoverable measured source '+n)
    target.write_bytes(data)
   if sha(target)!=h:raise ValueError('measured source version')
   private[target.relative_to(ROOT).as_posix()]=h;historical.append(dict(source_name=n,path=target.relative_to(ROOT).as_posix(),sha256=h))
 for target in archive.iterdir():private[target.relative_to(ROOT).as_posix()]=sha(target)
 if a['private_input_sha256']!=a['private_input_sha256_after'] or a['unchanged_replays'] or v['unchanged_replays'] or len(v['cases'])!=10 or v['gates']!=ref.GATES:raise ValueError('startup measured admission')
 stdout='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',stdout)!=['2','1'] or 'VCO1_STARTUP_ALLOCATION,startups=16,steps=128,allocations=0' not in stdout:raise ValueError('three native tests')
 if any(c['exit_code'] for c in a['commands']) or any('opt-level=2' not in c['command'] for c in a['commands'] if c['kind']=='compile') or sha(Path(a['compiler']['path']))!=a['compiler']['sha256']:raise ValueError('compiler/commands')
 roots={};seeds={}
 for m in re.finditer(r'STARTUP_(ROOT|SEED),([01]),([0-4]),([^\r\n]+)',stdout):(roots if m[1]=='ROOT' else seeds)[(int(m[2]),int(m[3]))]=list(map(float,m[4].split(',')))
 if set(roots)!=set(seeds) or len(roots)!=10:raise ValueError('captured production scenes')
 with localcontext() as ctx:
  ctx.prec=100
  for case in v['cases']:
   key=(case['profile'],case['scene']);root=case['root'];c=case['controls'];f=case['forcing_a'];r,j,g=ref.stamp.reference(root,root,0.,c);r[43]+=f;g-=f
   expected=[.5,500.,[1e-11,100e-12][key[0]],0.,0.,*([-2.1]*6)]
   if key[1]:expected[0]=.26134047;expected[1]=521.31266;expected[7]=[-3.1,-2.1,-1.1,-.1][key[1]-1]
   if c!=expected or case['initial']!=seeds[key] or case['native_root']!=roots[key][1:] or case['native_forcing_a']!=roots[key][0] or not case['passed']:raise ValueError('independent scene identity')
   if max(map(abs,r[:98]))>2e-14 or max(map(abs,r[98:]))>2e-12 or abs(sum(r[:98])+g)>1e-11 or any(abs(x-y)>(2e-7 if k<98 else 2e-10) for k,(x,y) in enumerate(zip(root,case['native_root']))) or abs(f-case['native_forcing_a'])>2e-10:raise ValueError('independent incidence/forcing/ground gates')
 for item in a['outputs']:
  if sha(ROOT/item['path'])!=item['sha256'] or (ROOT/item['path']).stat().st_size!=item['bytes']:raise ValueError('native output identity')
  private[item['path']]=item['sha256']
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('private identity '+n)
 if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/ref.stamp.EXE)!=q['official_executable_sha256']:raise ValueError('old audio/official simulator')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(q['source_sha256'])|{qp}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 local=[]
 for n in (*DOCS,'docs/VCO1_ARRANQUE_PROTOCOLO.md','docs/VCO1_ARRANQUE_RESULTADOS.md'):
  p=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve()
   if target!=out.resolve() and not target.exists():raise ValueError('missing target '+link)
   local.append(target.relative_to(ROOT).as_posix())
 report=dict(schema='rf-d/vco1-own-startup-release/v1',passed=True,base_commit=BASE,previous_qa_sha256=sha(ROOT/qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,historical_source_archive=historical,covered_test_count=223,inherited_test_count=220,native_test_count=3,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,native_own_startup_seed_admitted=True,native_conditioned_dc_admitted=True,calibrated_conditioned_startup_admitted=True,startup_scenes=10,native_full_period_admitted=False,native_reset_event_admitted=False,native_frequency_refinement_admitted=False,calibrated_transient_admitted=False,free_dc_admitted=False,fixed_cycle_bank_rejected=True,substep_probe_production=False,new_spice_processes=0,new_audio=False,temperature_c=25,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],checked_local_targets=sorted(set(local)),long_note_admitted_locally=False,physical_fidelity=False,real_time=False)
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('Own startup QA:223 covered,3 new+220 inherited;',len(sources),'public;',len(private),'private',flush=True)
if __name__=='__main__':main()
