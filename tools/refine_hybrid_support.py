"""Contiguous factor updates; skip proven zero work without a support list."""
from prepare_hybrid_stamp import once
def transform(s):
    s=once(s,'self.cross[p][col]=factor;\n                for k in col+1..end', 'self.cross[p][col]=factor;if factor==0.{continue;}\n                for k in col+1..end')
    for loop in ['0..i','i+1..N']:
        s=once(s,f'for k in {loop}{{v-=self.lu.a[i][k]*x[k];}}', f'for k in {loop}{{let value=self.lu.a[i][k];if value!=0.||v==0.{{v-=value*x[k];}}}}')
    s=once(s,'for p in 0..4{for k in 0..N{rhs[p]-=self.cross[p][k]*x[k];}}', 'for p in 0..4{for k in 0..N{let value=self.cross[p][k];if value!=0.||rhs[p]==0.{rhs[p]-=value*x[k];}}}')
    return s
