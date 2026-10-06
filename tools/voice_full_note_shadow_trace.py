"""Strict scratch corrections 3..5; exact arithmetic and unchanged linear gates."""
from decimal import Decimal,localcontext
import voice_matrix_trace as matrix
import voice_refine_trace as refine

def parse(text):
    old=refine.parse(text);out=[];cur=None
    for line in text.splitlines():
        if line.startswith('RFMATRIX,begin,'):
            if cur is not None:raise ValueError('nested shadow')
            cur=dict(n=int(line.split(',')[7]),r=[{} for _ in range(3)],correction=[{} for _ in range(3)],final={})
        elif line.startswith('RFSHADOW,'):
            if cur is None:raise ValueError('shadow outside capture')
            p=line.split(',');tag=p[1]
            if tag=='final':
                if len(p)!=4:raise ValueError('shadow final fields')
                k=int(p[2]);bucket=cur['final'];value=matrix.number(p[3])
            elif tag in ('r','correction'):
                if len(p)!=(6 if tag=='r' else 7):raise ValueError('shadow step fields')
                step=int(p[2]);k=int(p[3])
                if not 3<=step<6:raise ValueError('scratch steps must be 3..5')
                bucket=cur[tag][step-3];value=[matrix.number(v) for v in p[4:]]
            else:raise ValueError('unknown shadow record')
            if not 0<=k<cur['n'] or k in bucket:raise ValueError('shadow duplicate/index')
            bucket[k]=value
        elif line=='RFMATRIX,end':
            if cur is None:raise ValueError('missing shadow begin')
            expected=set(range(cur['n']))
            if any(set(b)!=expected for b in [cur['final']]+cur['r']+cur['correction']):raise ValueError('incomplete scratch steps')
            if len(out)>=len(old):raise ValueError('original capture missing')
            d=old[len(out)]
            if d['n']!=cur['n']:raise ValueError('shadow dimension')
            out.append(dict(n=cur['n'],original=d['original'],r=d['r']+cur['r'],correction=d['correction']+cur['correction'],final=cur['final']))
            cur=None
    if cur is not None or len(out)!=len(old):raise ValueError('shadow coverage')
    return out

def compare_six(s,detail,precise_analysis):
    with localcontext() as ctx:
        ctx.prec=160;n=s['n'];roots=[Decimal(r['precise']) for r in precise_analysis['rows']]
        rows=[];step_rows=[[] for _ in range(6)]
        x=[matrix.exact(detail['original'][i]) for i in range(n)]
        for step in range(6):
            expected=[matrix.exact(s['nodes'][i]['b']) for i in range(n)];scale=[abs(v) for v in expected]
            for (i,j),a in s['entries'].items():
                term=matrix.exact(a)*x[j];expected[i]-=term;scale[i]+=abs(term)
            for i in range(n):
                hi,lo=detail['r'][step][i];got=matrix.exact(hi)+matrix.exact(lo)
                err=got-expected[i]
                if abs(err)>Decimal('1e-30')*max(Decimal(1),scale[i]):raise ValueError('compiled residual differs from exact inputs')
                dx,hi,lo=detail['correction'][step][i];updated=matrix.exact(hi)+matrix.exact(lo)
                if abs(updated-(x[i]+matrix.exact(dx)))>Decimal('1e-30')*max(Decimal(1),abs(updated)):raise ValueError('compensated update')
                x[i]=updated;step_rows[step].append(dict(node=s['nodes'][i]['name'],residual_pair_error=str(err),
                    correction=dx,root_difference=str(updated-roots[i])))
        for i,root in enumerate(roots):
            info=s['nodes'][i];value=detail['final'][i]
            if value!=float(x[i]):raise ValueError('single final publication')
            error=matrix.exact(value)-root;bound=Decimal('1e-8' if info['type']==3 else '1e-13')+Decimal('1e-7')*abs(root)
            rows.append(dict(node=info['name'],unknown_unit=info['unknown_unit'],error=str(error),bound=str(bound),passed=abs(error)<=bound,
                original_error=str(matrix.exact(detail['original'][i])-root)))
        return dict(iteration=s['iteration'],time_s=s['time_s'],h_s=s['h_s'],passed=all(r['passed'] for r in rows),rows=rows,steps=step_rows,
                    max_voltage_error=str(max(abs(Decimal(r['error'])) for r in rows if r['unknown_unit']=='V')),
                    max_current_error=str(max(abs(Decimal(r['error'])) for r in rows if r['unknown_unit']=='A')))
