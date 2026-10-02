"""Offline analytic binary64 stamps, optionally retaining reciprocal rounding remainders."""
import copy
from fractions import Fraction as F
import math
import numpy as np

MODES=("ordinary-reciprocal","compensated-reciprocal")


def prepare(graph,mode):
    if mode not in MODES:raise ValueError("declared reciprocal mode required")
    result=copy.deepcopy(graph);result["reciprocal_mode"]=mode
    for row in result["resistors"]:
        ohm=float(row["ohm"])
        if not math.isfinite(ohm) or ohm<=0:raise ValueError("positive finite resistance required")
        exact=1/F.from_float(ohm);high=float(exact)
        terms=[high]
        if mode==MODES[1]:terms.append(float(exact-F.from_float(high)))
        remainder=exact-sum((F.from_float(v) for v in terms),F(0))
        row.update(conductance_terms_s=terms,remaining_reciprocal_error_s=float(remainder))
    return result


def evaluate(graph,node_v):
    x=np.asarray(node_v,dtype=float)
    if x.shape!=(graph["node_count"],) or not np.isfinite(x).all():
        raise ValueError("complete finite static node vector required")
    r=[[] for _ in x];j={}
    def voltage(node):return float(x[node]) if isinstance(node,int) else float(graph["fixed"][node])
    def add(row,current,gradient):
        if not isinstance(row,int):return
        r[row].append(current)
        for col,terms in gradient:
            if isinstance(col,int):j.setdefault((row,col),[]).extend(terms)
    def branch(a,b,current,terms):
        opposite=[-v for v in terms]
        add(a,current,((a,terms),(b,opposite)))
        add(b,-current,((a,opposite),(b,terms)))
    for row in graph["resistors"]+graph["conductances"]:
        a,b=row["left"],row["right"]
        if "ohm" in row:
            terms=row["conductance_terms_s"];current=(voltage(a)-voltage(b))/float(row["ohm"])
        else:
            terms=[float(row["siemens"])];current=terms[0]*(voltage(a)-voltage(b))
        branch(a,b,current,terms)
    for q in graph["bjts"]:
        b,c,e=q["base"],q["collector"],q["emitter"];s=q["polarity"]
        vt=float(q["vt"]);sat=float(q["is_a"]);bf=float(q["beta_forward"]);br=float(q["beta_reverse"])
        be=s*(voltage(b)-voltage(e))/vt;bc=s*(voltage(b)-voltage(c))/vt
        if max(be,bc)>45:raise ValueError("BJT exponential domain exceeded")
        forward=sat*math.expm1(be);reverse=sat*math.expm1(bc)
        ib=math.fsum((forward/bf,reverse/br));ic=math.fsum((forward,-reverse,-reverse/br))
        gf=sat*math.exp(be)/vt;gr=sat*math.exp(bc)/vt
        # Keep each contributing derivative until the final componentwise fsum.
        gb=((b,[gf/bf,gr/br]),(e,[-gf/bf]),(c,[-gr/br]))
        gc=((b,[gf,-gr,-gr/br]),(e,[-gf]),(c,[gr,gr/br]))
        ge=((b,[-gf,-gf/bf,gr]),(e,[gf,gf/bf]),(c,[-gr]))
        add(b,s*ib,gb);add(c,s*ic,gc);add(e,-s*math.fsum((ib,ic)),ge)
    for d in graph["diodes"]:
        a,c=d["anode"],d["cathode"];vt=float(d["ideality"])*float(d["vt"])
        exponent=(voltage(a)-voltage(c))/vt
        if exponent>45:raise ValueError("diode exponential domain exceeded")
        ef=float(d["is_a"])*math.exp(exponent)
        branch(a,c,float(d["is_a"])*math.expm1(exponent),[ef/vt])
    jac=np.zeros((len(x),len(x)))
    for (row,col),terms in j.items():jac[row,col]=math.fsum(terms)
    return np.array([math.fsum(row) for row in r]),jac
