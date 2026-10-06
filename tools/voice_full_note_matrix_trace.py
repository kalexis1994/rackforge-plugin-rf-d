"""Complete CSC parser for the declared long-note window; old LU unchanged."""
from voice_matrix_trace import number, exact, precise, analyze

def parse(text):
    out=[];cur=None
    for line in text.splitlines():
        if not line.startswith('RFMATRIX,'):continue
        p=line.split(',');tag=p[1]
        if tag=='begin':
            if cur is not None or len(p)!=10:raise ValueError('nested or malformed begin')
            cur=dict(time_s=number(p[2]),h_s=number(p[3]),iteration=int(p[4]),order=int(p[5]),mode=int(p[6]),
                     n=int(p[7]),nz=int(p[8]),diag_gmin=number(p[9]),nodes={},entries={},x={},factor=[])
            if cur['n']<=0 or cur['nz']<=0 or cur['iteration'] not in (100,101) or not 0<cur['h_s']<=1e-17 or not .01594035<=cur['time_s']<=.01594045:
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
