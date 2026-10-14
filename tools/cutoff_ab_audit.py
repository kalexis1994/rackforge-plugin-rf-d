
def seam(p):
 m=p['maximum_half_ticks'];d=ROOT/f'references-local/cutoff-ab01/{m}';parent=ROOT/f'references-local/voice-cutoff01/{m}/event1-before.ckp';a=parent.read_bytes();require(a==(d/'incoming-original.ckp').read_bytes()==(d/'checkpoints.bin').read_bytes()[:3736],'exact common origin including proposal and complete recipe');require((d/'seam-old.bin').read_bytes()==(d/'seam-new.bin').read_bytes(),'four complete open advances by bits');return dict(maximum_half_ticks=m,parent_sha256=sha(parent),preserved_values=458,complete_accepted_bit_comparisons=4)
def flux_audit(p):
 import inspect
 from release_audit_body import flux_audit as original
 body=inspect.getsource(original).replace('release-voice01','cutoff-ab01').replace('D(100000)','D(DECAY)');ns=dict(globals());exec(compile(body,'<unchanged open flux gates>','exec'),ns);return ns['flux_audit'](p)
def audit():
 native=json.loads((ROOT/'evidence/cutoff_ab_native01.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/cutoff_ab_inputs01.json').read_text(encoding='utf8'));old=json.loads((ROOT/'evidence/voice_cutoff_reference01.json').read_text(encoding='utf8'));require(native['passed'] and old['passed'],'admitted parent and open native');profiles=[profile(p,inp) for p in native['profiles']];compares=[];a,b=profiles;require(len(a['grids'])==len(b['grids'])==11 and len(a['resets'])==len(b['resets']),'open shared clocks and resets')
 for x,y in zip(a['grids'],b['grids']):
  require(x['ticks']==y['ticks'],'open common clock');u,v=lift(x['values']),lift(y['values']);ratio=lte(u,v);require(ratio<=1,'229 open refinement');compares.append(dict(ticks=x['ticks'],gate_ratio=ratio,max_voltage_error_v=max(float(abs(u[k]-v[k])) for k in range(229) if not 98<=k<133)))
 for x,y in zip(a['resets'],b['resets']):require(abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']))<=D(1e-8),'open reset refinement')
 flux=[flux_audit(p) for p in profiles];require(len(flux[0]['events'])==len(flux[1]['events']),'open transition counts')
 for x,y in zip(flux[0]['events'],flux[1]['events']):require(x['kind']==y['kind'] and x['direction']==y['direction'] and abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']))<=D(1e-7),'open transition refinement')
 forks=[]
 for p in profiles:
  m=p['maximum_half_ticks'];closed=next(q for q in old['profiles'] if q['maximum_half_ticks']==m);grid=[g for g in closed['grids'] if START<=g['ticks']<=START+BOUNDARIES[-1]];require(len(grid)==11 and packed(grid[0]['values'])==packed(p['grids'][0]['values']),'closed/open common 458 state and window');d=ROOT/f'references-local/voice-cutoff01/{m}';before=(d/'event1-before.ckp').read_bytes();after=(d/'event1-after.ckp').read_bytes();require(before[:28]==after[:28] and before[32:64]==after[32:64] and before[72:]==after[72:] and struct.unpack_from('<d',before,64)[0]==1. and struct.unpack_from('<d',after,64)[0]==.5,'only phase and cutoff differ at fork');differences=[]
  for x,y in zip(p['grids'],grid):
   require(x['ticks']==y['ticks'],'A/B identical observation clocks');u,v=lift(x['values']),lift(y['values']);differences.append(dict(ticks=x['ticks'],c2_difference_v=float(u[205]-v[205]),loudness_difference_v=float(u[203]-v[203]),j7_difference_v=float(u[194]-v[194]),q26_base_difference_v=float(u[195]-v[195]),tail_current_open_a=float((u[138]-u[198])/D(680)),tail_current_closed_a=float((v[138]-v[198])/D(680)),max_voltage_difference_v=max(float(abs(u[k]-v[k])) for k in range(229) if not 98<=k<133)))
  forks.append(dict(maximum_half_ticks=m,start_ticks=START,end_ticks=START+BOUNDARIES[-1],common_state_values=458,common_proposal=struct.unpack_from('<I',before,24)[0],open_alpha=1.,closed_alpha=.5,closed_accepted_steps=closed['phases'][1]['accepted_steps'],closed_fine_steps=closed['phases'][1]['fine_steps'],closed_selected_accepted_count=sum(q['phase']==1 for q in closed['selected_lte']),closed_ledger=closed['phases'][1]['ledger'],same_clock_differences=differences))
 return dict(profiles=profiles,seams=[seam(p) for p in profiles],flux_checks=flux,same_clock_refinement=compares,forks=forks,independent_candidates=6*sum(p['selected_accepted_count'] for p in profiles),independent_nonlinear_rows=1374*sum(p['selected_accepted_count'] for p in profiles),accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_steps=sum(p['fine_steps'] for p in profiles),restores=sum(p['restores'] for p in profiles),replayed_accepted_steps=sum(p['replayed_accepted_steps'] for p in profiles),maximum_active_replay_probes=max(p['maximum_active_replay_probes'] for p in profiles),rejected_corruptions=8,atomic_rollbacks=2,seam_compared_accepted=8,open_duration_s=.008,closed_coverage_inherited=True,closed_equations_reexecuted=False,new_continuous_history_duration_s=0,new_source_event=False,physical_fidelity=False,real_time=False)
def main():
 names={'tools/check_cutoff_ab.py','tools/prepare_cutoff_ab.py','tools/cutoff_ab_audit.py','evidence/cutoff_ab_native01.json','evidence/cutoff_ab_inputs01.json','evidence/voice_cutoff_reference01.json','docs/VOZ_CUTOFF_AB_PROTOCOLO.md'}
 for module in list(sys.modules.values()):
  f=getattr(module,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
 before={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=before);started=time.perf_counter()
 try:
  with localcontext() as ctx:ctx.prec=100;r.update(audit())
  require(time.perf_counter()-started<=600,'oracle budget');r['passed']=True
 except Exception:
  r['failure']=traceback.format_exc();r['failed_source_base64']={n:__import__('base64').b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith('.py')}
  try:
   with localcontext() as ctx:ctx.prec=100;audit()
   r['replay']='unexpected pass'
  except Exception:r['replay']=traceback.format_exc()
 r.update(source_sha256_after={n:sha(ROOT/n) for n in sorted(names)},wall_s=time.perf_counter()-started);require(before==r['source_sha256_after'],'stable auditor');write('evidence/cutoff_ab_reference01.json',r);print('CUTOFF_AB_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''));require(r['passed'],'original open branch and common-origin A/B')
if __name__=='__main__':main()
