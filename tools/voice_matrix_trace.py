"""Strict complete CSC parser and Decimal LU, separate from device evaluation."""
from decimal import Decimal, localcontext
import math

def number(s):
    x=float(s)
    if not math.isfinite(x): raise ValueError('nonfinite captured binary64')
    return x

def parse(text):
    out=[];cur=None
    for line in text.splitlines():
        if not line.startswith('RFMATRIX,'):continue
        p=line.split(',');tag=p[1]
        if tag=='begin':
            if cur is not None or len(p)!=10:raise ValueError('nested or malformed begin')
            cur=dict(time_s=number(p[2]),h_s=number(p[3]),iteration=int(p[4]),order=int(p[5]),mode=int(p[6]),
                     n=int(p[7]),nz=int(p[8]),diag_gmin=number(p[9]),nodes={},entries={},x={},factor=[])
            if cur['n']<=0 or cur['nz']<=0 or cur['iteration'] not in (100,101) or not 0<cur['h_s']<=1e-17 or not .0022773<=cur['time_s']<=.0022775:
                raise ValueError('selection outside protocol')
        elif cur is None:raise ValueError('record outside snapshot')
        elif tag=='node':
            if len(p)!=8:raise ValueError('node fields')
            k=int(p[2]);old=int(p[3]);typ=int(p[4])
            if k in cur['nodes'] or not 0<=k<cur['n'] or old<=0 or typ not in (3,4) or p[5]=='MISSING':raise ValueError('node mapping/type')
            cur['nodes'][k]=dict(old=old,type=typ,name=p[5],b=number(p[6]),xold=number(p[7]),
                unknown_unit='V' if typ==3 else 'A',row_unit='A' if typ==3 else 'V')
        elif tag=='factor':
            if len(p)!=6 or p[2] not in ('refactor-after-gmin','factor-after-gmin'):raise ValueError('factor location')
            cur['factor'].append(dict(stage=p[2],scale=int(p[3]),pivot_tol=number(p[4]),ordering=int(p[5])))
            if len(cur['factor'])!=1:raise ValueError('multiple factor attempts need separate matrices')
        elif tag=='a':
            if len(p)!=5 or len(cur['factor'])!=1:raise ValueError('CSC outside factor')
            r,c=int(p[2]),int(p[3]);key=(r,c)
            if key in cur['entries'] or not (0<=r<cur['n'] and 0<=c<cur['n']):raise ValueError('duplicate/out-of-bounds CSC')
            cur['entries'][key]=number(p[4])
        elif tag=='x':
            if len(p)!=4:raise ValueError('x fields')
            k=int(p[2])
            if k in cur['x'] or not 0<=k<cur['n']:raise ValueError('x duplicate/index')
            cur['x'][k]=number(p[3])
        elif tag=='end':
            n=cur['n']
            if len(p)!=2 or set(cur['nodes'])!=set(range(n)) or set(cur['x'])!=set(range(n)) or len(cur['entries'])!=cur['nz'] or len(cur['factor'])!=1:
                raise ValueError('incomplete matrix/vectors')
            if len({v['old'] for v in cur['nodes'].values()})!=n or len({v['name'] for v in cur['nodes'].values()})!=n:raise ValueError('ambiguous map')
            key=(cur['time_s'],cur['h_s'],cur['iteration'])
            if any((s['time_s'],s['h_s'],s['iteration'])==key for s in out):raise ValueError('duplicate selected iteration')
            out.append(cur);cur=None
        else:raise ValueError('unknown matrix record')
    if cur is not None:raise ValueError('unterminated snapshot')
    return out

def exact(x):
    return Decimal.from_float(x)

def lu(a):
    """Dense diagnostic LU with partial pivoting, no change to production KLU."""
    a=[row[:] for row in a];n=len(a);swaps=[]
    for k in range(n):
        p=max(range(k,n),key=lambda i:abs(a[i][k]))
        if not a[p][k]:raise ValueError('singular captured matrix')
        swaps.append(p);a[k],a[p]=a[p],a[k]
        for i in range(k+1,n):
            if not a[i][k]:continue
            a[i][k]/=a[k][k]
            for j in range(k+1,n):a[i][j]-=a[i][k]*a[k][j]
    return a,swaps

