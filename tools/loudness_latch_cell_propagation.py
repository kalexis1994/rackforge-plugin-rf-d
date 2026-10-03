"""First-order interval Neumann inverse and contiguous cell tangent budgets."""
from fractions import Fraction as F
from hashlib import sha256
from loudness_latch_bdf_doubling_survey import canonical
from loudness_latch_charge_enclosure import exp_bounds
import loudness_latch_dense_charge as poly


def packed_matrix(a):return [[[str(lo),str(hi)] for lo,hi in row] for row in a]
def matrix_hash(a):return sha256(canonical(packed_matrix(a))).hexdigest()


def dyadic_exponent(v):
    v=F(v);d=v.denominator
    if d&(d-1):raise ValueError('exact dyadic input required')
    return d.bit_length()-1


def interval_dyadic_product(a,b):
    """Exact signed dot products via common integer denominators, no rounding."""
    n=len(a)
    if not n or len(b)!=n or any(len(row)!=n for row in a) or any(len(row)!=n for row in b):
        raise ValueError('complete square product required')
    aa=[[tuple(map(F,v)) for v in row] for row in a];bb=[[F(v) for v in row] for row in b]
    if any(lo>hi for row in aa for lo,hi in row):raise ValueError('ordered interval required')
    pa=max(dyadic_exponent(v) for row in aa for ab in row for v in ab)
    ints=[[(v[0].numerator<<(pa-dyadic_exponent(v[0])),v[1].numerator<<(pa-dyadic_exponent(v[1]))) for v in row] for row in aa]
    out=[[(F(0),F(0)) for _ in range(n)] for _ in range(n)]
    for j in range(n):
        pb=max(dyadic_exponent(bb[k][j]) for k in range(n));den=1<<(pa+pb)
        col=[(k,bb[k][j].numerator<<(pb-dyadic_exponent(bb[k][j]))) for k in range(n) if bb[k][j]]
        for i,row in enumerate(ints):
            low=sum((row[k][0 if v>0 else 1]*v for k,v in col),0)
            high=sum((row[k][1 if v>0 else 0]*v for k,v in col),0)
            out[i][j]=(F(low,den),F(high,den))
    return out


def structured_inverse(inverse,scales,cover,parent_q):
    xx=[[F(v) for v in row] for row in inverse];d=list(map(F,scales));n=len(xx)
    if len(d)!=n or any(v<=0 for v in d):raise ValueError('positive complete scales required')
    e=[[tuple(map(F,v)) for v in row] for row in cover['preconditioned_defect_intervals']]
    rows=[sum((max(map(abs,v)) for v in row),F(0)) for row in e];q=max(rows);parent_q=F(parent_q)
    if q!=F(cover['contraction_upper']) or q>=1 or not q<=parent_q<1:raise ValueError('consistent contracted parent cover required')
    y=[[d[i]*v for v in row] for i,row in enumerate(xx)]
    correction=interval_dyadic_product(e,y);peaks=[max(abs(y[k][j]) for k in range(n)) for j in range(n)]
    raw=[];final=[];changed=0;zeros=0
    for i in range(n):
        rrow=[];frow=[]
        for j in range(n):
            tail=rows[i]*q/(1-q)*peaks[j]
            lo=(y[i][j]+correction[i][j][0]-tail)/d[i]
            hi=(y[i][j]+correction[i][j][1]+tail)/d[i]
            row_error=rows[i]/(1-q)*peaks[j]/d[i]
            parent_error=parent_q/(1-parent_q)*peaks[j]/d[i]
            a=max(lo,xx[i][j]-row_error,xx[i][j]-parent_error)
            b=min(hi,xx[i][j]+row_error,xx[i][j]+parent_error)
            if a>b:raise ValueError('empty inverse enclosure intersection')
            rrow.append((lo,hi));frow.append((a,b))
            changed+=b-a<2*parent_error;zeros+=a==b==0
        raw.append(rrow);final.append(frow)
    return final,dict(order=1,contraction_upper=str(q),row_defect_upper=list(map(str,rows)),
        raw_inverse_sha256=matrix_hash(raw),final_inverse_sha256=matrix_hash(final),
        final_inside_prior_global_inverse=True,strictly_narrower_entries=changed,exact_zero_entries=zeros,
        remaining_tail_policy='row_defect*q/(1-q)*column_peak/D_i')


