"""Read-only accepted-state/prefix observations; no admission or new solves."""
import json,math,re
from pathlib import Path
import numpy as np
import voice_full_note as note
import vco1_circuit_reference as vco

ROOT=vco.ROOT
OBS=('v(e2_timing_c2)','v(f4_loudness_contour)','v(mix_bus_board4_pin4)',
     'v(f4_recover_collector)','v(f4_main_output)')

def prefix(a,b,vectors):
    # The endpoint is bounded by both exports, including an aborted one.
    for x in (a,b):note.prior.clock_info(x,vectors,.35,float('inf'))
    stop=min(float(a[-1,0]),float(b[-1,0]));step=5e-6
    grid=np.arange(math.floor(stop/step)+1)*step
    grid=grid[grid<=stop]  # Floating multiplication may round the last grid point above stop.
    if not len(grid) or grid[-1]>stop:raise ValueError('prefix extrapolation prohibited')
    maxima={};times={}
    for name in OBS:
        i=vectors.index(name)+1;d=np.abs(np.interp(grid,a[:,0],a[:,i])-np.interp(grid,b[:,0],b[:,i]))
        k=int(np.argmax(d));maxima[name]=float(d[k]);times[name]=float(grid[k])
    ramp=vectors.index('v(ramp_c1)')+1;events=[]
    for x in (a,b):
        e=vco.crossings(x[:,0],x[:,ramp],-2,True);events.append(e[e<=stop])
    same=len(events[0])==len(events[1]);delta=float(np.max(np.abs(events[0]-events[1]))) if same and len(events[0]) else None
    return dict(common_export_endpoint_s=stop,grid_endpoint_s=float(grid[-1]),grid_points=len(grid),grid_step_s=step,
        voltage_maxima_v=maxima,voltage_max_clock_s=times,reset_counts=[len(e) for e in events],
        max_reset_time_difference_s=delta,dc_voltage_max_v=float(np.max(np.abs(a[0,1:]-b[0,1:]))),
        phase_alignment=False,full_horizon_measured=stop>=.35-1e-14,admission=False)

def main():
    output=ROOT/'evidence/voice_full_note_diagnostic01.json'
    if output.exists():raise ValueError('preserve diagnostic')
    bank_path=ROOT/'evidence/voice_full_note_runs01.json';bank=vco.read(bank_path)
    audit_path=ROOT/'evidence/voice_full_note_validation01.json';audit=vco.read(audit_path)
    if not audit['passed'] or audit['bank_sha256']!=vco.sha(bank_path):raise ValueError('audited long bank required')
    raw={};states={}
    for name,r in bank['records'].items():
        p=note.WORK/(name+'.txt')
        if vco.sha(p)!=r['raw_export_sha256']:raise ValueError('raw identity')
        a=np.loadtxt(p,skiprows=1,ndmin=2);raw[name]=a
        if r['trajectory_complete']:continue
        t=a[:,0];vectors=r['vectors'];ramp=vectors.index('v(ramp_c1)')+1
        events=vco.crossings(t,a[:,ramp],-2,True);near=t>=t[-1]-100e-9
        log=(note.WORK/(name+'.log')).read_text(encoding='utf-8',errors='replace')
        match=re.search(r'Timestep too small; time = ([^,]+), timestep = ([^:]+): trouble with ([^\r\n]+)',log)
        error=dict(reported_time_text=match[1],reported_step_text=match[2],reported_device=match[3]) if match else None
        if error:
            error.update(time_is_rounded_console_text=True,time_ulp_s=math.ulp(float(match[1])),
                reported_step_over_time_ulp=float(match[2])/math.ulp(float(match[1])))
        states[name]=dict(last_accepted_clock_s=float(t[-1]),accepted_reset_crossings_s=events.tolist(),
            accepted_reset_count=len(events),last_accepted_state_v={n:float(a[-1,i+1]) for i,n in enumerate(vectors)},
            time_since_last_accepted_upcross_s=float(t[-1]-events[-1]) if len(events) else None,
            time_since_keyboard_on_transition_end_s=float(t[-1]-(note.scenes()[name].trigger_on_s+note.scenes()[name].trigger_transition_s)),
            accepted_final_window=dict(width_s=100e-9,rows=int(near.sum()),first_clock_s=float(t[near][0]),
                min_v={n:float(a[near,i+1].min()) for i,n in enumerate(vectors)},
                max_v={n:float(a[near,i+1].max()) for i,n in enumerate(vectors)}),
            solver_error=error,rejected_Newton_state_available=False,cause_identified=False)
    comparisons={a+'--'+b:prefix(raw[a],raw[b],note.scenes()[a].vectors) for a,b in note.short.PAIRS}
    helpers=[Path(__file__),Path(note.__file__),Path(vco.__file__)]
    report=dict(schema='rf-d/full-note-diagnostic/v1',passed=True,bank_sha256=vco.sha(bank_path),audit_sha256=vco.sha(audit_path),
        incomplete_scenes=states,prefix_comparisons=comparisons,new_solves=0,new_compiler_runs=0,
        admission=False,cause_identified=False,rejected_Newton_state_available=False,new_audio=False,
        diagnostic_source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers})
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('accepted-state diagnostics:',list(states),'admission: False',flush=True)

if __name__=='__main__':main()
