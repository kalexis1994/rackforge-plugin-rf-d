"""Audit private grid copies, 22 independent roots and preserved temporal failures."""
import base64,hashlib,json,re,subprocess
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_increment_circuit as oracle
from vco1_newton_reference import ROOT,sha
from validate_mixer_on_native import native_source_identity
BASE='236f170'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 out=ROOT/'evidence/voice_vco1_reset_grid_tests01.json';require(not out.exists(),'preserve grid publication');qp='evidence/voice_vco1_increment_tests01.json';q=read(qp);snapshot=read('evidence/voice_vco1_reset_grid_documentation01.json');first=read('evidence/voice_vco1_reset_grid01.json');grid=read('evidence/voice_vco1_reset_grid02.json');floor=read('evidence/voice_vco1_reset_grid_floor01.json');private=dict(q['private_input_sha256']);archive=ROOT/'references-local/vco1-reset-grid-measured-source01';archive.mkdir(exist_ok=True);blobs={p.stem:p for p in (ROOT/'references-local').rglob('*.blob')}
 require(q['passed'] and q['covered_test_count']==235 and sha(ROOT/qp)==snapshot['previous_qa_sha256'],'inherited QA')
 for n,h in q['source_sha256'].items():
  if n in DOCS or n=='.gitattributes':
   old=base64.b64decode(snapshot['previous_bytes_base64'][n]);native_source_identity(n,h,old)
   if n=='.gitattributes':require((ROOT/n).read_bytes()==old+b'/tools/vco1_reset_grid.rs text eol=lf\n','only new runner policy')
  else:require(sha(ROOT/n)==h,'protected input '+n)
 for t in (first,grid,floor):
  require(t['source_sha256']==t['source_sha256_after'] and t['private_input_sha256']==t['private_input_sha256_after'],'measured input identity')
  for n,h in t['source_sha256'].items():
   target=archive/(h+'.blob')
   if not target.exists():
    b=(ROOT/n).read_bytes()
    if hashlib.sha256(b).hexdigest()!=h:
     if h in blobs:b=blobs[h].read_bytes()
     elif n in snapshot['previous_bytes_base64']:b=base64.b64decode(snapshot['previous_bytes_base64'][n])
     else:b=subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT)
    require(hashlib.sha256(b).hexdigest()==h,'recover measured bytes '+n);target.write_bytes(b)
   require(sha(target)==h,'source archive');private[target.relative_to(ROOT).as_posix()]=h
  private.update(t['private_input_sha256'])
  for item in t['outputs']:require(sha(ROOT/item['path'])==item['sha256'] and (ROOT/item['path']).stat().st_size==item['bytes'],'retained output')
  require(sha(Path(t['compiler']['path']))==t['compiler']['sha256'],'pinned compiler')
 require(not first['passed'] and len(first['unchanged_replays'])==1 and first['commands'][-1]['exit_code']==first['unchanged_replays'][0]['exit_code']!=0 and first['commands'][-1]['stderr']==first['unchanged_replays'][0]['stderr'] and first['unchanged_replays'][0]['source_sha256']==first['source_sha256'],'compile reject and exact replay')
 w=ROOT/'references-local/vco1-reset-grid02';core=(ROOT/'crates/rf-d-circuit/src/vco1_increment.rs').read_text();controller=(ROOT/'crates/rf-d-circuit/src/vco1_increment_adaptive.rs').read_text();require((w/'fine.rs').read_text()==core.replace('pub const MIN_DT_S:f64=125e-9/4096.;','pub const MIN_DT_S:f64=125e-9/65536.;'),'only private kernel domain extension');require((w/'adaptive.rs').read_text()==controller.replace('vco1_increment','fine').replace('maximum_half_ticks>32768','maximum_half_ticks>524288').replace('for attempts in 1..=16','for attempts in 1..=20'),'only declared controller changes')
 source=(ROOT/'crates/rf-d-circuit/src/output_conversion.rs').read_text();maxabs=source[source.index('pub(crate) fn max_abs'):source.index('\n}',source.index('pub(crate) fn max_abs'))+2];linear=source[source.index('pub(crate) fn solve_linear_sparse'):source.index('/// Scaled-pivot elimination for several')];require((w/'linear.rs').read_text()=='use rf_d_circuit::StepError;\n'+maxabs+'\n'+linear,'exact prior sparse elimination');require(sha(w/'vco1_stamp_data.rs')==sha(ROOT/'crates/rf-d-circuit/src/vco1_stamp_data.rs'),'private graph bytes')
 for n in ('fine.rs','linear.rs','vco1_stamp_data.rs'):require(sha(ROOT/'references-local/vco1-reset-grid-floor01'/n)==sha(w/n),'second floor exact same kernel')
 require(not grid['passed'] and len(grid['unchanged_replays'])==1 and not grid['coverage']['complete_50us'],'grid still rejected');replay=grid['unchanged_replays'][0];require(grid['commands'][-1]['exit_code']==replay['exit_code']!=0 and grid['commands'][-1]['stderr']==replay['stderr'] and replay['source_sha256']==grid['source_sha256'] and replay['export_sha256']==grid['failed_export']['sha256'],'unchanged trace replay');require('PrecisionLimit' in grid['commands'][-1]['stderr'] and 'RESOURCE_REJECT' not in grid['commands'][-1]['stderr'],'temporal failure, not resources')
 raw=np.memmap(ROOT/grid['failed_export']['path'],dtype='<f8').reshape(-1,274);require(len(raw)==32301 and raw[-1,0]==99028 and np.isfinite(raw).all() and np.array_equal(np.diff(raw[:,0]),raw[1:,1]),'all prefix ticks');hi=raw[:,6:140];lo=raw[:,140:];require(np.array_equal(hi+lo,hi) and np.all(np.abs(lo)<=np.abs(np.spacing(hi))/2) and np.max(np.abs(hi[:,:98]))<=40 and np.max(np.abs(hi[:,98:]))<=1 and np.max(raw[:,2:5])<=1 and np.min(raw[1:,1])==1 and np.max(raw[1:,1])==16,'complete memory and gates');require(raw[0,6:].tolist()==list(map(float,(w/'history.txt').read_text().split())),'initial history');require(grid['coverage']['max_attempts']<=20 and not floor['extra_domain_extension'],'bounded floor diagnostic')
 tick=125e-9/65536;c=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]
 def state(hi,lo):return [Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(hi,lo)]
 def check(row,previous,dt):
  root=list(map(Decimal,row['independent_decimal']));res,j,g=oracle.reference_decimal(root,previous,dt,c);require(row['passed'] and max(map(abs,res[:98]))<=Decimal.from_float(2e-14) and max(map(abs,res[98:]))<=Decimal.from_float(2e-12) and abs(sum(res[:98])+g)<=Decimal.from_float(1e-11),'independent root KCL/constraint/ground');n=row['native'];candidate=state(n['high'],n['low']);require(max(abs(a-b) for a,b in zip(candidate[:98],root[:98]))<=Decimal.from_float(2e-7) and max(abs(a-b) for a,b in zip(candidate[98:],root[98:]))<=Decimal.from_float(2e-10) and n['residual_ratio']<=1 and n['correction_ratio']<=1,'root contrast and native gates');return root
 with localcontext() as ctx:
  ctx.prec=100;original=state(raw[0,6:140],raw[0,140:]);require(len(grid['trios'])==5 and len(grid['intervals'])==4,'19 grid roots')
  for power in range(5):
   trio=grid['trios'][str(power)];h=125e-9/4096/2**power;require(trio['half_dt_s']==h,'declared dyadic scene');full=check(trio['roots']['full'],original,2*h);mid=check(trio['roots']['mid'],original,h);end=check(trio['roots']['end'],mid,h);ratios=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(full,end))];require(max(range(134),key=lambda k:ratios[k])==50 and float(max(ratios))==trio['error_ratio'] and (max(ratios)<=1)==trio['local_error_admitted'],'first limit decision');require(trio['local_error_admitted']==(power>0),'first interval recovered by subdivision')
  changes=np.max(np.abs(np.diff(raw[:,6:104],axis=0)),axis=1);expected=sorted(set([1,len(raw)-1,*list(np.argsort(changes)[-2:]+1)]));require([row['row_index'] for row in grid['intervals']]==expected,'selected actual intervals')
  for row in grid['intervals']:
   k=row['row_index'];require(row['conditional_previous_high']==raw[k-1,6:140].tolist() and row['conditional_previous_low']==raw[k-1,140:].tolist() and row['native']['high']==raw[k,6:140].tolist() and row['native']['low']==raw[k,140:].tolist() and row['interval_ticks']==raw[k,1] and row['elapsed_ticks']==raw[k,0],'actual interval provenance');check(row,state(raw[k-1,6:140],raw[k-1,140:]),float(raw[k,1]*tick))
  previous=state(raw[-1,6:140],raw[-1,140:]);full=check(floor['roots']['full'],previous,2*tick);mid=check(floor['roots']['mid'],previous,tick);end=check(floor['roots']['end'],mid,tick);ratios=[abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(full,end))];require(floor['passed'] and len(floor['roots'])==3 and max(range(134),key=lambda k:ratios[k])==81 and float(max(ratios))==floor['independent_limit']['error_ratio'] and max(ratios)>1 and oracle.inventory(oracle.scenario(c))['names'][81]=='XIC3.7','second temporal limit confirmed')
 for t in (grid,floor):require(t.get('main_stack_bytes',t.get('lab_stack_bytes'))==8388608 and all('opt-level=2' in cmd['command'] and 'link-arg=-Wl,--stack,8388608' in cmd['command'] for cmd in t['commands'] if cmd['command'][0]==t['compiler']['path']),'laboratory build flags')
 for folder in ('vco1-reset-grid01','vco1-reset-grid02','vco1-reset-grid-floor01','vco1-reset-grid-measured-source01'):
  for p in (ROOT/'references-local'/folder).rglob('*'):
   if p.is_file():private[p.relative_to(ROOT).as_posix()]=sha(p)
 for n,h in private.items():require(sha(ROOT/n)==h,'private corpus '+n)
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(q['source_sha256'])|{qp}|{n for n in staged if n and ROOT/n!=out});sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 for n in (*DOCS,'docs/VCO1_RESET_GRILLA_RESULTADOS.md','docs/VCO1_RESET_GRILLA_PROTOCOLO.md','docs/VCO1_RESET_GRILLA_ADAPTADOR.md','docs/VCO1_RESET_SEGUNDO_PISO_PROTOCOLO.md'):
  p=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(p.parent/link.split('#')[0]).resolve();require(target==out.resolve() or target.exists(),'local doc link '+link)
 report=dict(schema='rf-d/private-grid-diagnostic-release/v1',passed=True,base_commit=BASE,previous_qa_sha256=sha(ROOT/qp),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,covered_test_count=235,inherited_test_count=235,native_test_count=0,inherited_tests_reexecuted=False,independent_diagnostic_root_count=22,production_kernel_changed=False,first_reset_interval_recovered_in_private_copy=True,finer_grid_campaign_admitted=False,accepted_conditional_steps=32300,conditional_coverage_s=grid['coverage']['elapsed_s'],second_temporal_limit_node='XIC3.7',independent_local_error_ratio=floor['independent_limit']['error_ratio'],native_full_period_admitted=False,native_frequency_refinement_admitted=False,calibrated_transient_admitted=False,free_dc_admitted=False,new_spice_processes=0,new_audio=False,physical_fidelity=False,real_time=False,lab_stack_bytes=8388608,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],long_note_admitted_locally=False)
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('Grid release:235 inherited tests,22 independent diagnostic roots;',len(sources),'public;',len(private),'private',flush=True)
if __name__=='__main__':main()
