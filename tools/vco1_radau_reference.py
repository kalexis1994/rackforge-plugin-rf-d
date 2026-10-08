"""Independent Decimal100 coupled Radau IIA charge equations, absolute pivots."""
from decimal import Decimal
import vco1_increment_circuit as circuit
D=Decimal.from_float
B=((Decimal('1.5'),Decimal('.5')),(Decimal('-4.5'),Decimal('2.5')))
N=134


def system(stages,old,h,c):
    parts=[]
    for x in stages:
        f,g,ground_f=circuit.reference_decimal(x,old,0.,c)
        e,j,ground_e=circuit.reference_decimal(x,old,h,c)
        q=[a-b for a,b in zip(e,f)]
        if any(v for k,v in enumerate(q) if k>=98 and k not in (118,119,129,130)):
            raise ValueError('dynamic algebraic row')
        parts.append((f,g,q,[[a-b for a,b in zip(ja,ga)] for ja,ga in zip(j,g)],ground_f,ground_e-ground_f))
    r=[parts[i][0][a]+sum(B[i][j]*parts[j][2][a] for j in range(2)) for i in range(2) for a in range(N)]
    jac=[[((parts[i][1][a][b] if i==j else Decimal(0))+B[i][j]*parts[j][3][a][b]) for j in range(2) for b in range(N)] for i in range(2) for a in range(N)]
    ground=[parts[i][4]+sum(B[i][j]*parts[j][5] for j in range(2)) for i in range(2)]
    return r,jac,ground


def solve(old,h,c):
    x=[list(old),list(old)]
    for iteration in range(64):
        if not all(circuit.valid(v,c) for v in x):raise ValueError('Radau Decimal domain')
        r,j,g=system(x,old,h,c)
        norm=max(abs(v)/D(2e-14 if k%N<98 else 2e-12) for k,v in enumerate(r))
        d=circuit.op.dense([row[:] for row in j],[-v for v in r])
        corr=max(abs(v)/D(2e-10 if k%N<98 else 2e-13) for k,v in enumerate(d))
        if norm<=1 and corr<=1:return dict(stage=x[0],endpoint=x[1],iterations=iteration+1,residual=r,ground=g,correction_ratio=str(corr),residual_ratio=str(norm))
        for power in range(24):
            alpha=Decimal(2)**(-power)
            trial=[[v+alpha*d[i*N+a] for a,v in enumerate(x[i])] for i in range(2)]
            if not all(circuit.valid(v,c) for v in trial):continue
            rr,_,_=system(trial,old,h,c)
            new=max(abs(v)/D(2e-14 if k%N<98 else 2e-12) for k,v in enumerate(rr))
            if new<norm or new<=1:x=trial;break
        else:raise ValueError('Radau Decimal line search')
    raise ValueError('Radau Decimal iteration limit')
