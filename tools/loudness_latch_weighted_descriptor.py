"""Weighted infinity norm and ideal descriptor interval proof, offline only."""
from fractions import Fraction as F
import loudness_latch_constitutive_enclosure as iv
import loudness_latch_dense_charge as poly
from loudness_latch_charge_enclosure import exp_bounds
CELLS=8


def dyadic_floor(value):
    v=F(value)
    if v<=0:raise ValueError('positive weight source required')
    k=v.numerator.bit_length()-v.denominator.bit_length()
    p=F(2)**k
    if p>v:p/=2
    if not p<=v<2*p:raise ValueError('dyadic weight bracket failed')
    return p


def weights(h,nv=94):
    out=[F(1)]*21
    for row in h[nv+21:]:
        cap_ratio=max(abs(F(v)) for v in row[:nv])
        out.append(dyadic_floor(1/cap_ratio))
    if len(out)!=25:raise ValueError('25 frozen memory weights required')
    return out


def weighted_budget(x,errors,nv,w,r_l1,d_l1,r_point,d_point,duration,time_varying=False):
    nm=len(x)-nv;w=list(map(F,w));duration=F(duration)
    if len(w)!=nm or any(v<=0 for v in w) or duration<=0:raise ValueError('positive complete weights and duration required')
    groups=(r_l1,d_l1,r_point,d_point)
    if any(len(v)!=n for v,n in zip(groups,(nv,nm,nv,nm))) or any(F(t)<0 for v in groups for t in v):
        raise ValueError('complete nonnegative forcing required')
    xx=[[F(v) for v in row] for row in x]
    absolute=[[abs(v)+e for v,e in zip(row,err)] for row,err in zip(xx,errors)]
    mu=max(-xx[nv+i][nv+i]+errors[nv+i][nv+i]+
           sum((w[i]/w[j]*absolute[nv+i][nv+j] for j in range(nm) if j!=i),F(0)) for i in range(nm))
    budget=sum((max(w[i]*absolute[nv+i][j] for i in range(nm))*F(v)
                for j,v in enumerate((*r_l1,*d_l1))),F(0))
    node_gain=max(sum((absolute[i][nv+j]/w[j] for j in range(nm)),F(0)) for i in range(nv))
    direct=max(sum((a*F(v) for a,v in zip(row,(*r_point,*d_point))),F(0)) for row in absolute[:nv])
    exponent=max(mu,F(0))*duration
    result=dict(weights=list(map(str,w)),norm='max_i |w_i*y_i|',logarithmic_norm_upper_per_s=str(mu),
        integrated_forcing_norm_upper_v=str(budget),growth_exponent_upper=str(exponent),
        node_from_weighted_memory_gain_upper=str(node_gain),node_direct_forcing_upper_v=str(direct),
        anchor_known=False,nonlinear_remainder_bound=False,time_varying_operator_bound=time_varying)
    if exponent>4096:return result|dict(growth_supported=False,unsupported_reason='exponential domain >4096')
    gain=exp_bounds(exponent)[1];forced=gain*budget
    return result|dict(growth_supported=True,weighted_anchor_gain_upper=str(gain),
        node_from_unweighted_anchor_gain_upper=str(node_gain*gain*max(w)),
        zero_anchor_forced_weighted_memory_upper_v=str(forced),
        zero_anchor_forced_node_upper_v=str(node_gain*forced+direct))


