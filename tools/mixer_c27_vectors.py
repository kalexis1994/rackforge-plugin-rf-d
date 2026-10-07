"""Full resistor nodes plus an Euler C27/history source; no Rust Schur formula."""
from decimal import Decimal as D,localcontext
import hashlib,json
from pathlib import Path
from mixer_on_native_vectors import ROOT,sha,network,solve
import mixer_panel_bus_reference as prior

CSV=ROOT/'evidence/voice_mixer_c27_vectors01.txt'
RECEIPT=ROOT/'evidence/voice_mixer_c27_vectors01.json'
PROTOCOL='docs/MEZCLADOR_C27_PROTOCOLO.md'
GATES=dict(voltage_v=1e-10,current_a=1e-13,admittance_s=1e-12)
INPUTS=(PROTOCOL,'tools/mixer_c27_vectors.py','tools/mixer_on_native_vectors.py',
        'tools/mixer_panel_bus_reference.py','evidence/mixer_panel_bus.json',
        'evidence/filter_input_board4.json','evidence/voice_mixer_on_vectors01.json')

def imposed(g,sources,base,history,gc):
    n=len(g);unknown=list(range(5,n));v=list(sources)+[D(0)]*(n-5)
    a=[[g[i][j]+(gc if i==j==5 else 0) for j in unknown] for i in unknown]
    rhs=[-sum(g[i][j]*v[j] for j in range(5))+(gc*(base-history) if i==5 else 0) for i in unknown]
    for i,x in zip(unknown,solve(a,rhs)):v[i]=x
    currents=[sum(g[i][j]*v[j] for j in range(n)) for i in range(5)]
    currents.append(gc*(base-v[5]-history))
    return v,currents

def fixtures():
    old=json.loads((ROOT/'evidence/voice_mixer_on_vectors01.json').read_text(encoding='utf8'))
    parts=prior._sources();rows=[]
    with localcontext() as ctx:
        ctx.prec=80
        for index,case in enumerate(old['cases']):
            included=case['included_on'];alpha=case['alpha'];mask=sum(1<<i for i,x in enumerate(included) if x)
            g,_=network(included,alpha,parts);sources=[D(str(x)) for x in case['terminal_v'][:5]]
            base=D(str((index%7-3)*.23));history=D(str((index%5-2)*.31))
            for dt in ('0.0000005','0.00002','0.001'):
                gc=D('0.00001')/D(dt)
                nodes,current=imposed(g,sources,base,history,gc)
                matrix=[[D(0)]*6 for _ in range(6)]
                for column in range(6):
                    _,ci=imposed(g,[D(int(i==column)) for i in range(5)],D(int(column==5)),D(0),gc)
                    for i in range(6):matrix[i][column]=ci[i]
                next_v=base-nodes[5];delta=next_v-history
                values=[mask,*alpha,*sources,base,history,D(dt),nodes[5],*current,
                        *(x for row in matrix for x in row),delta,next_v]
                rows.append(' '.join(format(float(x),'.17e') for x in values))
    return '\n'.join(rows)+'\n',len(rows)

def main():
    if CSV.exists() or RECEIPT.exists():raise ValueError('preserve prospective C27 vectors')
    before={n:sha(ROOT/n) for n in INPUTS}
    text,count=fixtures();after={n:sha(ROOT/n) for n in INPUTS}
    if before!=after or count!=837:raise ValueError('C27 oracle inputs changed')
    CSV.write_text(text,encoding='utf8',newline='\n')
    RECEIPT.write_text(json.dumps(dict(schema='rf-d/mixer-c27-vectors/v1',precision_digits=80,case_count=count,
        column_count=58,gates=GATES,source_sha256=before,source_sha256_after=after,
        vector_path=CSV.relative_to(ROOT).as_posix(),vector_sha256=sha(CSV),
        oracle='full resistor-node and C27 companion elimination with Decimal pivoting',
        new_spice_solves=0,full_ladder_integrated=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
    print('C27 independent cases',count,'columns',len(text.splitlines()[0].split()),flush=True)

if __name__=='__main__':main()
