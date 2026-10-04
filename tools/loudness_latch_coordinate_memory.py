"""Certified scalar outgoing-memory refinement and 22-group comparison."""
from fractions import Fraction as F
import loudness_latch_startup_blocks as prior
blocks=prior.blocks
quadratic=prior.quadratic
GROUPS=tuple((i,) for i in range(21))+(tuple(range(21,25)),)

def fine_metrics(inverse,weights,forcing,metric,mu):
    if not metric['accepted']:raise ValueError('accepted fixed junction metric required')
    w=list(map(F,weights));n=len(inverse);nv=94;junction=range(21,25)
    if n!=119 or len(w)!=25 or any(v<=0 for v in w) or any(len(row)!=n for row in inverse):raise ValueError('complete fixed circuit coordinates required')
    inverse=[[quadratic.box.interval(v) for v in row] for row in inverse]
    absolute=[[max(map(abs,v)) for v in row] for row in inverse]
    p=[[F(v) for v in row] for row in metric['metric']];pi=[[F(v) for v in row] for row in metric['inverse_metric']]
    normal=2*F(metric['anchor_normalization_upper'])
    if normal<=0 or not quadratic.ldlt(p)['positive_definite']:raise ValueError('positive fixed norm required')
    values=list(map(F,forcing['nodal_l1_c']+forcing['constraint_l1_v_s']));point=list(map(F,forcing['nodal_point_a']+forcing['constraint_point_v']))
    if len(values)!=n or len(point)!=n or min(values+point)<0:raise ValueError('complete nonnegative forcing required')
    def scale(v,f):return quadratic.box.mul(v,(f,f))
    m=[[F(0)]*22 for _ in range(22)]
    for i in range(21):
        for k in range(21):m[i][k]=-inverse[nv+i][nv+i][0] if i==k else w[i]/w[k]*absolute[nv+i][nv+k]
        m[i][21]=normal*quadratic.quadratic_upper(pi,[scale(inverse[nv+i][nv+k],w[i]/w[k]) for k in junction])
        m[21][i]=quadratic.quadratic_upper(p,[scale(inverse[nv+k][nv+i],w[k]/w[i]) for k in junction])/normal
    m[21][21]=F(mu)
    forcing_budget=[sum((w[i]*absolute[nv+i][k]*v for k,v in enumerate(values)),F(0)) for i in range(21)]
    forcing_budget.append(sum((quadratic.quadratic_upper(p,[scale(inverse[nv+i][k],w[i]) for i in junction])*v for k,v in enumerate(values)),F(0))/normal)
    gains=[[absolute[i][nv+k]/w[k] for k in range(21)]+[normal*quadratic.quadratic_upper(pi,[scale(inverse[i][nv+k],1/w[k]) for k in junction])] for i in range(nv)]
    direct=[sum((absolute[i][k]*v for k,v in enumerate(point)),F(0)) for i in range(nv)]
    return dict(comparison_per_s=blocks.pack(m),block_forcing_l1_v=list(map(str,forcing_budget)),nodal_block_gains=blocks.pack(gains),nodal_direct_v=list(map(str,direct)),
        norm_policy=metric['metric_norm'],junction_mu_reused_per_s=str(F(mu)),partition='21 individual weighted linear coordinates plus fixed quadratic junction group')

def scalar_refine(initial,diagonal,injection,old_endpoint,duration):
    initial,injection,old_endpoint=map(F,(initial,injection,old_endpoint));h=F(duration)
    if min(initial,injection,old_endpoint)<0 or h<=0:raise ValueError('nonnegative known scalar bounds and positive duration required')
    e,p,cert=blocks.kernels([[F(diagonal)]],h);raw=blocks.up(e[0][0]*initial+p[0][0]*injection);final=min(raw,old_endpoint)
    return dict(initial_error_upper_v=str(initial),diagonal_upper_per_s=str(F(diagonal)),injection_l1_upper_v=str(injection),
        previous_endpoint_upper_v=str(old_endpoint),raw_endpoint_upper_v=str(raw),endpoint_upper_v=str(final),
        endpoint_kernel=blocks.pack(e),peak_kernel=blocks.pack(p),kernel_certificate=cert,same_coordinate_intersection=True)

def lift(previous):
    if not previous['accepted'] or not previous['actual_dae_error_bound']:raise ValueError('actual preceding interval certificate required')
    p=previous['propagation'];a=list(map(F,p['endpoint_anchor_v']));b=list(map(F,p['endpoint_forced_v']))
    if len(a)!=6 or len(b)!=6 or min(a+b)<0:raise ValueError('six known outgoing groups required')
    u=[x+y for x,y in zip(a,b)]
    return list(map(str,[u[0]]*17+u[1:5]+[u[5]]))

def refine(initial,previous,cells):
    coarse=list(map(F,lift(previous)));values=list(map(F,initial))
    if len(values)!=21 or min(values)<0 or len(cells)!=len(previous['propagation']['trace']):raise ValueError('complete individual anchor and certified profiles required')
    trace=[];last=F(0)
    for cell,profile in zip(cells,previous['propagation']['trace']):
        f=cell['forcing_inputs'];m=cell['metrics'];left,right=F(f['left']),F(f['right'])
        if left!=last or right<=left or profile['left']!=f['left'] or profile['right']!=f['right']:raise ValueError('same contiguous certified support required')
        matrix=[[F(v) for v in row] for row in m['comparison_per_s']];budget=list(map(F,m['block_forcing_l1_v']));h=F(f['duration_s'])
        if len(matrix)!=22 or any(len(row)!=22 for row in matrix) or len(budget)!=22:raise ValueError('complete fine comparison required')
        peaks=[F(a)+F(b) for a,b in zip(profile['peak_anchor_v'],profile['peak_forced_v'])]
        ends=[F(a)+F(b) for a,b in zip(profile['endpoint_anchor_v'],profile['endpoint_forced_v'])]
        if len(peaks)!=6 or len(ends)!=6 or min(peaks+ends+budget)<0:raise ValueError('known nonnegative profiles required')
        mapped=[peaks[0]]*17+peaks[1:5]+[peaks[5]];rows=[]
        for i in range(21):
            coupling=sum((matrix[i][k]*mapped[k] for k in range(22) if k!=i),F(0))
            if coupling<0:raise ValueError('nonnegative directed couplings required')
            old=ends[0 if i<17 else i-16]
            row=scalar_refine(values[i],matrix[i][i],budget[i]+h*coupling,old,h)
            rows.append(dict(index=i,forcing_l1_upper_v=str(budget[i]),other_coordinates_rate_upper_v_s=str(coupling),scalar=row))
        values=[F(row['scalar']['endpoint_upper_v']) for row in rows]
        trace.append(dict(left=f['left'],right=f['right'],known_group_peaks_v=list(map(str,peaks)),rows=rows));last=right
    if last!=1:raise ValueError('complete certified interval required')
    final=values+[coarse[21]]
    return dict(trace=trace,coarse_outgoing_v=list(map(str,coarse)),refined_outgoing_v=list(map(str,final)),
        improved_linear_coordinates=sum(a<b for a,b in zip(values,coarse[:21])),initial_linear_error_upper_v=list(map(str,initial)),
        outgoing_memory_refinement_proven=True,dc_anchor_reset=False,junction_norm_changed=False)
