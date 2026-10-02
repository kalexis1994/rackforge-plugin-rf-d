"""Offline exact solve of the binary64 coefficient matrix lifted to rationals."""
from fractions import Fraction as F
import numpy as np


def solve(j,b):
    j=np.asarray(j,dtype=float);b=np.asarray(b,dtype=float)
    if j.ndim!=2 or j.shape[0]!=j.shape[1] or b.ndim!=2 or b.shape[0]!=j.shape[0]:
        raise ValueError("square matrix and complete RHS required")
    if not np.isfinite(j).all() or not np.isfinite(b).all():raise ValueError("finite binary64 coefficients required")
    n=j.shape[0];m=b.shape[1]
    a=[[F.from_float(float(v)) for v in row] for row in j]
    rhs=[[F.from_float(float(v)) for v in row] for row in b]
    pivots=[]
    for k in range(n):
        pivot=max(range(k,n),key=lambda i:abs(a[i][k]))
        if not a[pivot][k]:raise ValueError("exact singular binary64 coefficient matrix at column "+str(k))
        pivots.append(pivot)
        if pivot!=k:a[k],a[pivot]=a[pivot],a[k];rhs[k],rhs[pivot]=rhs[pivot],rhs[k]
        active=[c for c in range(k+1,n) if a[k][c]]
        for i in range(k+1,n):
            if not a[i][k]:continue
            factor=a[i][k]/a[k][k];a[i][k]=F(0)
            for c in active:a[i][c]-=factor*a[k][c]
            for c in range(m):
                if rhs[k][c]:rhs[i][c]-=factor*rhs[k][c]
    x=[[F(0)]*m for _ in range(n)]
    for i in range(n-1,-1,-1):
        active=[k for k in range(i+1,n) if a[i][k]]
        for c in range(m):x[i][c]=(rhs[i][c]-sum((a[i][k]*x[k][c] for k in active),F(0)))/a[i][i]
    rounded=np.array([[float(v) for v in row] for row in x])
    if not np.isfinite(rounded).all():raise ValueError("exact solution is outside finite binary64 range")
    # Independently multiply the original rational inputs, not eliminated rows.
    original=[[F.from_float(float(v)) for v in row] for row in j]
    for i,row in enumerate(original):
        active=[k for k,v in enumerate(row) if v]
        for c in range(m):
            if sum((row[k]*x[k][c] for k in active),F(0))!=F.from_float(float(b[i,c])):
                raise ValueError("exact rational solution verification failed")
    return rounded,dict(linear_solver="binary64-coefficients/exact-rational-elimination/v1",
        exact_rational_residual_zero=True,pivot_rows=pivots,
        exact_zero_entries=sum(v==0 for row in x for v in row),
        maximum_numerator_bits=max(v.numerator.bit_length() for row in x for v in row),
        maximum_denominator_bits=max(v.denominator.bit_length() for row in x for v in row),
        coefficients_identical_to_input_binary64=True,rounded_only_after_exact_solve=True)
