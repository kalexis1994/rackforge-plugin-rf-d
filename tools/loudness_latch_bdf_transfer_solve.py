"""Equilibrated linear solve; retain both binary and Decimal80 backward gates."""
from decimal import Decimal,localcontext
import math
import numpy as np

BACKWARD_GATE=1e-10
MAXIMUM_REFINEMENTS=8


def backward_errors(j,b,x):
    denominator=np.abs(j)@np.abs(x)+np.abs(b)
    residual=b-j@x
    binary=np.divide(np.abs(residual),denominator,out=np.zeros_like(residual),where=denominator>0)
    precise=np.empty_like(b)
    with localcontext() as ctx:
        ctx.prec=80
        jd=[[(k,Decimal.from_float(float(v))) for k,v in enumerate(row) if v] for row in j]
        xd=[[Decimal.from_float(float(v)) for v in row] for row in x]
        for i,row in enumerate(jd):
            for col in range(b.shape[1]):
                precise[i,col]=float(Decimal.from_float(float(b[i,col]))-sum((v*xd[k][col] for k,v in row),Decimal(0)))
    exact=np.divide(np.abs(precise),denominator,out=np.zeros_like(precise),where=denominator>0)
    return precise,dict(binary_componentwise_backward_error=float(np.max(binary)),
                        decimal80_componentwise_backward_error=float(np.max(exact)))


def solve(j,b):
    j=np.asarray(j,dtype=float);b=np.asarray(b,dtype=float)
    if j.ndim!=2 or j.shape[0]!=j.shape[1] or b.ndim!=2 or b.shape[0]!=j.shape[0]:
        raise ValueError("square matrix and complete RHS columns required")
    if not np.isfinite(j).all() or not np.isfinite(b).all():raise ValueError("finite matrix and RHS required")
    rows=np.max(np.abs(j),axis=1)
    if np.any(rows==0):raise ValueError("zero row in transfer matrix")
    a=j/rows[:,None];columns=np.max(np.abs(a),axis=0)
    if np.any(columns==0):raise ValueError("zero column in transfer matrix")
    a=a/columns[None,:]
    def correction(rhs):return np.linalg.solve(a,rhs/rows[:,None])/columns[:,None]
    x=correction(b);iterations=[]
    for k in range(MAXIMUM_REFINEMENTS+1):
        if not np.isfinite(x).all():raise ValueError("finite transfer solution required")
        residual,errors=backward_errors(j,b,x);iterations.append(dict(iteration=k,**errors))
        if max(errors.values())<BACKWARD_GATE:
            return x,dict(linear_solver="row-column-equilibrated/Decimal80-refinement/v1",
                row_scales=rows.tolist(),column_scales=columns.tolist(),refinements=k,iterations=iterations,
                maximum_refinements=MAXIMUM_REFINEMENTS,backward_gate=BACKWARD_GATE,**errors)
        if k<MAXIMUM_REFINEMENTS:
            delta=correction(residual)
            x=np.array([[math.fsum((u,v)) for u,v in zip(xrow,drow)] for xrow,drow in zip(x,delta)])
    raise ValueError("equilibrated transfer exhausted unchanged binary/Decimal80 backward gates: "+str(errors))
