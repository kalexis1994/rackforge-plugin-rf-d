"""Fixed weighted RMS junction block, with signed symmetric-part enclosure."""
from fractions import Fraction as F
from math import isqrt
import loudness_latch_block_comparison as prior

BITS=256
UNIT=1<<BITS
JUNCTION_BLOCK=5
NORMALIZATION=F(2) # sqrt(4): u_junction=||W e||2/2 <= ||W e||infinity.

def sqrt_bounds(value):
    value=F(value)
    if value<0:raise ValueError('nonnegative square root required')
    k=isqrt((value.numerator<<(2*BITS))//value.denominator)
    lo=F(k,UNIT);hi=lo if lo*lo==value else F(k+1,UNIT)
    return lo,hi

def norm2_upper(values):return sqrt_bounds(sum((F(v)**2 for v in values),F(0)))[1]

def block_metrics(inverse,nv,weights,forcing):
    # Keep every previous infinity block, graph, weight and point budget.
    old=prior.block_metrics(inverse,nv,weights,forcing)
    n=len(inverse);w=list(map(F,weights));groups=prior.BLOCKS;junction=groups[JUNCTION_BLOCK]
    if n-nv!=25:raise ValueError('fixed 25-memory physical partition required')
    absolute=[[max(abs(F(lo)),abs(F(hi))) for lo,hi in row] for row in inverse]
    matrix=[[F(v) for v in row] for row in old['comparison_per_s']]
    b=[[(-w[i]/w[j]*F(inverse[nv+i][nv+j][1]),-w[i]/w[j]*F(inverse[nv+i][nv+j][0])) for j in junction] for i in junction]
    symmetric=[[( (b[i][j][0]+b[j][i][0])/2,(b[i][j][1]+b[j][i][1])/2) for j in range(4)] for i in range(4)]
    mu=max(symmetric[i][i][1]+sum((max(map(abs,symmetric[i][j])) for j in range(4) if j!=i),F(0)) for i in range(4))
    matrix[JUNCTION_BLOCK][JUNCTION_BLOCK]=mu
    for a,block in enumerate(groups):
        if a==JUNCTION_BLOCK:continue
        # RMS sender -> infinity receiver: dual 2-norm, multiplied by sqrt(4).
        matrix[a][JUNCTION_BLOCK]=NORMALIZATION*max(norm2_upper(w[i]/w[j]*absolute[nv+i][nv+j] for j in junction) for i in block)
        # Infinity sender -> RMS receiver: bound each row, then the 2-norm /sqrt(4).
        rows=[sum((w[i]/w[j]*absolute[nv+i][nv+j] for j in block),F(0)) for i in junction]
        matrix[JUNCTION_BLOCK][a]=norm2_upper(rows)/NORMALIZATION
    values=list(map(F,forcing['nodal_l1_c']+forcing['constraint_l1_v_s']))
    budget=list(map(F,old['block_forcing_l1_v']))
    budget[JUNCTION_BLOCK]=sum((norm2_upper(w[i]*absolute[nv+i][j] for i in junction)/NORMALIZATION*v for j,v in enumerate(values)),F(0))
    gains=[[F(v) for v in row] for row in old['nodal_block_gains']]
    for i in range(nv):gains[i][JUNCTION_BLOCK]=NORMALIZATION*norm2_upper(absolute[i][nv+j]/w[j] for j in junction)
    return dict(comparison_per_s=prior.pack(matrix),block_forcing_l1_v=list(map(str,budget)),
        nodal_block_gains=prior.pack(gains),nodal_direct_v=old['nodal_direct_v'],
        junction_symmetric_intervals=[[[str(lo),str(hi)] for lo,hi in row] for row in symmetric],
        junction_mu2_gershgorin_upper_per_s=str(mu),prior_junction_mu_infinity_upper_per_s=old['comparison_per_s'][JUNCTION_BLOCK][JUNCTION_BLOCK],
        rms_normalization=str(NORMALIZATION),initial_common_weighted_infinity_anchor_conversion='RMS<=infinity; initial block anchor vector is ones')

def propagate(cells):return prior.propagate(cells)