def residual_cells(parent,correlated,equations,duration,count=8):
    duration=F(duration)
    if duration<=0 or len(parent['cells_a'])!=count:raise ValueError('positive complete residual partition required')
    out=[];active=correlated['active_nodes']
    for index in range(count):
        left=F(index,count);right=F(index+1,count);width=right-left
        point=[max(map(abs,map(F,v))) for v in parent['cells_a'][index]]
        l1=[duration*width*v for v in point]
        slices=[]
        for seg in correlated['segments']:
            a=max(left,F(seg['left']));b=min(right,F(seg['right']))
            if a<b:slices.append((a,b,seg))
        slices.sort(key=lambda v:v[0])
        if not slices or slices[0][0]!=left or slices[-1][1]!=right or any(a[1]!=b[0] for a,b in zip(slices,slices[1:])):
            raise ValueError('active residual segments leave a gap or overlap')
        for k,node in enumerate(active):
            values=[(a,b,max(map(abs,map(F,seg['active_a'][k])))) for a,b,seg in slices]
            point[node]=max(v for _,_,v in values);l1[node]=duration*sum(((b-a)*v for a,b,v in values),F(0))
        dpoint=[max(map(abs,poly.bernstein(p,left,right))) for p in equations]+[F(0)]*4
        out.append(dict(left=str(left),right=str(right),duration_s=str(duration*width),
            nodal_point_a=list(map(str,point)),nodal_l1_c=list(map(str,l1)),
            constraint_point_v=list(map(str,dpoint)),constraint_l1_v_s=list(map(str,[duration*width*v for v in dpoint]))))
    return out


def metrics(inverse,nv,weights,forcing):
    n=len(inverse);nm=n-nv;w=list(map(F,weights))
    if len(w)!=nm or any(v<=0 for v in w):raise ValueError('positive complete weights required')
    absolute=[[max(map(abs,v)) for v in row] for row in inverse]
    mu=max(-inverse[nv+i][nv+i][0]+sum((w[i]/w[j]*absolute[nv+i][nv+j] for j in range(nm) if j!=i),F(0)) for i in range(nm))
    values=list(map(F,forcing['nodal_l1_c']+forcing['constraint_l1_v_s']))
    point=list(map(F,forcing['nodal_point_a']+forcing['constraint_point_v']))
    if len(values)!=n or len(point)!=n or any(v<0 for v in values+point):raise ValueError('complete nonnegative forcing required')
    budget=sum((max(w[i]*absolute[nv+i][j] for i in range(nm))*v for j,v in enumerate(values)),F(0))
    gain=max(sum((absolute[i][nv+j]/w[j] for j in range(nm)),F(0)) for i in range(nv))
    direct=max(sum((a*v for a,v in zip(row,point)),F(0)) for row in absolute[:nv])
    return dict(logarithmic_norm_upper_per_s=str(mu),integrated_forcing_norm_upper_v=str(budget),
        node_from_weighted_memory_gain_upper=str(gain),node_direct_forcing_upper_v=str(direct))


def propagate(cells):
    if not cells:raise ValueError('nonempty contiguous cell propagation required')
    anchor=F(1);forced=F(0);node_anchor=F(0);node_forced=F(0);memory_peak=F(0);trace=[];end=F(0)
    for cell in cells:
        f=cell['forcing_inputs'];m=cell['metrics'];left=F(f['left']);right=F(f['right']);h=F(f['duration_s'])
        if left!=end or right<=left or h<=0:raise ValueError('contiguous positive cells required')
        mu=F(m['logarithmic_norm_upper_per_s']);b=F(m['integrated_forcing_norm_upper_v']);l=F(m['node_from_weighted_memory_gain_upper']);r=F(m['node_direct_forcing_upper_v'])
        if min(b,l,r)<0:raise ValueError('nonnegative budgets and gains required')
        exponent=mu*h
        if abs(exponent)>4096:raise ValueError('cell exponential domain >4096')
        end_gain=exp_bounds(exponent)[1];peak_gain=exp_bounds(max(exponent,F(0)))[1]
        peak_anchor=peak_gain*anchor;peak_forced=peak_gain*(forced+b)
        node_anchor=max(node_anchor,l*peak_anchor);node_forced=max(node_forced,l*peak_forced+r)
        memory_peak=max(memory_peak,peak_forced)
        anchor=end_gain*anchor;forced=end_gain*forced+peak_gain*b
        trace.append(dict(left=str(left),right=str(right),signed_growth_exponent=str(exponent),
            endpoint_gain_upper=str(end_gain),peak_gain_upper=str(peak_gain),
            endpoint_weighted_anchor_gain_upper=str(anchor),endpoint_zero_anchor_memory_upper_v=str(forced),
            peak_weighted_anchor_gain_upper=str(peak_anchor),peak_zero_anchor_memory_upper_v=str(peak_forced),
            peak_node_anchor_gain_upper=str(l*peak_anchor),peak_zero_anchor_node_upper_v=str(l*peak_forced+r)))
        end=right
    if end!=1:raise ValueError('complete normalized interval required')
    return dict(trace=trace,endpoint_weighted_anchor_gain_upper=str(anchor),
        endpoint_zero_anchor_memory_upper_v=str(forced),peak_zero_anchor_memory_upper_v=str(memory_peak),
        peak_node_from_weighted_anchor_gain_upper=str(node_anchor),peak_zero_anchor_node_upper_v=str(node_forced),
        initial_error_known=False,nonlinear_remainder_bound=False,actual_dae_error_bound=False)
