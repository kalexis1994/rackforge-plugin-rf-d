"""Full-clock control gates for the declared equivalent branch-row experiment."""
import math
import numpy as np
import voice_newton_probe as prior
import vco1_circuit_reference as vco


def compare(candidate,reference):
    prior.exact(candidate,candidate);prior.exact(reference,reference)
    if candidate[-1,0]!=.04 or reference[-1,0]!=.04:raise ValueError('complete 40 ms controls required')
    grid=np.linspace(0,.04,8001)
    maxima=[float(np.max(np.abs(np.interp(grid,candidate[:,0],candidate[:,k])-np.interp(grid,reference[:,0],reference[:,k])))) for k in range(1,6)]
    events=[vco.crossings(a[:,0],a[:,1],-2.,True) for a in (candidate,reference)]
    if any(len(e[e>=.005])<3 for e in events):raise ValueError('settled frequency unverified')
    frequencies=[float(1/np.mean(np.diff(e[e>=.005]))) for e in events]
    cents=abs(1200*math.log2(frequencies[0]/frequencies[1]))
    same=len(events[0])==len(events[1]);timing=float(np.max(np.abs(events[0]-events[1]))) if same else None
    dc_v=float(np.max(np.abs(candidate[0,1:6]-reference[0,1:6])));dc_i=float(abs(candidate[0,6]-reference[0,6]))
    gates=dict(dc_voltage=dc_v<=1e-6,dc_port_current=dc_i<=1e-12,grid_voltage=max(maxima)<=.005,
               frequency=cents<=1.,reset_count=same,reset_timing=timing is not None and timing<=1e-8)
    return dict(passed=all(gates.values()),gates=gates,grid_step_s=5e-6,grid_points=len(grid),
                voltage_maxima_v=maxima,dc_voltage_max_v=dc_v,dc_port_current_difference_a=dc_i,
                frequencies_hz=frequencies,frequency_difference_cents=cents,
                reset_counts=[len(x) for x in events],max_reset_time_difference_s=timing,
                reset_crossings_s=[x.tolist() for x in events],phase_alignment=False)
