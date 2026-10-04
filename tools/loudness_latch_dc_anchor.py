"""Outward rational Banach enclosure of a frozen static DC, no root fitting."""
from fractions import Fraction as F
import loudness_latch_constitutive_enclosure as iv
from loudness_latch_coverage_bridge import digest

def pack(a):return [[str(v) for v in row] for row in a]
def interval_pack(a):return [[str(lo),str(hi)] for lo,hi in a]
def incidence(a,b):
    out={}
    for node,value in ((a,F(1)),(b,F(-1))):
        if isinstance(node,int):out[node]=out.get(node,F(0))+value
    return {k:v for k,v in out.items() if v}

def compile_graph(g,center,inverse):
    n=g['node_count'];x=list(map(F,center));z=[[F(v) for v in row] for row in inverse]
    if n<=0 or len(x)!=n or len(z)!=n or any(len(row)!=n for row in z):raise ValueError('complete center and static preconditioner required')
    def voltage(k):return x[k] if isinstance(k,int) else F(g['fixed'][k])
    def weighted(rows):return [sum((z[i][k]*v for k,v in rows.items()),F(0)) for i in range(n)]
    linear=[[F(0) for _ in range(n)] for _ in range(n)];eta=[(F(0),F(0)) for _ in range(n)];terms=[]
    for r in g['resistors']+g['conductances']:
        a,b=r['left'],r['right'];c=1/F(r['ohm']) if 'ohm' in r else F(r['siemens'])
        if c<0:raise ValueError('nonnegative conductance required')
        rows=incidence(a,b);w=weighted(rows);value=c*(voltage(a)-voltage(b))
        for i in range(n):
            eta[i]=iv.add(eta[i],(w[i]*value,w[i]*value))
            for j,v in rows.items():linear[i][j]+=w[i]*c*v
    def exponential(ref,a,b,factor,saturation,rows):
        if saturation<=0 or not factor:raise ValueError('positive saturation and nonzero voltage factor required')
        power=factor*(voltage(a)-voltage(b))
        if power>45:raise ValueError('DC center exponential domain exceeded')
        columns={j:factor*v for j,v in incidence(a,b).items()};w=weighted(rows)
        current=iv.scale(iv.sub(iv.base.exp_bounds(power),(F(1),F(1))),saturation)
        coeff=[]
        for i in range(n):
            eta[i]=iv.add(eta[i],iv.scale(current,w[i]))
            for j,v in columns.items():
                if w[i]*v:coeff.append((i,j,w[i]*saturation*v))
        terms.append(dict(ref=ref,center_exponent=str(power),radius_gain=str(sum(map(abs,columns.values()),F(0))),coefficients=coeff))
    for q in g['bjts']:
        b,c,e=q['base'],q['collector'],q['emitter'];s=F(q['polarity']);sat=F(q['is_a']);vt=F(q['vt']);bf=F(q['beta_forward']);br=F(q['beta_reverse'])
        if vt<=0 or bf<=0 or br<=0 or s not in (-1,1):raise ValueError('valid bipolar coefficients required')
        def rows(values):
            result={}
            for node,value in values:
                if isinstance(node,int):result[node]=result.get(node,F(0))+value
            return {k:v for k,v in result.items() if v}
        exponential(q['ref']+'/BE',b,e,s/vt,sat,rows(((b,s/bf),(c,s),(e,-s*(1+1/bf)))))
        exponential(q['ref']+'/BC',b,c,s/vt,sat,rows(((b,s/br),(c,-s*(1+1/br)),(e,s))))
    for d in g['diodes']:
        a,b=d['anode'],d['cathode'];vt=F(d['ideality'])*F(d['vt'])
        if vt<=0:raise ValueError('positive diode voltage scale required')
        exponential(d['ref'],a,b,1/vt,F(d['is_a']),incidence(a,b))
    defect=[[(F(i==j)-linear[i][j],F(i==j)-linear[i][j]) for j in range(n)] for i in range(n)]
    return dict(dimension=n,center=list(map(str,x)),constant_defect=defect,terms=terms,preconditioned_residual=eta,
        graph_sha256=digest(g),inverse_sha256=digest(inverse),residual_policy='precondition each rank-one current before enclosing its single exponential')

