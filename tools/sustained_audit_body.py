
def prefix_identity(p):
    maximum=p['maximum_half_ticks'];new=ROOT/f'references-local/sustained-voice01/{maximum}/selected.txt';old=ROOT/f'references-local/conditioned-portable-cycle01/1-{maximum}/selected.txt';end=START+788529152
    def exports(path):
        lines=path.read_text(encoding='utf8').splitlines();steps=[];obs=[];grids=[(START,lines[1])];clock=None;roots=[]
        for i,line in enumerate(lines):
            row=line.split(',')
            if row[0]=='STEP':
                clock=int(row[3]);
                if clock<=end:steps.append(line)
            elif row[0]=='OBS' and int(row[1])<=end:obs.append(line)
            elif row[0]=='GRID' and int(row[2])<=end:grids.append((int(row[2]),lines[i+1]))
            elif row[0]=='SELECT' and clock<=end:roots.append(lines[i:i+19])
        return dict(steps=steps,obs=obs,grids=grids,roots=roots)
    a,b=exports(old),exports(new);require(a==b,'complete admitted prefix exports by bytes')
    return dict(maximum_half_ticks=maximum,old_sha256=sha(old),new_sha256=sha(new),accepted_steps=len(a['steps']),fine_endpoints=len(a['obs']),grid_states=len(a['grids']),selected_triples=len(a['roots']),prefix_end_ticks=end,all_exported_prefix_bits_identical=True)

def cycle_diagnostic(p):
    maximum=p['maximum_half_ticks'];path=ROOT/f'references-local/sustained-voice01/{maximum}/selected.txt'
    rows=np.array([list(map(float,line.split(',')[1:])) for line in path.read_text(encoding='utf8').splitlines() if line.startswith('OBS,')]);ticks=rows[:,0];t=ticks*TICK
    held=[r for r in p['resets'] if r['phase']==1];require(len(held)>=3,'two complete held cycles');edges=[float(r['interpolated_time_s']) for r in held[-3:]]
    phase=np.linspace(0.,1.,2049);waves=[np.interp(a+phase*(b-a),t,rows[:,4]) for a,b in zip(edges[:-1],edges[1:])]
    ac=waves[-1]-np.trapezoid(waves[-1],phase);rms=float(np.sqrt(np.trapezoid(ac*ac,phase)))
    error=float(np.max(abs(waves[-1]-waves[-2])));seam=float(abs(waves[-1][-1]-waves[-1][0]))
    candidate=rms>=1e-4 and error<=5e-6 and error<=.02*rms and seam<=5e-6
    return dict(maximum_half_ticks=maximum,held_cycle_edges_s=edges,periods_s=list(np.diff(edges)),frequency_hz=1/(edges[-1]-edges[-2]),phase_points=2049,ac_rms_v=rms,cycle_difference_max_v=error,relative_to_ac_rms=error/rms if rms else None,seam_v=seam,repetition_candidate=candidate,steady_periodicity_admitted=False,last_cycle_volts=waves[-1].tolist())

def audit():
    native=json.loads((ROOT/'evidence/voice_sustained_native01.json').read_text(encoding='utf8'));inp=json.loads((ROOT/'evidence/voice_sustained_inputs01.json').read_text(encoding='utf8'));require(native['passed'] and len(native['profiles'])==2,'two extended profiles')
    profiles=[profile(p,inp) for p in native['profiles']];compares=[];a,b=profiles
    for x,y in zip(a['grids'],b['grids']):
        require(x['ticks']==y['ticks'],'shared grid clocks');u,v=lift(x['values']),lift(y['values']);ratio=lte(u,v);require(ratio<=1,'229 global refinement');compares.append(dict(ticks=x['ticks'],gate_ratio=ratio,max_voltage_error_v=max(float(abs(u[k]-v[k])) for k in range(229) if not 98<=k<133)))
    require(len(a['grids'])==len(b['grids'])==43 and len(a['resets'])==len(b['resets']),'grid/reset counts')
    for x,y in zip(a['resets'],b['resets']):require(x['phase']==y['phase'] and abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']))<=D(1e-8),'reset time refinement')
    prefixes=[prefix_identity(p) for p in profiles];cycles=[cycle_diagnostic(p) for p in profiles];difference=max(abs(x-y) for x,y in zip(cycles[0]['last_cycle_volts'],cycles[1]['last_cycle_volts']))
    for c in cycles:c.pop('last_cycle_volts')
    return dict(profiles=profiles,same_clock_refinement=compares,admitted_prefix_identity=prefixes,cycle_diagnostics=cycles,phase_cycle_resolution_difference_v=difference,
        repetition_candidate=all(c['repetition_candidate'] for c in cycles) and difference<=2e-6,
        independent_candidates=6*sum(p['selected_accepted_count'] for p in profiles),independent_nonlinear_rows=1374*sum(p['selected_accepted_count'] for p in profiles),
        accepted_steps=sum(p['accepted_steps'] for p in profiles),fine_steps=sum(p['fine_steps'] for p in profiles),replayed_accepted_steps=sum(p['replayed_accepted_steps'] for p in profiles),restores=sum(p['restores'] for p in profiles),reset_crossings=sum(len(p['resets']) for p in profiles),
        maximum_active_replay_probes=max(p['maximum_active_replay_probes'] for p in profiles),rejected_corruptions=8,atomic_rollbacks=4,
        sustained_on_window_admitted=True,duration_per_profile_s=.012004,held_s=.008,release_s=.004,
        steady_periodicity_admitted=False,full_contour_from_silence_admitted=False,physical_fidelity=False,real_time=False)

def main():
    names={'tools/check_sustained_voice.py','tools/sustained_audit_body.py','tools/prepare_sustained_auditor.py','tools/prepare_sustained_voice.py','evidence/voice_sustained_native01.json','evidence/voice_sustained_inputs01.json','evidence/voice_schur_chain_trajectory01.json','docs/VOZ_SOSTENIDA_PROTOCOLO.md'}
    for m in list(sys.modules.values()):
        f=getattr(m,'__file__',None)
        if f:
            p=Path(f).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':names.add(p.relative_to(ROOT).as_posix())
    before={n:sha(ROOT/n) for n in sorted(names)};r=dict(passed=False,source_sha256=before);started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(audit())
        require(time.perf_counter()-started<=600,'oracle wall budget');r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_base64']={n:__import__('base64').b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith('.py')}
        try:
            with localcontext() as ctx:ctx.prec=100;audit()
            r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r.update(source_sha256_after={n:sha(ROOT/n) for n in sorted(names)},wall_s=time.perf_counter()-started)
    require(before==r['source_sha256_after'],'stable graph auditor');write('evidence/voice_sustained_reference01.json',r);print('SUSTAINED_REFERENCE',r['passed'],r['wall_s'],r.get('failure',''),flush=True);require(r['passed'],'extended graph/refinement')
if __name__=='__main__':main()
