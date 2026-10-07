"""Diagnose decimal conversion at every mismatched prefix cell; no solver change."""
from decimal import Decimal
import hashlib,json,lzma
from pathlib import Path
import numpy as np
from mixer_on_native_vectors import ROOT,sha

def main():
    output=ROOT/'evidence/voice_serial_prefix_decimal01.json'
    if output.exists():raise ValueError('preserve prefix decimal audit')
    dp=ROOT/'evidence/voice_serial_prefix_nominal50001.json';d=json.loads(dp.read_text(encoding='utf8'))
    for n,h in d['source_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('observed prefix source changed')
    paths=list(d['source_sha256']);ap=next(ROOT/n for n in paths if n.endswith('.xz'))
    old=next(ROOT/n for n in paths if n.endswith('nominal500.txt'))
    with lzma.open(ap,'rb') as f:raw=f.read()
    fresh=np.frombuffer(raw,dtype='<f8',offset=823).reshape(d['new_rows'],19)
    loaded=np.loadtxt(old,skiprows=1)
    differing=np.argwhere(loaded.view(np.uint64)!=fresh.view(np.uint64));wanted={int(i) for i,j in differing};lines={}
    with old.open(encoding='utf8') as f:
        next(f)
        for i,line in enumerate(f):
            if i in wanted:lines[i]=line.split()
    cells=[]
    def bits(value):return int(np.float64(value).view(np.uint64))
    for i,j in differing:
        token=lines[int(i)][int(j)];direct=float(token);decimal=float(Decimal(token));native=float(fresh[i,j])
        cells.append(dict(row=int(i),column=int(j),token=token,numpy_bits=bits(loaded[i,j]),
            python_bits=bits(direct),decimal_bits=bits(decimal),native_bits=bits(native)))
    all_native=all(c['python_bits']==c['decimal_bits']==c['native_bits'] for c in cells)
    sources={**d['source_sha256'],dp.relative_to(ROOT).as_posix():sha(dp),Path(__file__).relative_to(ROOT).as_posix():sha(Path(__file__))}
    after={n:sha(ROOT/n) for n in sources}
    if sources!=after:raise ValueError('decimal audit inputs changed')
    output.write_text(json.dumps(dict(schema='rf-d/prefix-decimal-diagnostic/v1',source_sha256=sources,source_sha256_after=after,
        numpy_loadtxt_differing_cells=len(cells),cells=cells,all_mismatches_match_python_and_decimal_native_bits=all_native,
        identical_prefix_after_explicit_decimal_audit=all_native,original_diagnostic_preserved=True,
        new_spice_solves=0,no_file_restoration=True,long_note_admitted=False,cause_identified=False),indent=2)+'\n',encoding='utf8',newline='\n')
    print('prefix decimal audit: cells',len(cells),'all direct/Decimal equal native',all_native,flush=True)

if __name__=='__main__':main()
