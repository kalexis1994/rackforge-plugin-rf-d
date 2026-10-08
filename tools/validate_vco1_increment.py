"""Publish compensated local roots and independently confirmed temporal rejection."""
import base64,hashlib,json,re,subprocess
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from vco1_newton_reference import ROOT,sha,GATES
import vco1_increment_circuit as oracle
from lm741_reference import table
from validate_mixer_on_native import native_source_identity
BASE='cad6841a4e1398dd01286cd8a08548bbca7e2a11'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
EXPORT=b'\npub mod vco1_increment;\n\npub mod vco1_increment_adaptive;\n'
ATTRS=b'/crates/rf-d-circuit/src/vco1_increment.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_increment.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_increment_no_alloc.rs text eol=lf\n/evidence/voice_vco1_increment*.txt -text\n/crates/rf-d-circuit/src/vco1_increment_adaptive.rs text eol=lf\n/tools/vco1_increment_trajectory.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_increment_adaptive.rs text eol=lf\n/crates/rf-d-circuit/tests/vco1_increment_adaptive_no_alloc.rs text eol=lf\n/tools/vco1_increment_floor.rs text eol=lf\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,message):
 if not ok:raise ValueError(message)
def main():
 out=ROOT/'evidence/voice_vco1_increment_tests01.json';require(not out.exists(),'preserve publication');qp='evidence/voice_vco1_substep_tests02.json';q=read(qp);snapshot=read('evidence/voice_vco1_increment_documentation01.json');v=read('evidence/voice_vco1_increment_reference01.json');first=read('evidence/voice_vco1_increment_native01.json');native=read('evidence/voice_vco1_increment_native02.json');adaptive=read('evidence/voice_vco1_increment_adaptive_native01.json');pre=read('evidence/voice_vco1_increment_cycles01.json');cycle=read('evidence/voice_vco1_increment_cycles02.json');floor=read('evidence/voice_vco1_increment_floor01.json');archive=read('evidence/voice_vco1_increment_archive01.json');stack=read('references-local/vco1-increment-stack01/receipt.json')
 require(q['passed'] and q['covered_test_count']==229 and snapshot['previous_qa_sha256']==sha(ROOT/qp),'inherited release')
 for n,h in q['source_sha256'].items():
  if n in DOCS:native_source_identity(n,h,base64.b64decode(snapshot['previous_bytes_base64'][n]))
  elif n in ('crates/rf-d-circuit/src/lib.rs','.gitattributes'):
   old=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT);native_source_identity(n,h,old);require((ROOT/n).read_bytes()==old+(EXPORT if n.endswith('lib.rs') else ATTRS),'exact additive publication')
  else:require(sha(ROOT/n)==h,'protected input '+n)
 require(v['passed'] and v['rows']==50 and v['columns']==1351 and v['sum_rows']==110 and not v['native_current_roots_used'] and not v['unchanged_replays'] and v['gates']==GATES,'independent fixture admission')
 private=dict(q['private_input_sha256']);versions={}
 for item in archive['versions']:
  require(sha(ROOT/item['path'])==item['sha256'],'measured source archive');private[item['path']]=item['sha256'];versions[(item['receipt'],item['source_name'])]=item['sha256']
 receipts=('evidence/voice_vco1_increment_reference01.json','evidence/voice_vco1_increment_native01.json','evidence/voice_vco1_increment_native02.json','evidence/voice_vco1_increment_adaptive_native01.json','evidence/voice_vco1_increment_cycles01.json','evidence/voice_vco1_increment_cycles02.json','evidence/voice_vco1_increment_floor01.json','references-local/vco1-increment-stack01/receipt.json')
 for rp in receipts:
  t=read(rp)
  if 'source_sha256_after' in t:require(t['source_sha256']==t['source_sha256_after'],'changed measured inputs '+rp)
  for n,h in t['source_sha256'].items():require(versions.get((rp,n))==h,'archived measured input '+rp+' '+n)
  if 'private_input_sha256_after' in t:require(t['private_input_sha256']==t['private_input_sha256_after'],'private inputs changed')
  private.update(t.get('private_input_sha256',{}))
  for item in t.get('outputs',[]):require(sha(ROOT/item['path'])==item['sha256'] and (ROOT/item['path']).stat().st_size==item['bytes'],'retained output')
 for t,marker in ((native,'VCO1_INCREMENT_ALLOCATION,recoveries=16,steps=128,allocations=0'),(adaptive,'VCO1_INCREMENT_ADAPTIVE_ALLOCATION,candidates=128,allocations=0')):
  stdout='\n'.join(cmd['stdout'] for cmd in t['commands'] if cmd['kind']=='test');require(t['passed'] and not t['unchanged_replays'] and all(cmd['exit_code']==0 for cmd in t['commands']),'native tests passed');require(re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',stdout)==['2','1'] and marker in stdout,'six executed tests');require(t['test_thread_stack_bytes']==8388608 and t['main_stack_reserve_bytes']==8388608 and sha(Path(t['compiler']['path']))==t['compiler']['sha256']==t['compiler_sha256_after'],'compiler/stack');require(all('opt-level=2' in cmd['command'] and 'link-arg=-Wl,--stack,8388608' in cmd['command'] for cmd in t['commands'] if cmd['kind']=='compile'),'optimized laboratory build')
 require(not first['passed'] and len(first['unchanged_replays'])==1 and first['commands'][-1]['exit_code']!=0 and re.sub(r'\(\d+\) has overflowed its stack','(thread id) has overflowed its stack',first['commands'][-1]['stderr'])==re.sub(r'\(\d+\) has overflowed its stack','(thread id) has overflowed its stack',first['unchanged_replays'][0]['stderr']) and first['commands'][-1]['exit_code']==first['unchanged_replays'][0]['exit_code'],'preserved stack failure')
 require(not pre['passed'] and not pre['resource_passed'] and not pre['commands'] and not pre['cases'],'resource-only preflight')
 require(not cycle['passed'] and cycle['resource_passed'] and not cycle['cases'] and len(cycle['unchanged_replays'])==1,'trajectory rejection');replay=cycle['unchanged_replays'][0];require(cycle['commands'][-1]['exit_code']==replay['exit_code']!=0 and cycle['commands'][-1]['stderr']==replay['stderr'] and replay['source_sha256']==cycle['source_sha256'] and replay['export_sha256']==cycle['failed_export']['sha256'],'byte-identical rejection replay')
 raw=np.memmap(ROOT/cycle['failed_export']['path'],dtype='<f8').reshape(-1,412);require(len(raw)==15899 and raw[0,0]==0. and raw[-1,0]==79768392*125e-9/4096,'prefix clock');require(sha(ROOT/cycle['failed_export']['path'])==cycle['failed_export']['sha256'],'original prefix identity')
 hi=raw[:,1:135];lo=raw[:,135:269];require(np.isfinite(raw).all() and np.array_equal(hi+lo,hi) and np.all(np.abs(lo)<=np.abs(np.spacing(hi))/2),'complete normalized prefix memory');require(np.max(np.abs(hi[:,:98]))<=40 and np.max(np.abs(hi[:,98:]))<=1 and np.max(raw[:,407:409])<=1,'all accepted prefix gates');ticks=raw[:,0]/(125e-9/4096);require(np.max(np.abs(ticks-np.round(ticks)))<=2e-6 and np.max(np.abs(np.diff(ticks)-raw[1:,411]))<=2e-6,'all actual intervals');require(np.min(raw[1:,411])>=1 and np.max(raw[1:,411])<=16384,'prefix interval domain')
 aa=hi[1:];bb=-hi[:-1];ss=aa+bb;vv=ss-aa;ee=(aa-(ss-vv))+(bb-vv);difference=ss+(ee+(lo[1:]-lo[:-1]));delta=raw[1:,269:403];require(np.all(np.abs(difference-delta)<=np.abs(delta)*2e-15+1e-28),'increment transport');history=list(map(float,(ROOT/'evidence/voice_vco1_increment_floor_history01.txt').read_text().split()));require(history==raw[-1,1:269].tolist(),'full failure history')
 pattern=[tuple(map(int,l.split())) for l in (ROOT/'evidence/voice_vco1_stamp_pattern08.txt').read_text().splitlines()];rows=[]
 with localcontext() as ctx:
  ctx.prec=100
  for case in v['cases']:
   require(case['passed'],'all 50 roots');c=case['controls'];old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(case['previous_high'],case['previous_low'])];now=[x+Decimal.from_float(d) for x,d in zip(old,case['delta'])];rr,j,g=oracle.reference_decimal(now,old,case['dt_s'],c);root=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(case['root_high'],case['root_low'])];res,jj,gg=oracle.reference_decimal(root,old,case['dt_s'],c);require(max(map(abs,res[:98]))<=Decimal.from_float(2e-14) and max(map(abs,res[98:]))<=Decimal.from_float(2e-12) and abs(sum(res[:98])+gg)<=Decimal.from_float(1e-11),'independent root incidence');require(all(j[a][b]==0 for a in range(134) for b in range(134) if (a,b) not in pattern),'full sparse pattern');rows.append([*c,*case['previous_high'],*case['previous_low'],*case['delta'],case['dt_s'],*map(float,rr),float(g),*[float(j[a][b]) for a,b in pattern],*case['root_high'],*case['root_low']])
  require((ROOT/'evidence/voice_vco1_increment_vectors01.txt').read_text()==table(rows) and sha(ROOT/'evidence/voice_vco1_increment_vectors01.txt')==v['text_sha256'] and sha(ROOT/'evidence/voice_vco1_increment_sum01.txt')==v['sum_sha256'] and sha(ROOT/'evidence/voice_vco1_stamp_pattern08.txt')==v['pattern_sha256'],'fixture byte reconstruction')
  sums=[list(map(float,line.split())) for line in (ROOT/'evidence/voice_vco1_increment_sum01.txt').read_text().splitlines()]
  require(len(sums)==110 and all(Decimal.from_float(a)+Decimal.from_float(b)==Decimal.from_float(h)+Decimal.from_float(l) for a,b,h,l in sums),'exact TwoSum fixture')
  c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)];old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(history[:134],history[134:])];roots={n:list(map(Decimal,row['independent_decimal'])) for n,row in floor['roots'].items()}
  for n,row in floor['roots'].items():
   rr,j,g=oracle.reference_decimal(roots[n],roots['mid'] if n=='end' else old,(2 if n=='full' else 1)*125e-9/4096,c);require(row['passed'] and max(map(abs,rr[:98]))<=Decimal.from_float(2e-14) and max(map(abs,rr[98:]))<=Decimal.from_float(2e-12) and abs(sum(rr[:98])+g)<=Decimal.from_float(1e-11),'reset independent KCL')
  error=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(roots['full'],roots['end']))];require(floor['passed'] and not floor['independent_local_error_admitted'] and max(range(134),key=lambda k:error[k])==50 and 1<float(max(error))<1.01,'confirmed temporal rejection')
 for folder in ('vco1-increment-native01','vco1-increment-native02','vco1-increment-adaptive-native01','vco1-increment-reference01','vco1-increment-cycles02','vco1-increment-floor01','vco1-increment-stack01','vco1-increment-measured-source01'):
  for p in (ROOT/'references-local'/folder).rglob('*'):
   if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
 for n,h in private.items():require(sha(ROOT/n)==h,'private corpus '+n)
 require(stack['exit_code']==0 and sha(Path(stack['compiler']['path']))==stack['compiler']['sha256'],'stack inspection compiler');require(sha(ROOT/q['previous_audio']['path'])==q['previous_audio']['sha256'],'previous audio')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(q['source_sha256'])|{qp}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 for n in (*DOCS,'docs/VCO1_INCREMENTOS_PROTOCOLO.md','docs/VCO1_INCREMENTOS_ALMACENAMIENTO.md','docs/VCO1_INCREMENTOS_RESET_PROTOCOLO.md','docs/VCO1_INCREMENTOS_RESULTADOS.md'):
  p=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve();require(target==out.resolve() or target.exists(),'local doc link '+link)
 report=dict(schema='rf-d/compensated-increment-release/v1',passed=True,base_commit=BASE,previous_qa_sha256=sha(ROOT/qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,covered_test_count=235,inherited_test_count=229,native_test_count=6,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,compensated_stamp_admitted=True,compensated_conditional_roots_admitted=50,all_jacobian_entries=897800,old_precision_floor_recovered_locally=True,step_doubling_contract_admitted=True,step_doubling_full_trajectory_admitted=False,adaptive_campaign_rejected=True,accepted_prefix_steps=15898,limiting_node='SCHMITT_Q6_COLLECTOR',independent_local_error_ratio=floor['independent_limit']['error_ratio'],native_full_period_admitted=False,native_frequency_refinement_admitted=False,calibrated_transient_admitted=False,free_dc_admitted=False,new_spice_processes=0,new_audio=False,temperature_c=25,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],long_note_admitted_locally=False,physical_fidelity=False,real_time=False,lab_stack_bytes=8388608)
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('Increment release:235 covered,6 new+229 inherited;',len(sources),'public;',len(private),'private',flush=True)
if __name__=='__main__':main()
