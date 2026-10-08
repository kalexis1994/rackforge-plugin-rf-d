"""Publish short stamps/conditional roots and controller contracts, retaining rejects."""
import base64,hashlib,json,re,subprocess
from decimal import localcontext
from pathlib import Path
import numpy as np
import vco1_newton_reference as ref
from validate_mixer_on_native import native_source_identity
ROOT=ref.ROOT;sha=ref.sha;BASE='d6f4159365f9a4046bc9d1694c3c1f25413b3811';DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
EXPORT=b'\npub mod vco1_substep;\n\npub mod vco1_adaptive;\n'
ATTRS=b'/crates/rf-d-circuit/src/vco1_substep.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_substep.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_substep_no_alloc.rs text eol=lf\n/evidence/voice_vco1_substep*.txt -text\n/crates/rf-d-circuit/src/vco1_adaptive.rs text eol=lf\n/tools/vco1_adaptive_trajectory.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_adaptive.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_adaptive_no_alloc.rs text eol=lf\n/evidence/voice_vco1_adaptive*.txt -text\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def main():
 out=ROOT/'evidence/voice_vco1_substep_tests02.json'
 if out.exists():raise ValueError('preserve substep publication')
 qp='evidence/voice_vco1_startup_tests01.json';q=read(qp);v1=read('evidence/voice_vco1_substep_reference01.json');v=read('evidence/voice_vco1_substep_reference02.json');a=read('evidence/voice_vco1_substep_native01.json');b=read('evidence/voice_vco1_adaptive_native01.json');cycle=read('evidence/voice_vco1_adaptive_cycles01.json');diag=read('evidence/voice_vco1_substep_rounding01.json');snapshot=read('evidence/voice_vco1_substep_documentation01.json')
 if not all(t['passed'] for t in (q,a,b,diag)) or q['covered_test_count']!=223 or v1['passed'] or v['passed'] or not v['stamp_bank_complete'] or v['all_roots_admitted'] or cycle['passed'] or cycle['cases']:raise ValueError('frozen admissions and rejects')
 if snapshot['previous_qa_sha256']!=sha(ROOT/qp):raise ValueError('previous documentation')
 for n,h in q['source_sha256'].items():
  if n in DOCS:native_source_identity(n,h,base64.b64decode(snapshot['previous_bytes_base64'][n]))
  elif n in ('crates/rf-d-circuit/src/lib.rs','.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT);native_source_identity(n,h,old)
   if (ROOT/n).read_bytes()!=old+(EXPORT if n.endswith('lib.rs') else ATTRS):raise ValueError('exact additive publication')
  elif sha(ROOT/n)!=h:raise ValueError('protected input '+n)
 old_solver=(ROOT/'crates/rf-d-circuit/src/vco1_newton.rs').read_text(encoding='utf8');new_solver=(ROOT/'crates/rf-d-circuit/src/vco1_substep.rs').read_text(encoding='utf8')
 if new_solver[new_solver.index('fn system'):]!=old_solver[old_solver.index('fn system'):].replace('vco1_stamp::linearize(x,c,m)','linearize(x,c,m)'):raise ValueError('same Newton algorithm')
 private=dict(q['private_input_sha256']);private.update(diag['private_input_sha256']);archive=ROOT/'references-local/vco1-substep-measured-source01';versions=[]
 for t in (v1,v,a,b,cycle):
  if t['source_sha256']!=t['source_sha256_after']:raise ValueError('changed measured input')
  for n,h in t['source_sha256'].items():
   target=archive/(h+'.blob')
   if not target.exists():
    data=(ROOT/n).read_bytes()
    if hashlib.sha256(data).hexdigest()!=h:data=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
    if hashlib.sha256(data).hexdigest()!=h:raise ValueError('unrecoverable measured source '+n)
    target.write_bytes(data)
   if sha(target)!=h:raise ValueError('measured source archive')
   private[target.relative_to(ROOT).as_posix()]=h;versions.append(dict(source_name=n,path=target.relative_to(ROOT).as_posix(),sha256=h))
  private.update(t.get('private_input_sha256',{}))
 for folder in ('vco1-substep-measured-source01','vco1-substep-reference01','vco1-substep-reference02','vco1-substep-native01','vco1-adaptive-native01','vco1-adaptive-cycles01'):
  for p in (ROOT/'references-local'/folder).rglob('*'):
   if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
 for t,marker in ((a,'VCO1_SUBSTEP_ALLOCATION,stamps=100,steps=128,allocations=0'),(b,'VCO1_ADAPTIVE_ALLOCATION,candidates=128,allocations=0')):
  stdout='\n'.join(c['stdout'] for c in t['commands'] if c['kind']=='test')
  if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',stdout)!=['2','1'] or marker not in stdout or t['unchanged_replays'] or any(c['exit_code'] for c in t['commands']):raise ValueError('six executed native tests')
  if sha(Path(t['compiler']['path']))!=t['compiler']['sha256'] or t['compiler_sha256_after']!=t['compiler']['sha256'] or any('opt-level=2' not in c['command'] for c in t['commands'] if c['kind']=='compile'):raise ValueError('pinned optimized compiler')
  for item in t['outputs']:
   if sha(ROOT/item['path'])!=item['sha256'] or (ROOT/item['path']).stat().st_size!=item['bytes']:raise ValueError('native retained output')
 if v['gates']!=ref.GATES or len(v['cases'])!=48 or sum(c['passed'] for c in v['cases'])!=28 or len(v['unchanged_replays'])!=20 or v1['cases'][-1]['error']!=v1['unchanged_replays'][0]['error']:raise ValueError('conditional independent roots')
 pattern=[tuple(map(int,l.split())) for l in (ROOT/'evidence/voice_vco1_stamp_pattern08.txt').read_text().splitlines()];vectors=[]
 with localcontext() as ctx:
  ctx.prec=100
  for case in v['cases']:
   c=case['controls'];x=case['stamp_state'];old=case['previous'];dt=case['dt_s'];r,j,g=ref.stamp.reference(x,old,dt,c)
   if dt!=125e-9/(2**case['power']) or not 1<=case['power']<=12:raise ValueError('dyadic interval')
   root=case['root'] if case['passed'] else [0.]*134
   if case['passed']:
    rr,jj,gg=ref.stamp.reference(root,old,dt,c)
    if max(map(abs,rr[:98]))>2e-14 or max(map(abs,rr[98:]))>2e-12 or abs(sum(rr[:98])+gg)>1e-11:raise ValueError('accepted independent root incidence')
   else:
    match=[p for p in v['unchanged_replays'] if (p['c4_pf'],p['scene'],p['power'])==(case['c4_pf'],case['history_scene'],case['power'])]
    if len(match)!=1 or match[0]['error']!=case['error'] or match[0]['source_sha256']!=v['source_sha256']:raise ValueError('rejected tuple unchanged replay')
   vectors.append([*c,*x,*old,dt,*r,g,*[j[aa][bb] for aa,bb in pattern],*root])
 text=ROOT/'evidence/voice_vco1_substep_vectors02.txt'
 if text.read_text()!=ref.stamp.op.table(vectors) or sha(text)!=v['text_sha256'] or sha(ROOT/'evidence/voice_vco1_stamp_pattern08.txt')!=v['pattern_sha256']:raise ValueError('complete stamp reconstruction')
 # Prefix remains incomplete, replayed with byte-identical state exports.
 if len(cycle['unchanged_replays'])!=1 or cycle['commands'][-1]['exit_code']==0 or cycle['unchanged_replays'][0]['exit_code']!=cycle['commands'][-1]['exit_code'] or cycle['unchanged_replays'][0]['export_sha256']!=cycle['failed_export']['sha256']:raise ValueError('adaptive failure replay')
 raw=np.memmap(ROOT/cycle['failed_export']['path'],dtype='<f8',mode='r').reshape(-1,143);history=list(map(float,(ROOT/'evidence/voice_vco1_adaptive_failure_history01.txt').read_text().split()))
 if len(raw)!=7521 or raw[-1,0]!=38799168*(125e-9/4096) or history!=raw[-1,1:135].tolist() or not diag['update_rounds_to_same_value'] or not diag['source_replay_identical'] or abs(diag['last_residual_a'])<=1e-13 or abs(diag['newton_correction_v'])>=diag['node_ulp_v']/2:raise ValueError('temporal floor context')
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('private corpus identity '+n)
 if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/ref.stamp.EXE)!=q['official_executable_sha256']:raise ValueError('prior media/compiler')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(q['source_sha256'])|{qp}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 for n in (*DOCS,'docs/VCO1_SUBPASOS_PROTOCOLO.md','docs/VCO1_SUBPASOS_RESULTADOS.md'):
  p=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve()
   if target!=out.resolve() and not target.exists():raise ValueError('missing local link '+link)
 report=dict(schema='rf-d/vco1-short-step-contract-release/v1',passed=True,base_commit=BASE,superseded_publication_audit='evidence/voice_vco1_substep_tests01.json',previous_qa_sha256=sha(ROOT/qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,historical_source_archive=versions,covered_test_count=229,inherited_test_count=223,native_test_count=6,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,native_own_startup_seed_admitted=True,native_short_stamp_admitted=True,short_stamp_rows=48,all_jacobian_entries=861888,conditional_short_roots_admitted=28,independent_short_roots_rejected=20,entire_short_root_domain_admitted=False,step_doubling_contract_admitted=True,step_doubling_full_trajectory_admitted=False,adaptive_campaign_rejected=True,native_full_period_admitted=False,native_frequency_refinement_admitted=False,calibrated_transient_admitted=False,free_dc_admitted=False,new_spice_processes=0,new_audio=False,temperature_c=25,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],long_note_admitted_locally=False,physical_fidelity=False,real_time=False)
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('Substeps/control QA:229 covered,6 new+223 inherited;',len(sources),'public;',len(private),'private',flush=True)
if __name__=='__main__':main()
