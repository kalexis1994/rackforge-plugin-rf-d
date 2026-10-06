"""Frozen long-note transformations and gates; no change to electrical branches."""
from dataclasses import asdict,replace
import difflib,hashlib,math
import numpy as np
import loudness_voice_probes as short
import voice_union_refine_runner as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT
PROTOCOL='docs/VOZ_REFINAMIENTO_SIGUIENTE_PROTOCOLO.md'
WORK=ROOT/'references-local/voice-circuit/full-note01'
GATES=dict(short.GATES)
WINDOWS=dict(rest=(.002,.008),attack=(.020,.080),held=(.120,.190),release=(.230,.340))

def scenes():
    return {name:replace(s,board=replace(s.board,oscillator=replace(s.oscillator,duration_s=.35)),
                         trigger_on_s=.01,trigger_off_s=.2) for name,s in short.scenes().items()}

def keyboard(s):
    return ('VE2_keyboard E2_KEYBOARD_TRIGGER 0 PWL(0 0 '
            f'{s.trigger_on_s:.17g} 0 {s.trigger_on_s+s.trigger_transition_s:.17g} 10 '
            f'{s.trigger_off_s:.17g} 10 {s.trigger_off_s+s.trigger_transition_s:.17g} 0)\n').encode()

def tran(s):
    h=s.oscillator.max_step_s
    return f'tran {h:.17g} {s.oscillator.duration_s:.17g} 0 {h:.17g}\n'.encode()

def patch(deck,name,old_export,new_export):
    old=short.scenes()[name];new=scenes()[name]
    anchors=[(keyboard(old),keyboard(new)),(tran(old),tran(new)),
             (('wrdata '+old_export+' ').encode(),('wrdata '+new_export+' ').encode())]
    result=deck;skeleton_before=deck;changes=[]
    for i,(a,b) in enumerate(anchors):
        if a==b or deck.count(a)!=1:raise ValueError('unique changed temporal/export anchor required')
        result=result.replace(a,b,1);skeleton_before=skeleton_before.replace(a,f'ANCHOR_{i}'.encode(),1)
        changes.append(dict(before=a.decode(),after=b.decode()))
    skeleton_after=result
    for i,(a,b) in enumerate(anchors):
        if result.count(b)!=1:raise ValueError('unique new anchor required')
        skeleton_after=skeleton_after.replace(b,f'ANCHOR_{i}'.encode(),1)
    if skeleton_before!=skeleton_after:raise ValueError('electrical bytes changed outside anchors')
    return result,dict(changes=changes,unchanged_skeleton_sha256=hashlib.sha256(skeleton_before).hexdigest(),
        diff=''.join(difflib.unified_diff(deck.decode().splitlines(True),result.decode().splitlines(True),
                                       fromfile='historical-short',tofile='long-note',n=0)),
        scenario=asdict(new),vectors=new.vectors)

def measurement(raw,s):
    info=prior.clock_info(raw,s.vectors,s.oscillator.duration_s,s.oscillator.max_step_s)
    if not info['endpoint_complete'] or not info['max_step_passed']:raise ValueError('complete long clock required')
    # Reuse current orientation/integration of both C2 and the ramp crossings.
    m=short.c.measurement(raw,s);t=raw[:,0]
    main=raw[:,s.vectors.index('v(f4_main_output)')+1]
    contour=raw[:,s.vectors.index('v(f4_loudness_contour)')+1];windows={}
    for name,(a,b) in WINDOWS.items():
        tt=np.r_[a,t[(t>a)&(t<b)],b];x=np.interp(tt,t,main);dc=np.trapezoid(x,tt)/(b-a)
        windows[name]=dict(output_dc_v=float(dc),output_ac_rms_v=float(np.sqrt(np.trapezoid((x-dc)**2,tt)/(b-a))),
            contour_mean_v=float(np.trapezoid(np.interp(tt,t,contour),tt)/(b-a)))
    m.update(windows=windows,window_spans_s=WINDOWS,dc_v={n:float(raw[0,i+1]) for i,n in enumerate(s.vectors)},
        output_min_v=float(main.min()),output_max_v=float(main.max()),output_final_v=float(main[-1]),
        contour_final_v=float(contour[-1]))
    return m

def contrast(a,b,sa,sb):
    ma=measurement(a,sa);mb=measurement(b,sb)
    if sa.oscillator.duration_s!=.35 or sb.oscillator.duration_s!=.35:raise ValueError('long pair duration required')
    grid=np.linspace(0,.35,70001);differences={};max_times={}
    for name in ('v(e2_timing_c2)','v(f4_loudness_contour)','v(mix_bus_board4_pin4)',
                 'v(f4_recover_collector)','v(f4_main_output)'):
        x=np.interp(grid,a[:,0],a[:,sa.vectors.index(name)+1]);y=np.interp(grid,b[:,0],b[:,sb.vectors.index(name)+1])
        d=np.abs(x-y);k=int(np.argmax(d));differences[name]=float(d[k]);max_times[name]=float(grid[k])
    cents=abs(1200*math.log2(ma['frequency_hz']/mb['frequency_hz']));rms={}
    for label in WINDOWS:
        x,y=[m['windows'][label]['output_ac_rms_v'] for m in (ma,mb)]
        rms[label]=dict(difference_v=abs(x-y),limit_v=GATES['rms_absolute_v']+GATES['rms_relative']*y)
    tests=dict(trace=all(d<=GATES['trace_v'] for d in differences.values()),frequency=cents<=GATES['frequency_cents'],
        rms=all(r['difference_v']<=r['limit_v'] for r in rms.values()),
        charge=all(max(m['timing_balance_max_c'],m['output_balance_max_c'])<=GATES['charge_c'] for m in (ma,mb)))
    return dict(measured=True,passed=all(tests.values()),gates=tests,max_trace_difference_v=differences,
        max_trace_clock_s=max_times,frequency_cents=cents,output_window_rms=rms,grid_points=len(grid),
        grid_step_s=GATES['observation_grid_s'],phase_alignment=False)
