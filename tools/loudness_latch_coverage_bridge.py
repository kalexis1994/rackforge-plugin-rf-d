"""Exact interval inventory, archived state lineage and fixed norm conversions."""
from fractions import Fraction as F
import hashlib
from loudness_latch_bdf_doubling_survey import canonical
import loudness_latch_junction_metric as metric
from loudness_latch_spectral_junction import ldlt
BISECTIONS=32
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()

def coverage(spans,start,end):
    start,end=F(start),F(end)
    if end<=start:raise ValueError('positive coverage domain required')
    values=sorted((F(a),F(b)) for a,b in spans)
    if any(a<start or b>end or b<=a for a,b in values):raise ValueError('positive spans inside domain required')
    union=[]
    for a,b in values:
        if union and a<=union[-1][1]:union[-1][1]=max(b,union[-1][1])
        else:union.append([a,b])
    gaps=[];left=start
    for a,b in union:
        if left<a:gaps.append([left,a])
        left=b
    if left<end:gaps.append([left,end])
    covered=sum((b-a for a,b in union),F(0));missing=sum((b-a for a,b in gaps),F(0))
    if covered+missing!=end-start:raise ValueError('coverage conservation failed')
    pack=lambda xs:[[str(a),str(b)] for a,b in xs]
    return dict(domain_s=[str(start),str(end)],input_span_count=len(values),raw_duration_s=str(sum((b-a for a,b in values),F(0))),
        union_s=pack(union),gaps_s=pack(gaps),covered_duration_s=str(covered),missing_duration_s=str(missing),covered_fraction=str(covered/(end-start)),complete=not gaps)

def lineage(initial,rows):
    if not rows:raise ValueError('nonempty archived chain required')
    old=initial;trace=[]
    for index,row in enumerate(rows):
        new=row['history'];dt=row['diagnostics']['actual_dt_s'];left,right=F(old['time_s']),F(new['time_s'])
        if row['previous_history_sha256']!=digest(old):raise ValueError('incoming history identity differs')
        if dt<=0 or right<=left or new['time_s']!=old['time_s']+dt:raise ValueError('published clock closure differs')
        if canonical(new['previous'])!=canonical(old['current']) or new['previous_key_v']!=old['key_v'] or new['previous_dt_s']!=dt:raise ValueError('complete multistep history differs')
        trace.append(dict(index=index,left_s=str(left),right_s=str(right),incoming_sha256=digest(old),history_sha256=digest(new)))
        old=new
    return dict(initial_sha256=digest(initial),final_sha256=digest(old),interval_count=len(trace),trace=trace,
        domain_s=[str(F(initial['time_s'])),str(F(old['time_s']))],numerical_lineage_verified=True,entry_error_bound_proven=False)

def gram(candidate,weights):
    if not candidate['accepted']:raise ValueError('accepted positive metric required')
    w=list(map(F,weights));p=[[F(v) for v in row] for row in candidate['metric']];a=F(candidate['anchor_normalization_upper'])
    if len(w)!=25 or any(v<=0 for v in w) or w[:21]!=[F(1)]*21 or len(p)!=4 or any(len(row)!=4 for row in p) or a<=0:raise ValueError('fixed 21 linear and four junction coordinates required')
    g=[[w[21+i]*p[i][j]*w[21+j]/(4*a*a) for j in range(4)] for i in range(4)]
    if any(g[i][j]!=g[j][i] for i in range(4) for j in range(4)) or not ldlt(g)['positive_definite']:raise ValueError('positive symmetric Gram matrix required')
    return dict(gram=metric.pack(g),inverse_gram=metric.pack(metric.invert(g)),pd_proof=ldlt(g),candidate_sha256=digest(candidate),weights=list(map(str,w)),
        common_error_vector='four junction charge-memory errors scaled by the unchanged S',other_five_blocks_unchanged=True)

def bridge(source,destination):
    g=[[F(v) for v in row] for row in source['gram']];h=[[F(v) for v in row] for row in destination['gram']]
    if len(g)!=4 or len(h)!=4 or any(len(row)!=4 for row in g+h):raise ValueError('complete four-coordinate Gram matrices required')
    if any(g[i][j]!=g[j][i] or h[i][j]!=h[j][i] for i in range(4) for j in range(4)) or not ldlt(g)['positive_definite'] or not ldlt(h)['positive_definite']:raise ValueError('positive symmetric source and destination required')
    common=dict(source_sha256=digest(source),destination_sha256=digest(destination),same_error_vector_only=True,actual_interface_verified=False,missing_region_propagation_proven=False)
    if g==h:return common|dict(identity=True,squared_upper='1',junction_gain_upper='1',full_block_gain_upper='1',probes=[],final_upper_ldlt=None)
    inverse=metric.invert(g);lo=max(h[i][i]/g[i][i] for i in range(4));hi=max(sum(map(abs,row)) for row in h)*max(sum(map(abs,row)) for row in inverse)+1
    seed_lo,seed_hi=lo,hi;probes=[]
    def query(alpha):return ldlt([[alpha*g[i][j]-h[i][j] for j in range(4)] for i in range(4)])
    def log(alpha,proof):return dict(alpha_squared=str(alpha),positive_definite=proof['positive_definite'],failed_at=proof['failed_at'],pivot_sha256=digest(proof['pivots']))
    proof=query(hi)
    if not proof['positive_definite']:raise ValueError('strict norm-conversion seed failed')
    probes.append(log(hi,proof))
    for _ in range(BISECTIONS):
        alpha=(lo+hi)/2;test=query(alpha);probes.append(log(alpha,test))
        if test['positive_definite']:hi=alpha;proof=test
        else:lo=alpha
    bracket=metric.sqrt_bounds(hi);gain=bracket[1]
    return common|dict(identity=False,seed_lower_squared=str(seed_lo),seed_upper_squared=str(seed_hi),auxiliary_lower_squared=str(lo),squared_upper=str(hi),
        square_root_bracket=list(map(str,bracket)),junction_gain_upper=str(gain),full_block_gain_upper=str(max(F(1),gain)),
        probes=probes,bisections=BISECTIONS,final_upper_ldlt=proof)
