"""Strict single real transient rawfile reader for the measured UCRT64 ABI."""
import hashlib,struct,sys
from pathlib import Path
import numpy as np

HEADER_LIMIT=131072

def canonical_name(name,unit,expected):
    if name in expected:return name
    if unit=='current' and name.startswith('i(@') and name.endswith(')') and name[2:-1] in expected:
        return name[2:-1]
    raise ValueError('unexpected native vector name: '+name)

def read(path,vectors):
    if sys.byteorder!='little' or struct.calcsize('d')!=8:raise ValueError('measured little-endian binary64 ABI required')
    path=Path(path);header=bytearray()
    with path.open('rb') as stream:
        while True:
            line=stream.readline(HEADER_LIMIT+1)
            if not line or len(header)+len(line)>HEADER_LIMIT:raise ValueError('bounded complete native header required')
            header.extend(line)
            if line in (b'Binary:\n',b'Binary:\r\n'):break
    try:lines=bytes(header).decode('ascii').splitlines()
    except UnicodeDecodeError as e:raise ValueError('ASCII native header required') from e
    if lines.count('Variables:')!=1 or lines[-1]!='Binary:':raise ValueError('single native variable table required')
    pivot=lines.index('Variables:');fields={}
    for line in lines[:pivot]:
        key,sep,value=line.partition(':')
        if not sep:raise ValueError('native header field required')
        if key in ('Command','Option'):continue
        if key not in ('Title','Date','Plotname','Flags','No. Variables','No. Points') or key in fields:raise ValueError('ambiguous native header field')
        fields[key]=value.strip()
    if set(fields)!=set(('Title','Date','Plotname','Flags','No. Variables','No. Points')):raise ValueError('complete native header fields required')
    if fields['Plotname']!='Transient Analysis' or fields['Flags']!='real':raise ValueError('single padded real transient required')
    if not fields['No. Variables'].isdigit() or not fields['No. Points'].isdigit():raise ValueError('integer native counts required')
    columns=int(fields['No. Variables']);rows=int(fields['No. Points'])
    expected=['time',*vectors]
    if len(set(expected))!=len(expected) or columns!=len(expected) or rows<2:raise ValueError('native counts/vector domain')
    table=lines[pivot+1:-1]
    if len(table)!=columns:raise ValueError('native variable count mismatch')
    names=[];variables=[]
    for i,line in enumerate(table):
        tokens=line.split()
        if len(tokens)!=3 or tokens[0]!=str(i):raise ValueError('native indexed scalar variable required')
        _,name,unit=tokens;n=canonical_name(name,unit,expected)
        required='time' if n=='time' else 'voltage' if n.startswith('v(') else 'current' if n.startswith(('@','i(')) else None
        if required is None or unit!=required:raise ValueError('native vector unit mismatch')
        names.append(n);variables.append(dict(index=i,name=name,canonical_name=n,unit=unit))
    if names[0]!='time' or len(set(names))!=columns or set(names)!=set(expected):raise ValueError('unique native scale/vector mapping required')
    offset=len(header);payload=rows*columns*8
    if path.stat().st_size!=offset+payload:raise ValueError('native payload size mismatch')
    mm=np.fromfile(path,dtype='<f8',count=rows*columns,offset=offset).reshape(rows,columns)
    indices=[names.index(n) for n in expected]
    a=np.asarray(mm) if indices==list(range(columns)) else np.ascontiguousarray(mm[:,indices])
    if not np.isfinite(a).all() or a[0,0]!=0 or np.any(np.diff(a[:,0])<=0):raise ValueError('finite native vectors and strict DC-to-transient clock required')
    return a,dict(schema='rf-d/native-raw-layout/v1',dtype='<f8',endianness='little',columns=columns,rows=rows,
        header_bytes=offset,payload_bytes=payload,header_sha256=hashlib.sha256(header).hexdigest(),
        payload_sha256=hashlib.sha256(memoryview(mm).cast('B')).hexdigest(),variables=variables,
        canonical_columns=expected,column_indices=indices,physical_fidelity=False,real_time=False)

def bits(a,b):
    if a.dtype!=np.dtype('float64') or b.dtype!=np.dtype('float64'):raise ValueError('binary64 arrays required')
    same_shape=a.shape==b.shape
    mismatches=int(np.count_nonzero(a.view(np.uint64)!=b.view(np.uint64))) if same_shape else None
    return dict(passed=same_shape and mismatches==0,shapes=[list(a.shape),list(b.shape)],bit_mismatches=mismatches,
        signed_zero_compared=True,interpolation=False)