def prove(defect,residual,radius):
    radius=F(radius);n=len(defect)
    if radius<=0 or not n or len(residual)!=n or any(len(row)!=n for row in defect):raise ValueError('positive radius and complete square proof data required')
    intervals=[v for row in defect for v in row]+list(residual)
    if any(len(v)!=2 or F(v[0])>F(v[1]) for v in intervals):raise ValueError('ordered proof intervals required')
    sums=[sum((iv.magnitude(v) for v in row),F(0)) for row in defect];etas=list(map(iv.magnitude,residual));q=max(sums);eta=max(etas)
    image=[e+radius*s for e,s in zip(etas,sums)];accepted=q<1 and all(v<radius for v in image)
    error=eta/(1-q) if accepted else None
    return dict(radius_v=str(radius),defect_intervals=[[interval_pack(row) for row in defect]][0],
        defect_row_sums=list(map(str,sums)),preconditioned_residual_intervals=interval_pack(residual),
        row_image_radius_v=list(map(str,image)),contraction_upper=str(q),eta_upper_v=str(eta),
        strict_self_map=all(v<radius for v in image),strict_contraction=q<1,accepted=accepted,
        posterior_error_upper_v=str(error) if error is not None else None,
        local_root_exists=accepted,local_root_unique=accepted,preconditioner_nonsingular_implied=q<1,
        full_trajectory_error_proven=False)

def certify(compiled,radius):
    radius=F(radius)
    if radius<=0:raise ValueError('positive DC box radius required')
    a=[[tuple(v) for v in row] for row in compiled['constant_defect']];exponents=[]
    for t in compiled['terms']:
        c,gain=F(t['center_exponent']),F(t['radius_gain']);lo,hi=c-radius*gain,c+radius*gain
        if hi>45:raise ValueError('whole DC box exponential domain exceeded')
        e=iv.exp_interval((lo,hi));exponents.append(dict(ref=t['ref'],range=[str(lo),str(hi)]))
        for i,j,coefficient in t['coefficients']:a[i][j]=iv.sub(a[i][j],iv.scale(e,coefficient))
    return prove(a,compiled['preconditioned_residual'],radius)|dict(exponent_ranges=exponents)

def static_point(g,values):
    n=g['node_count'];x=list(map(F,values))
    if len(x)!=n:raise ValueError('complete static point required')
    residual=[(F(0),F(0)) for _ in range(n)]
    def voltage(k):return x[k] if isinstance(k,int) else F(g['fixed'][k])
    def stamp(rows,current):
        for node,value in rows.items():residual[node]=iv.add(residual[node],iv.scale(current,value))
    for r in g['resistors']+g['conductances']:
        c=1/F(r['ohm']) if 'ohm' in r else F(r['siemens']);v=c*(voltage(r['left'])-voltage(r['right']));stamp(incidence(r['left'],r['right']),(v,v))
    def current(a,b,k,sat):
        power=k*(voltage(a)-voltage(b))
        if power>45:raise ValueError('static point exponential domain exceeded')
        return iv.scale(iv.sub(iv.base.exp_bounds(power),(F(1),F(1))),sat)
    def combine(items):
        out={}
        for node,c in items:
            if isinstance(node,int):out[node]=out.get(node,F(0))+c
        return out
    for q in g['bjts']:
        b,c,e=q['base'],q['collector'],q['emitter'];s=F(q['polarity']);bf=F(q['beta_forward']);br=F(q['beta_reverse']);vt=F(q['vt']);sat=F(q['is_a'])
        stamp(combine(((b,s/bf),(c,s),(e,-s*(1+1/bf)))),current(b,e,s/vt,sat))
        stamp(combine(((b,s/br),(c,-s*(1+1/br)),(e,s))),current(b,c,s/vt,sat))
    for d in g['diodes']:stamp(incidence(d['anode'],d['cathode']),current(d['anode'],d['cathode'],1/(F(d['ideality'])*F(d['vt'])),F(d['is_a'])))
    return residual
