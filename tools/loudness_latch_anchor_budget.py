"""Exact conditional anchor capacity of frozen node/cell affine upper bounds."""
from fractions import Fraction as F

def constraints(trace,metrics):
    if not trace or len(trace)!=len(metrics):raise ValueError('complete trace and matching maps required')
    rows=[];last=F(0)
    for cell,(t,m) in enumerate(zip(trace,metrics)):
        left,right=F(t['left']),F(t['right'])
        if left!=last or right<=left:raise ValueError('contiguous positive cells required')
        a=list(map(F,t['peak_anchor']));f=list(map(F,t['peak_forced_v']))
        g=[[F(v) for v in row] for row in m['nodal_block_gains']];d=list(map(F,m['nodal_direct_v']))
        if not a or len(f)!=len(a) or not g or len(g)!=len(d) or any(len(row)!=len(a) for row in g):raise ValueError('complete nodal maps and peak vectors required')
        if any(v<0 for v in a+f+d+[v for row in g for v in row]):raise ValueError('nonnegative affine coefficients required')
        current=[]
        for node,(gain,direct) in enumerate(zip(g,d)):
            anchor=sum((v*w for v,w in zip(gain,a)),F(0));forced=direct+sum((v*w for v,w in zip(gain,f)),F(0))
            current.append(dict(cell_index=cell,node_row_index=node,anchor_gain=str(anchor),forced_upper_v=str(forced)))
        if max(F(v['anchor_gain']) for v in current)!=F(t['peak_node_anchor']) or max(F(v['forced_upper_v']) for v in current)!=F(t['peak_node_forced_v']):raise ValueError('archived nodal maxima differ')
        rows.extend(current);last=right
    if last!=1:raise ValueError('complete normalized interval required')
    return rows

def capacity(rows,threshold,reserve=F(0)):
    threshold,reserve=F(threshold),F(reserve)
    if threshold<=0 or reserve<0 or reserve>threshold:raise ValueError('positive threshold and reserve inside threshold required')
    if not rows:raise ValueError('nonempty affine family required')
    seen=set();limits=[];violations=[]
    for row in rows:
        key=(row['cell_index'],row['node_row_index'])
        if any(not isinstance(v,int) or isinstance(v,bool) or v<0 for v in key) or key in seen:raise ValueError('unique nonnegative integer cell/node identities required')
        seen.add(key);a,f=F(row['anchor_gain']),F(row['forced_upper_v'])
        if a<0 or f<0:raise ValueError('nonnegative affine coefficients required')
        margin=threshold-reserve-f
        if margin<0:violations.append(dict(cell_index=key[0],node_row_index=key[1]))
        if a>0:limits.append((margin/a,key))
    if violations:
        return dict(status='infeasible',anchor_upper_v=None,binding_constraints=[],zero_anchor_violations=violations)
    if not limits:
        return dict(status='unbounded',anchor_upper_v=None,binding_constraints=[],zero_anchor_violations=[])
    limit=min(v for v,key in limits)
    return dict(status='finite',anchor_upper_v=str(limit),binding_constraints=[dict(cell_index=key[0],node_row_index=key[1]) for v,key in limits if v==limit],zero_anchor_violations=[])

def separated_capacity(rows,threshold,reserve=F(0)):
    if not rows:raise ValueError('nonempty affine family required')
    synthetic=dict(cell_index=0,node_row_index=0,anchor_gain=str(max(F(r['anchor_gain']) for r in rows)),forced_upper_v=str(max(F(r['forced_upper_v']) for r in rows)))
    return capacity([synthetic],threshold,reserve)