def compile_terms(network,g,prepared,inverse,scales):
    """Rank-one analytic stamps, preconditioned before enclosing each scalar law."""
    x=[[F(v) for v in row] for row in inverse];d=list(map(F,scales));n=len(x);nv=g['node_count'];terms=[]
    def voltage(i):return prepared['x'][i] if isinstance(i,int) else (F(g['fixed'][i]),)
    def incidence(a,b):
        result={}
        for node,value in ((a,F(1)),(b,-F(1))):
            if isinstance(node,int):result[node]=result.get(node,F(0))+value
        return {k:v for k,v in result.items() if v}
    def difference(a,b):return poly.add(voltage(a),poly.scale(voltage(b),-1))
    def append(ref,rows,columns,kind,**data):
        coeff=[]
        for i in range(n):
            value=d[i]*sum((x[i][k]*v for k,v in rows.items()),F(0))
            if value:
                for j,c in columns.items():
                    if c:coeff.append((i,j,value*c/d[j]))
        terms.append(dict(ref=ref,coefficients=coeff,kind=kind,**data))
    for r in g['resistors']+g['conductances']:
        a=incidence(r['left'],r['right']);value=1/F(r['ohm']) if 'ohm' in r else F(r['siemens'])
        append(r['ref'],a,a,'constant',value=value)
    for q in g['bjts']:
        b,c,e=q['base'],q['collector'],q['emitter'];bf=F(q['beta_forward']);br=F(q['beta_reverse']);vt=F(q['vt'])
        for suffix,other,stamps in (('BE',e,((b,1/bf),(c,F(1)),(e,-1-1/bf))),
                                    ('BC',c,((b,1/br),(c,-1-1/br),(e,F(1))))):
            rows={}
            for node,v in stamps:
                if isinstance(node,int):rows[node]=rows.get(node,F(0))+v
            append(q['ref']+'/'+suffix,rows,incidence(b,other),'exponential',
                power=poly.scale(difference(b,other),F(q['polarity'])/vt),factor=F(q['is_a'])/vt)
    for q in g['diodes']:
        a=incidence(q['anode'],q['cathode']);vt=F(q['ideality'])*F(q['vt'])
        append(q['ref'],a,a,'exponential',power=poly.scale(difference(q['anode'],q['cathode']),1/vt),factor=F(q['is_a'])/vt)
    net=network.network
    for k,(left,right,_,cap,resistance) in enumerate(net.branches):
        a=incidence(left,right)
        append('linear-mass/'+str(k),a,{nv+k:F(1)},'constant',value=F(cap))
        append('linear-constraint/'+str(k),{nv+k:-F(1)},a,'constant',value=F(1))
        if resistance:append('series-tau/'+str(k),{nv+k:F(1)},{nv+k:F(1)},'constant',value=F(cap)*F(resistance))
    p=net.latch.device.parameters;s=F(p.polarity);scale=F(1e-12)
    for k,terminals in enumerate(net.latch.terminals):
        b,c,e=[i for i,_ in terminals]
        for index,other,junction in ((21+2*k,e,prepared['junctions'][2*k]),(22+2*k,c,prepared['junctions'][2*k+1])):
            a={i:s*v for i,v in incidence(b,other).items()}
            append('junction-mass/'+str(index),a,{nv+index:F(1)},'constant',value=scale)
            v,dep,t,em=junction
            append('junction-constraint/'+str(index),{nv+index:-1/scale},a,'capacitance',
                power=v,depletion=dep,transit=t,saturation=p.saturation_a,emission=em)
    constant=[[(F(0),F(0)) for _ in range(n)] for _ in range(n)];variable=[]
    for t in terms:
        if t['kind']!='constant':variable.append(t);continue
        for i,j,c in t['coefficients']:constant[i][j]=iv.add(constant[i][j],(c*t['value'],c*t['value']))
    return constant,variable


def preconditioned_cover(constant,terms,left,right):
    n=len(constant);product=[[v for v in row] for row in constant];diagnostics=[]
    for t in terms:
        b=poly.bernstein(t['power'],left,right);lo,hi=min(b),max(b)
        if t['kind']=='exponential':
            if hi>45:raise ValueError('whole exponential domain exceeded')
            interval=iv.scale((exp_bounds(lo)[0],exp_bounds(hi)[1]),t['factor'])
        elif t['kind']=='capacitance':
            args=(t['depletion'],t['transit'],t['saturation'],t['emission'])
            interval=(iv.junction_bounds(*args,lo)[1][0],iv.junction_bounds(*args,hi)[1][1])
        else:raise ValueError('registered variable coefficient required')
        diagnostics.append(dict(ref=t['ref'],kind=t['kind'],voltage_or_exponent_lower=str(lo),
            voltage_or_exponent_upper=str(hi),coefficient_lower=str(interval[0]),coefficient_upper=str(interval[1])))
        for i,j,c in t['coefficients']:product[i][j]=iv.add(product[i][j],iv.scale(interval,c))
    errors=[];rows=[]
    for i,row in enumerate(product):
        out=[]
        for j,v in enumerate(row):out.append(iv.sub((F(i==j),F(i==j)),v))
        rows.append(sum((iv.magnitude(v) for v in out),F(0)));errors.append(out)
    return errors,dict(left=str(left),right=str(right),coefficient_domains=diagnostics,
        preconditioned_defect_intervals=[[[str(a),str(b)] for a,b in row] for row in errors],
        defect_row_upper=list(map(str,rows)),contraction_upper=str(max(rows)),strict_contraction=max(rows)<1)


def temporal_inverse_errors(inverse,scales,covers):
    n=len(inverse);d=list(map(F,scales));xx=[[F(v) for v in row] for row in inverse]
    if not covers or any(not c['strict_contraction'] for c in covers):raise ValueError('complete contracted cover required')
    peaks=[max(abs(d[k]*xx[k][j]) for k in range(n)) for j in range(n)]
    q=max(F(c['contraction_upper']) for c in covers)
    return [[q/(1-q)*p/di for p in peaks] for di in d]
