"""Recompute preserved failing rows with exact binary64 operands in Decimal100."""
import ast,json,re
from decimal import Decimal,localcontext
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    name='evidence/voice_dynamic_schur_linear_inspection01.json'
    r=json.loads((ROOT/name).read_text(encoding='utf8'))
    require(r['identical_replay'] and not r['passed'],'preserved rejection')
    rows=[]
    with localcontext() as c:
        c.prec=100
        for line in r['commands'][0]['stderr'].splitlines():
            m=re.fullmatch(r'BAD_ROW,(\d+),b=([^,]+),terms=(.*)',line)
            if not m:continue
            i=int(m[1]);b=Decimal.from_float(float(m[2]));terms=ast.literal_eval(m[3]);out={'row':i,'b':str(b),'nnz':len(terms)}
            for label,index in [('schur',2),('reference',3)]:
                products=[Decimal.from_float(t[1])*Decimal.from_float(t[index]) for t in terms]
                residual=abs(sum(products,Decimal(0))-b);denom=abs(b)+sum(map(abs,products),Decimal(0))
                q=residual/denom if denom else Decimal(0)
                out[label]={'absolute_residual':str(residual),'componentwise_backward':str(q),'passes_original':q<=Decimal('1e-11')}
            rows.append(out)
    require(rows,'bad rows recorded')
    rejected=sum(not q['reference']['passes_original'] for q in rows)
    require(rejected>0,'baseline counterexample')
    write('evidence/voice_dynamic_schur_backward_analysis01.json',dict(passed=True,original_schur_gate_passed=False,reference_rejected_rows=rejected,rows=rows,source_sha256={'tools/analyze_dynamic_schur_backward.py':sha(ROOT/'tools/analyze_dynamic_schur_backward.py'),name:sha(ROOT/name)},precision=100,operands='exact Decimal.from_float binary64; no rounded decimal reinterpretation',scope='first preserved failing linear system only'))
    print('BACKWARD_BASELINE_COUNTEREXAMPLE',len(rows),rejected)
    print(json.dumps([q for q in rows if q['row'] in [14,243]],indent=2))

if __name__=='__main__':main()