def solve_factored(f,b):
    a,swaps=f;b=b[:];n=len(b)
    for k,p in enumerate(swaps):b[k],b[p]=b[p],b[k]
    for i in range(n):b[i]-=sum((a[i][j]*b[j] for j in range(i)),Decimal(0))
    for i in range(n-1,-1,-1):b[i]=(b[i]-sum((a[i][j]*b[j] for j in range(i+1,n)),Decimal(0)))/a[i][i]
    return b

def residual(a,x,b):
    return [sum((v*x[j] for j,v in enumerate(row)),Decimal(0))-b[i] for i,row in enumerate(a)]

def precise(s,digits):
    with localcontext() as ctx:
        ctx.prec=digits;n=s['n'];a=[[Decimal(0) for j in range(n)] for i in range(n)]
        for (i,j),v in s['entries'].items():a[i][j]=exact(v)
        b=[exact(s['nodes'][i]['b']) for i in range(n)]
        f=lu(a);x=solve_factored(f,b);r0=residual(a,x,b)
        dx=solve_factored(f,[-v for v in r0]);refined=[v+d for v,d in zip(x,dx)]
        r1=residual(a,refined,b)
        return refined,dict(digits=digits,max_residual_before=str(max(map(abs,r0))),
                           max_residual_after=str(max(map(abs,r1))),max_refinement=str(max(map(abs,dx))))

def analyze(s):
    x80,r80=precise(s,80);x120,r120=precise(s,120)
    with localcontext() as ctx:
        ctx.prec=120;n=s['n'];a=[[Decimal(0) for j in range(n)] for i in range(n)]
        for (i,j),v in s['entries'].items():a[i][j]=exact(v)
        b=[exact(s['nodes'][i]['b']) for i in range(n)];observed=[exact(s['x'][i]) for i in range(n)]
        rs=residual(a,observed,b);rp=residual(a,x120,b);rows=[]
        for i in range(n):
            info=s['nodes'][i];delta=observed[i]-x120[i];agreement=abs(x80[i]-x120[i])
            if agreement>Decimal('1e-55')*max(Decimal(1),abs(x120[i])):raise ValueError('80/120 digit solve disagrees')
            terms=sum((abs(v*x120[j]) for j,v in enumerate(a[i])),abs(b[i]))
            if abs(rp[i])>Decimal('1e-95')*max(Decimal(1),terms):raise ValueError('high precision residual failed')
            denom=sum((abs(v*observed[j]) for j,v in enumerate(a[i])),abs(b[i]))
            rows.append(dict(index=i,node=info['name'],old=info['old'],unknown_unit=info['unknown_unit'],row_unit=info['row_unit'],
                observed=float(observed[i]),precise=str(x120[i]),previous=info['xold'],
                observed_minus_precise=str(delta),newton_correction=str(observed[i]-exact(info['xold'])),
                observed_residual=str(rs[i]),precise_residual=str(rp[i]),agreement_80_120=str(agreement),
                componentwise_backward_error=str(abs(rs[i])/denom if denom else abs(rs[i]))))
        maxima={}
        for unit in ('V','A'):
            same=[r for r in rows if r['unknown_unit']==unit]
            worst=max(same,key=lambda r:abs(Decimal(r['observed_minus_precise'])))
            residual_rows=[r for r in rows if r['row_unit']==unit]
            wr=max(residual_rows,key=lambda r:abs(Decimal(r['observed_residual'])))
            maxima[unit]=dict(max_solution_difference=worst['observed_minus_precise'],at_unknown=worst['node'],
                              max_observed_residual=wr['observed_residual'],at_row=wr['node'])
        return dict(time_s=s['time_s'],h_s=s['h_s'],iteration=s['iteration'],order=s['order'],mode=s['mode'],n=n,nz=s['nz'],
                    diag_gmin=s['diag_gmin'],factor=s['factor'][0],precision_checks=[r80,r120],rows=rows,maxima=maxima,
                    max_componentwise_backward_error=max((r['componentwise_backward_error'] for r in rows),key=Decimal),
                    linear_solve_only=True,independent_nonlinear_root=False)
