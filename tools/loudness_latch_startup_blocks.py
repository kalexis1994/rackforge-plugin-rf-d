"""Known vector anchors and fixed whole-interval junction metrics, offline only."""
from fractions import Fraction as F
import loudness_latch_block_comparison as blocks
import loudness_latch_junction_rms as rms
import loudness_latch_junction_metric as quadratic
import loudness_latch_junction_directed as directed
import loudness_latch_junction_balanced as balanced

MODES=('infinity','rms','quadratic_balanced')

def generator(inverse,weights):
    w=list(map(F,weights));j=blocks.BLOCKS[5]
    return [[(-w[i]/w[k]*F(inverse[94+i][94+k][1]),-w[i]/w[k]*F(inverse[94+i][94+k][0])) for k in j] for i in j]

def initial_vector(anchor,mode,metric=None):
    if mode not in MODES:raise ValueError('registered fixed norm required')
    rows=anchor['rows']
    if len(rows)!=25 or [r['index'] for r in rows]!=list(range(25)):raise ValueError('complete ordered charge anchor required')
    bounds=[F(r['weighted_error_upper_v']) for r in rows]
    if min(bounds)<0:raise ValueError('nonnegative initial errors required')
    result=[max(bounds[i] for i in group) for group in blocks.BLOCKS]
    if mode=='rms':result[5]=rms.norm2_upper(bounds[21:])/2
    elif mode=='quadratic_balanced':
        if not metric or not metric['accepted']:raise ValueError('accepted whole-interval metric required')
        p=[[F(v) for v in row] for row in metric['metric']]
        # Signed coordinate enclosure, derived from the archived C/V and weights.
        # scale = coordinate_error/charge_error when nonzero; use symmetric
        # weighted coordinate bounds to avoid division by zero at zero charge.
        result[5]=quadratic.quadratic_upper(p,[(-v,v) for v in bounds[21:]])/(2*F(metric['anchor_normalization_upper']))
    return list(map(str,result))

def cell_metrics(inverse,weights,forcing,mode,metric=None,prepared=None,balance=None):
    if mode=='infinity':return blocks.block_metrics(inverse,94,weights,forcing),None
    if mode=='rms':return rms.block_metrics(inverse,94,weights,forcing),None
    if mode!='quadratic_balanced':raise ValueError('registered fixed norm required')
    b=generator(inverse,weights);iso=quadratic.rate(metric,b)
    direct=directed.rate(metric,b,iso,prepared);tight=balanced.rate(prepared,direct,balance)
    old=blocks.block_metrics(inverse,94,weights,forcing)
    metrics=quadratic.metrics(inverse,weights,forcing,old,metric,iso)
    return balanced.refine_metrics(metrics,tight),dict(isotropic=iso,directed=direct,balanced=tight)

def propagate(cells,initial):
    if not cells:raise ValueError('nonempty propagation required')
    n=len(cells[0]['metrics']['comparison_per_s']);anchor=list(map(F,initial));forced=[F(0)]*n
    if len(anchor)!=n or min(anchor)<0:raise ValueError('complete nonnegative anchor vector required')
    trace=[];last=F(0);peak=F(0);anchor_peak=F(0);forced_peak=F(0)
    for cell in cells:
        m=cell['metrics'];f=cell['forcing_inputs'];left,right=F(f['left']),F(f['right'])
        if not cell.get('inverse_certified',False):raise ValueError('all mean descriptors must be certified')
        if left!=last or right<=left:raise ValueError('contiguous positive partition required')
        e,p,cert=blocks.kernels(m['comparison_per_s'],f['duration_s'])
        b=list(map(F,m['block_forcing_l1_v']));g=[[F(v) for v in row] for row in m['nodal_block_gains']];d=list(map(F,m['nodal_direct_v']))
        if len(e)!=n or len(b)!=n or not g or len(g)!=len(d) or any(len(row)!=n for row in g) or min(b+d+[v for row in g for v in row])<0:raise ValueError('complete nonnegative budgets required')
        pa=blocks.apply(p,anchor);pf=blocks.apply(p,[v+q for v,q in zip(forced,b)])
        na=[sum((v*a for v,a in zip(row,pa)),F(0)) for row in g]
        nf=[sum((v*a for v,a in zip(row,pf)),F(0))+di for row,di in zip(g,d)]
        node=max(a+q for a,q in zip(na,nf));peak=max(peak,node)
        anchor_peak=max(anchor_peak,max(na));forced_peak=max(forced_peak,max(nf))
        anchor=blocks.apply(e,anchor);fb=blocks.apply(p,b)
        forced=[blocks.up(a+q) for a,q in zip(blocks.apply(e,forced),fb)]
        trace.append(dict(left=str(left),right=str(right),kernel_certificate=cert,endpoint_kernel=blocks.pack(e),peak_kernel=blocks.pack(p),
            peak_anchor_v=list(map(str,pa)),peak_forced_v=list(map(str,pf)),endpoint_anchor_v=list(map(str,anchor)),endpoint_forced_v=list(map(str,forced)),
            node_anchor_v=list(map(str,na)),node_forced_v=list(map(str,nf)),peak_node_error_upper_v=str(node)))
        last=right
    if last!=1:raise ValueError('complete normalized interval required')
    return dict(trace=trace,initial_block_error_upper_v=list(map(str,initial)),endpoint_anchor_v=list(map(str,anchor)),endpoint_forced_v=list(map(str,forced)),
        peak_node_error_upper_v=str(peak),peak_node_anchor_part_upper_v=str(anchor_peak),peak_node_forcing_part_upper_v=str(forced_peak),
        initial_error_known=True,mean_descriptor_comparison=True,actual_dae_error_bound=False)

def close(cells,initial,radius,initial_node):
    radius=F(radius);initial_node=F(initial_node)
    if radius<=0 or initial_node<0:raise ValueError('positive radius and nonnegative nodal origin required')
    try:result=propagate(cells,initial)
    except ValueError as error:return dict(accepted=False,reason=str(error),actual_dae_error_bound=False)
    peak=max(initial_node,F(result['peak_node_error_upper_v']));accepted=peak<radius
    return dict(accepted=accepted,reason=None if accepted else 'comparison bound escapes assumed potential tube',
        radius_v=str(radius),initial_node_error_upper_v=str(initial_node),peak_node_error_upper_v=str(peak),propagation=result,
        nonlinear_tube_self_consistent=accepted,actual_dae_error_bound=accepted,global_1mv_gate_closed=False)
