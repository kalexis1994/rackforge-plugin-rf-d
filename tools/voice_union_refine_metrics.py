"""Nominal full-vector control; frozen gates; no phase alignment."""
import math
import numpy as np
import vco1_circuit_reference as vco
import voice_union_refine_runner as runner

def exact(a,b,vectors):
    for raw in (a,b):runner.clock_info(raw,vectors,.04,.5e-6)
    return dict(passed=a.shape==b.shape and bool(np.array_equal(a,b)),rows=[len(a),len(b)],last_clock_s=[float(a[-1,0]),float(b[-1,0])])

def control(a,b,vectors):
    for raw in (a,b):
        info=runner.clock_info(raw,vectors,.04,.5e-6)
        if not info['endpoint_complete'] or not info['max_step_passed']:raise ValueError('two complete controls required')
    indices=[i+1 for i,n in enumerate(vectors) if n.startswith('v(')]
    grid=np.linspace(0,.04,8001)
    maxima={vectors[i-1]:float(np.max(np.abs(np.interp(grid,a[:,0],a[:,i])-np.interp(grid,b[:,0],b[:,i])))) for i in indices}
    dc=max(float(abs(a[0,i]-b[0,i])) for i in indices);ramp=vectors.index('v(ramp_c1)')+1
    events=[vco.crossings(raw[:,0],raw[:,ramp],-2.,True) for raw in (a,b)]
    settled=[e[e>=.005] for e in events]
    if any(len(e)<4 for e in settled):raise ValueError('settled reset train required')
    frequencies=[float(1/np.mean(np.diff(e))) for e in settled];cents=abs(1200*math.log2(frequencies[0]/frequencies[1]))
    same=len(events[0])==len(events[1]);timing=float(np.max(np.abs(events[0]-events[1]))) if same else None
    gates=dict(dc_voltage=dc<=1e-6,grid_voltage=max(maxima.values())<=.005,frequency=cents<=1.,reset_count=same,reset_timing=timing is not None and timing<=1e-8)
    return dict(passed=all(gates.values()),gates=gates,voltage_maxima_v=maxima,dc_voltage_max_v=dc,
        grid_step_s=5e-6,grid_points=len(grid),frequencies_hz=frequencies,frequency_difference_cents=cents,
        reset_counts=[len(e) for e in events],max_reset_time_difference_s=timing,reset_crossings_s=[e.tolist() for e in events],phase_alignment=False)
