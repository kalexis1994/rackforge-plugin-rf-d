"""Release charge-form lab integration and local descriptor with explicit rejects."""
import base64,hashlib,json,re,subprocess,sys
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_sdirk_reference as ref
from vco1_newton_reference import ROOT,sha
from validate_mixer_on_native import native_source_identity
BASE='5d073dd0a31d45209bf8f042ece440febd0e53f1'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
ATTRS=b'/tools/vco1_sdirk_kernel.rs text eol=lf\n/tools/vco1_sdirk_runner.rs text eol=lf\n/tools/vco1_sdirk_runner4.rs text eol=lf\n'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,msg):
 if not ok:raise ValueError(msg)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def main():
 out=ROOT/'evidence/voice_vco1_sdirk_tests01.json';require(not out.exists(),'preserve publication');qp='evidence/voice_vco1_reset_grid_tests01.json';q=read(qp);snapshot=read('evidence/voice_vco1_sdirk_documentation01.json');p1=read('evidence/voice_vco1_sdirk_probe01.json');p4=read('evidence/voice_vco1_sdirk_probe4_01.json');f1=read('evidence/voice_vco1_sdirk_floor01.json');f4=read('evidence/voice_vco1_sdirk_floor4_01.json');m1=read('evidence/voice_vco1_reset_modes01.json');m2=read('evidence/voice_vco1_reset_modes02.json');private=dict(q['private_input_sha256']);archive=ROOT/'references-local/vco1-sdirk-measured-source01';archive.mkdir(exist_ok=True);blobs={p.stem:p for p in (ROOT/'references-local').rglob('*.blob')}
 require(q['passed'] and q['covered_test_count']==235 and sha(ROOT/qp)==snapshot['previous_qa_sha256'],'inherited QA')
 for n,h in q['source_sha256'].items():
  if n in DOCS or n=='.gitattributes':
   old=base64.b64decode(snapshot['previous_bytes_base64'][n]);native_source_identity(n,h,old)
   if n=='.gitattributes':require((ROOT/n).read_bytes()==old+ATTRS,'only LF policy append')
  else:require(sha(ROOT/n)==h,'protected input '+n)
 for t in (p1,p4,f1,f4,m1,m2):
  require(t['source_sha256']==t['source_sha256_after'] and t['private_input_sha256']==t['private_input_sha256_after'],'measured identity')
  for n,h in t['source_sha256'].items():
   target=archive/(h+'.blob')
   if not target.exists():
    b=(ROOT/n).read_bytes()
    if hashlib.sha256(b).hexdigest()!=h:
     if h in blobs:b=blobs[h].read_bytes()
     elif n in snapshot['previous_bytes_base64']:b=base64.b64decode(snapshot['previous_bytes_base64'][n])
     else:b=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
    require(hashlib.sha256(b).hexdigest()==h,'measured source bytes '+n);target.write_bytes(b)
   require(sha(target)==h,'archive identity');private[target.relative_to(ROOT).as_posix()]=h
  private.update(t['private_input_sha256'])
  for item in t.get('outputs',[]):require(sha(ROOT/item['path'])==item['sha256'] and (ROOT/item['path']).stat().st_size==item['bytes'],'retained output')
 require((ROOT/'tools/vco1_sdirk_runner4.rs').read_text()==(ROOT/'tools/vco1_sdirk_runner.rs').read_text().replace('if ticks<=16','if ticks<=8'),'only controller minimum changed')
 for folder in ('vco1-sdirk-probe01','vco1-sdirk-probe4-01','vco1-sdirk-floor01','vco1-sdirk-floor4-01'):
  w=ROOT/'references-local'/folder
  for n in ('fine.rs','linear.rs','vco1_stamp_data.rs'):require(sha(w/n)==sha(ROOT/'references-local/vco1-reset-grid02'/n),'same inherited kernel/data/elimination')
  require(sha(w/'sdirk.rs')==sha(ROOT/'tools/vco1_sdirk_kernel.rs'),'same SDIRK kernel')
 require(p1['commands'][1]['stdout']==p4['commands'][1]['stdout'] and canonical(p1['cases'])==canonical(p4['cases']),'48 roots exactly reverified')
 for t in (p1,p4,f1,f4):
  require(sha(Path(t['compiler']['path']))==t['compiler']['sha256'] and t['lab_stack_bytes']==8388608,'compiler and stack')
  builds=[c for c in t['commands'] if Path(c['command'][0])==Path(t['compiler']['path'])];require(builds and all(c['exit_code']==0 and 'opt-level=2' in c['command'] and 'link-arg=-Wl,--stack,8388608' in c['command'] for c in builds),'actual O2 stack build flags')
 traces=[]
 for p,minimum,ticks,count in ((p1,8,37104,2199),(p4,4,98008,17425)):
  require(not p['passed'] and p['native_roots_admitted'] and not p['conditional_continuation_admitted'] and len(p['cases'])==8 and len(p['actual_intervals'])==4,'root admission and continuation rejection');require(len(p['unchanged_replays'])==1,'native replay');replay=p['unchanged_replays'][0];require(p['commands'][-1]['exit_code']==replay['exit_code']!=0 and p['commands'][-1]['stderr']==replay['stderr'] and replay['source_sha256']==p['source_sha256'] and replay['export_sha256']==p['coverage']['sha256']==p['failed_export']['sha256'],'byte-identical walk replay');require('RESOURCE_REJECT' not in p['commands'][-1]['stderr'],'not resource rejection')
  raw=np.memmap(ROOT/p['failed_export']['path'],dtype='<f8').reshape(-1,542);traces.append(raw);require(len(raw)==count and raw[-1,0]==ticks and np.isfinite(raw).all() and np.array_equal(np.diff(raw[:,0]),raw[1:,1]) and np.max(raw[:,2:5])<=1 and np.min(raw[1:,1])==minimum and np.max(raw[1:,1])<=262144,'all rows real clock and gates')
  for start in (6,274):
   hi=raw[:,start:start+134];lo=raw[:,start+134:start+268];require(np.array_equal(hi+lo,hi) and np.all(np.abs(lo)<=np.abs(np.spacing(hi))/2) and np.max(np.abs(hi[:,:98]))<=40 and np.max(np.abs(hi[:,98:]))<=1,'whole endpoint/stage memory')
  changes=np.max(np.abs(np.diff(raw[:,6:104],axis=0)),axis=1);selected=sorted(set([1,len(raw)-1,*list(np.argsort(changes)[-2:]+1)]));require([x['row_index'] for x in p['actual_intervals']]==selected,'selected intervals')
 c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]
 def state(h,l):return [Decimal.from_float(v)+Decimal.from_float(w) for v,w in zip(h,l)]
 def check(rows,old,h):
  stage=list(map(Decimal,rows['stage']['independent_decimal']));endpoint=list(map(Decimal,rows['endpoint']['independent_decimal']));dt=ref.GAMMA*h;r,j,g=ref.circuit.reference_decimal(stage,old,dt,c);dc,jd,gd=ref.circuit.reference_decimal(stage,old,0.,c);forcing=[a-b for a,b in zip(r,dc)];ground=g-gd;rr,jj,gg=ref.forced_reference(endpoint,old,dt,c,forcing,ground);require(all(v==0 for k,v in enumerate(forcing) if k>=98 and k not in (118,119,129,130)),'no forcing of algebraic constraints')
  for part,res,ggg in [('stage',r,g),('endpoint',rr,gg)]:
   row=rows[part];n=row['native'];candidate=state(n['high'],n['low']);target=stage if part=='stage' else endpoint;require(row['passed'] and max(map(abs,res[:98]))<=Decimal.from_float(2e-14) and max(map(abs,res[98:]))<=Decimal.from_float(2e-12) and abs(sum(res[:98])+ggg)<=Decimal.from_float(1e-11),'independent stage KCL/constraint/ground');require(max(abs(a-b) for a,b in zip(candidate[:98],target[:98]))<=Decimal.from_float(2e-7) and max(abs(a-b) for a,b in zip(candidate[98:],target[98:]))<=Decimal.from_float(2e-10) and n['residual_ratio']<=1 and n['correction_ratio']<=1,'stage contrast and native gates')
  return endpoint
 with localcontext() as ctx:
  ctx.prec=100
  for p in (p1,p4):
   for case in p['cases']:
    old=state(case['previous_high'],case['previous_low']);h=case['half_dt_s'];full=check(case['steps']['full']['roots'],old,2*h);mid=check(case['steps']['mid']['roots'],old,h);end=check(case['steps']['end']['roots'],mid,h);ratios=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(full,end))];require(float(max(ratios))==case['error_ratio'] and (max(ratios)<=1)==case['local_error_admitted'],'case local error gate');require(case['local_error_admitted']==(case['scene']==0),'case temporal admissions unchanged')
   for item in p['actual_intervals']:check(item['roots'],state(item['previous_high'],item['previous_low']),item['dt_s'])
  for f,raw,half in ((f1,traces[0],8),(f4,traces[1],4)):
   require(f['passed'] and not f['unchanged_replays'] and f['failure_cause_confirmed']=='local error' and f['previous_high']==raw[-1,6:140].tolist() and f['previous_low']==raw[-1,140:274].tolist(),'floor provenance');old=state(f['previous_high'],f['previous_low']);h=half*125e-9/65536;full=check(f['steps']['full'],old,2*h);mid=check(f['steps']['mid'],old,h);end=check(f['steps']['end'],mid,h);ratios=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(full,end))];require(max(range(134),key=lambda k:ratios[k])==81 and float(max(ratios))==f['independent_limit']['error_ratio'] and max(ratios)>1,'floor LTE cause confirmed')
  require(m1['passed'] and m2['passed'] and m2['descriptor_identical_to_attempt01'] and m2['not_an_eigenvalue_enclosure'],'descriptor scope');require(all(not z['candidates'] for s in m1['scenes'] for z in s['shifts']),'original normalization admits no modes');require([len(s['matches']) for s in m2['scenes']]==[11,14,10],'cross-shift mode count')
  for old,new in zip(m1['scenes'],m2['scenes']):
   require(old['dc_jacobian_decimal']==new['dc_jacobian_decimal'] and old['charge_jacobian_decimal']==new['charge_jacobian_decimal'],'identical descriptor, changed criterion explicit');x=state(new['previous_high'],new['previous_low']);r,g,gg=ref.circuit.reference_decimal(x,x,0.,c);rr,j,ggr=ref.circuit.reference_decimal(x,x,1e-12,c);m=[[(a-b)*Decimal.from_float(1e-12) for a,b in zip(ja,ga)] for ja,ga in zip(j,g)];require([[str(v) for v in row] for row in g]==new['dc_jacobian_decimal'] and [[str(v) for v in row] for row in m]==new['charge_jacobian_decimal'],'whole descriptor reconstruction')
   for mode in new['matches']:
    require(mode['relative_pencil_residual']<=1e-8 and all(v['relative_distance']<=1e-3 for v in mode['other_shifts']),'matched mode gates')
   require(-1.311e14<new['matches'][0]['lambda_real_s']<-1.310e14 and new['matches'][0]['dominant_name']=='IC3_OUT','fastest mode reported accurately')
 for folder in ('vco1-sdirk-probe01','vco1-sdirk-probe4-01','vco1-sdirk-floor01','vco1-sdirk-floor4-01','vco1-reset-modes-source01','vco1-sdirk-measured-source01'):
  for p in (ROOT/'references-local'/folder).rglob('*'):
   if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
 for n,h in private.items():require(sha(ROOT/n)==h,'private corpus '+n)
 require(sha(ROOT/q['previous_audio']['path'])==q['previous_audio']['sha256'],'previous audio')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(q['source_sha256'])|{qp}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 for n in (*DOCS,'docs/VCO1_SDIRK_RESULTADOS.md','docs/VCO1_SDIRK_PROTOCOLO.md','docs/VCO1_POLOS_RESET_PROTOCOLO.md','docs/VCO1_POLOS_RESET_NORMALIZACION.md','docs/VCO1_SDIRK_CONTROL4_PROTOCOLO.md','docs/VCO1_SDIRK_PISO_PROTOCOLO.md','docs/VCO1_SDIRK_PISO4_PROTOCOLO.md'):
  p=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve();require(target==out.resolve() or target.exists(),'local doc link '+link)
 report=dict(schema='rf-d/SDIRK-lab-and-descriptor-release/v1',passed=True,base_commit=BASE,previous_qa_sha256=sha(ROOT/qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,covered_test_count=235,inherited_test_count=235,native_test_count=0,inherited_tests_reexecuted=False,independent_stage_root_comparisons_executed=124,repeated_conditional_root_bank=True,production_kernel_changed=False,sdirk_conditional_stage_roots_admitted=True,sdirk_continuation_admitted=False,walks_rejected=2,local_descriptor_reconstructed=True,matched_mode_counts=[11,14,10],spectrum_enclosure=False,new_spice_processes=0,new_audio=False,native_full_period_admitted=False,native_frequency_refinement_admitted=False,calibrated_transient_admitted=False,free_dc_admitted=False,physical_fidelity=False,real_time=False,sdirk_heap_measured=False,lab_stack_bytes=8388608,c4_pf=10,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],long_note_admitted_locally=False)
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('SDIRK release:235 inherited tests,124 stage-root comparisons;',len(sources),'public;',len(private),'private',flush=True)
if __name__=='__main__':main()
