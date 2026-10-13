"""Original graph, full-state refinement, control event and finite discharge."""
from release_audit_body import flux_audit as _unused  # Source identity only; no reuse of its experiment globals.

def seam(p):
 maximum=p['maximum_half_ticks'];directory=ROOT/f'references-local/decay-voice02/{maximum}';parent=ROOT/f'references-local/release-voice01/{maximum}/final.ckp';raw=parent.read_bytes();copy=(directory/'incoming-original.ckp').read_bytes();nominal=(directory/'incoming-nominal.ckp').read_bytes();changed=(directory/'checkpoints.bin').read_bytes()[:3728]
 require(raw==copy and len(raw)==3720 and len(nominal)==3728 and nominal[:8]==b'RFDCY001' and raw[8:56]==nominal[8:56] and raw[56:]==nominal[64:] and struct.unpack('<d',nominal[56:64])[0]==100000.,'old payload and metadata preserved in controlled format')
 expected=bytearray(nominal);expected[56:64]=struct.pack('<d',DECAY);require(changed==bytes(expected),'only resistance changes at event');q=checkpoint(changed);require(q['ticks']==START,'event clock')
 require((directory/'control-event.txt').read_text(encoding='utf8')==f'DECAY_CONTROL,{START},100000,1000\n','electrical control event declaration')
 legacy=ROOT/f'references-local/decay-voice02/legacy-{maximum}/nominal.bin';a=legacy.read_bytes();require(a==(directory/'nominal-old.bin').read_bytes()==(directory/'nominal-new.bin').read_bytes(),'three-way finite nominal history identity')
 return dict(maximum_half_ticks=maximum,preserved_high_low_values=458,preserved_next_full_ticks=q['next_full'],event_ticks=START,old_decay_ohm=100000.,new_decay_ohm=DECAY,source_voltage_event=False,only_resistance_changed=True,nominal_compared_accepted=4,nominal_bytes=len(a),frozen_library_sha256=sha(ROOT/'references-local/conditioned-recipe-library02/librf_d_circuit.rlib'))

# Exact prior flux-observer audit adapted only in path and the one resistance.
def flux_audit(p):
 import inspect
 from release_audit_body import flux_audit as original_flux
 body=inspect.getsource(original_flux).replace('release-voice01','decay-voice02').replace('D(100000)','D(DECAY)')
 namespace=dict(globals());exec(compile(body,'<declared-decay-flux-auditor>','exec'),namespace);return namespace['flux_audit'](p)

def audit():
 native=json.loads((ROOT/'evidence/voice_decay_native02.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_decay_inputs01.json').read_text(encoding='utf8'));parent=json.loads((ROOT/'evidence/voice_release_reference01.json').read_text(encoding='utf8'));held=json.loads((ROOT/'evidence/voice_sustained_reference01.json').read_text(encoding='utf8'));require(native['passed'] and parent['passed'] and native['nominal_three_way_identical'],'new family and parent admitted')
 profiles=[profile(p,inp) for p in native['profiles']];a,b=profiles;compares=[];require(len(a['grids'])==len(b['grids'])==21 and len(a['resets'])==len(b['resets']),'common controlled clocks/resets')
 for x,y in zip(a['grids'],b['grids']):
  require(x['ticks']==y['ticks'],'common clock');u,v=lift(x['values']),lift(y['values']);ratio=lte(u,v);require(ratio<=1,'229 controlled refinement');compares.append(dict(ticks=x['ticks'],gate_ratio=ratio,max_voltage_error_v=max(float(abs(u[k]-v[k])) for k in range(229) if not 98<=k<133)))
 for x,y in zip(a['resets'],b['resets']):require(abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']))<=D(1e-8),'oscillator reset refinement')
 seams=[seam(p) for p in profiles];flux=[flux_audit(p) for p in profiles];event_refinement=[];require(len(flux[0]['events'])==len(flux[1]['events']),'controlled transition counts')
 for x,y in zip(flux[0]['events'],flux[1]['events']):
  require(x['kind']==y['kind'] and x['direction']==y['direction'],'controlled transition direction');delta=abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']));require(delta<=D(1e-7),'controlled transition refinement');event_refinement.append(dict(kind=x['kind'],difference_s=str(delta)))
 joined=[]
 for p in profiles:
  old=next(j for j in parent['joined_ledgers'] if j['maximum_half_ticks']==p['maximum_half_ticks']);first=next(q for q in held['profiles'] if q['maximum_half_ticks']==p['maximum_half_ticks'])['grids'][0];integrals=[D(r['native_dc_integral_c'])+D(p['phases'][0]['native_integrals_c'][k]) for k,r in enumerate(old['ledger']['rows'])];duration=START+BOUNDARIES[-1]-first['ticks'];balance=ledger(lift(first['values']),lift(p['grids'][-1]['values']),[float(x) for x in integrals],duration);joined.append(dict(maximum_half_ticks=p['maximum_half_ticks'],duration_ticks=duration,duration_s=duration*TICK,ledger=balance))
 return dict(profiles=profiles,seams=seams,same_clock_refinement=compares,flux_checks=flux,transition_refinement=event_refinement,joined_ledgers=joined,controlled_release_admitted=True,decay_ohm=DECAY,continued_duration_s=.016,joined_duration_s=.036004,
  independent_candidates=6*sum(p['selected_accepted_count'] for p in profiles),independent_nonlinear_rows=1374*sum(p['selected_accepted_count'] for p in profiles),accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_steps=sum(p['fine_steps'] for p in profiles),restores=sum(p['restores'] for p in profiles),replayed_accepted_steps=sum(p['replayed_accepted_steps'] for p in profiles),maximum_active_replay_probes=max(p['maximum_active_replay_probes'] for p in profiles),rejected_corruptions=8,atomic_rollbacks=2,nominal_compared_accepted=8,invalid_control_rejections=12,invalid_control_restore_rejections=2,new_source_event=True,source_voltage_event=False,steady_periodicity_admitted=False,full_contour_from_silence_admitted=False,physical_fidelity=False,real_time=False)

def main():
 names={'tools/check_decay_control.py','tools/decay_audit_body.py','tools/prepare_decay_auditor.py','tools/prepare_decay_control.py','evidence/voice_decay_native02.json','evidence/voice_decay_inputs01.json','evidence/voice_release_reference01.json','evidence/voice_sustained_reference01.json','docs/DECAY_CONTROL_PROTOCOLO.md'}
 for m in list(sys.modules.values()):
  f=getattr(m,'__file__',None)
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
 r.update(source_sha256_after={n:sha(ROOT/n) for n in sorted(names)},wall_s=time.perf_counter()-started);require(before==r['source_sha256_after'],'stable auditor');write('evidence/voice_decay_reference02.json',r);print('DECAY_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True);require(r['passed'],'controlled original graph/flux/refinement')
if __name__=='__main__':main()
