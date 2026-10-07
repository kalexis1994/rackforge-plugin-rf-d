"""Independent full BUS/cursor/66-node Euler trajectory; no reduced port formula."""
import hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
from mixer_on_native_vectors import ROOT,sha,network
from circuit66_dc_vectors import dc_evaluator,solve_dc
from circuit66_vca_release_probes import transient_evaluator
from circuit66_r21_vectors import charges
from cutoff_j7_vectors import setup
import mixer_panel_bus_reference as panel

OUTPUT=ROOT/'evidence/voice_mixer_chain_vectors01.json'
TEXT=ROOT/'evidence/voice_mixer_chain_vectors01.txt'
PROTOCOL='docs/MEZCLADOR_CADENA_PROTOCOLO.md'
GATES=dict(node_v=1e-6,current_a=1e-9,kcl_a=1e-11,correction_v=1e-8)

def solve(seed,evaluate):
    x=np.array(seed,dtype=float)
    def direction(x,r):
        j=np.empty((len(x),len(x)))
        for column in range(len(x)):
            shifted=x.copy();shifted[column]+=1e-6
            j[:,column]=(np.array(evaluate(shifted))-r)/1e-6
        return np.linalg.solve(j,-r)
    for iteration in range(40):
        r=np.array(evaluate(x));error=float(np.max(np.abs(r)));d=direction(x,r);correction=float(np.max(np.abs(d)))
        if error<1e-11 and correction<1e-8:return x.tolist(),error,correction
        for power in range(32):
            trial=x+2.0**-power*d
            try:rr=np.array(evaluate(trial));next_error=float(np.max(np.abs(rr)))
            except (ValueError,OverflowError):continue
            decreased=(next_error<1e-11 and float(np.max(np.abs(direction(trial,rr))))<correction) if error<1e-11 else next_error<error
            if decreased:x=trial;break
        else:raise ValueError(f'full mixer/chain line search: KCL={error} correction={correction}')
    raise ValueError('full mixer/chain FD budget')

def fixtures():
    cases=[];text=[]
    for r61 in (200,200000):
        values=setup(r61);initial,kcl,correction=solve_dc(list(values[5]['node_v']),dc_evaluator(values,values[4]))
        for mask in (1,31):
            included=[bool(mask&(1<<i)) for i in range(5)];alpha=[.5]*4
            g,_=network(included,alpha,panel._sources());g=np.array(g,dtype=float);count=len(g)
            prior=initial+[0.]*(count-5)
            history=dict(node_v=initial,capacitor_v=charges(initial,0),c10_v=initial[22]-initial[7])
            case=dict(r61_ohm=r61,mask=mask,alpha=alpha,initial_node_v=initial,initial_history=history,rows=[])
            for step in range(16):
                sources=[(.08,-.05,.03,-.02,.04)[i]*(1 if step%8<4 else -1) for i in range(5)]
                boundary=dict(bus_v=0.,loudness_v=2.,q21_base_v=2.,r21_lower_ohm=2000.,dt_s=1/48000)
                core=transient_evaluator(values,history,boundary);gc=10e-6/boundary['dt_s']
                def evaluate(x):
                    rr,_=core(x[:66].tolist() if isinstance(x,np.ndarray) else x[:66])
                    rr[6]+=gc*x[66]
                    v=np.array([*sources,*x[66:]])
                    resistive=g@v
                    bus_current=float(resistive[5])-gc*(x[6]-x[66]-history['capacitor_v'][5])
                    return [*rr,bus_current,*resistive[6:].tolist()]
                x,kcl,correction=solve(prior,evaluate)
                capacitor=charges(x[:66],x[66]);series=25500.;gc=10e-6*48000
                i10=gc/(1+gc*series)*(x[22]-x[7]-history['c10_v']);c10=x[22]-x[7]-series*i10
                v=np.array([*sources,*x[66:]]);resistive=g@v
                current=[*resistive[:5].tolist(),gc*(x[6]-x[66]-history['capacitor_v'][5])]
                row=dict(source_v=sources,node_v=x[:66],bus_v=x[66],capacitor_v=capacitor,c10_v=c10,
                    current_a=current,kcl_a=kcl,correction_v=correction)
                case['rows'].append(row)
                flat=[r61,mask,*alpha,boundary['dt_s'],*sources,*history['node_v'],*history['capacitor_v'],history['c10_v'],
                    *x[:66],x[66],*capacitor,c10,*current]
                text.append(' '.join(format(float(v),'.17e') for v in flat))
                prior=x;history=dict(node_v=x[:66],capacitor_v=capacitor,c10_v=c10)
            cases.append(case);print('full nodal oracle',r61,mask,'16 steps',flush=True)
    return cases,'\n'.join(text)+'\n'

def main():
    if OUTPUT.exists() or TEXT.exists():raise ValueError('preserve full chain oracle')
    start=time.perf_counter();cases,text=fixtures()
    sources={PROTOCOL:sha(ROOT/PROTOCOL)}
    for module in tuple(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file:
            p=Path(file).resolve()
            if p.is_relative_to(ROOT/'tools') and p.suffix=='.py':sources[p.relative_to(ROOT).as_posix()]=sha(p)
    TEXT.write_text(text,encoding='utf8',newline='\n')
    OUTPUT.write_text(json.dumps(dict(schema='rf-d/mixer-chain-oracle/v1',passed=True,cases=cases,gates=GATES,
        source_sha256=sources,text_sha256=sha(TEXT),rows=64,columns=len(text.splitlines()[0].split()),wall_s=time.perf_counter()-start,
        native_seeds_used=False,new_spice_solves=0,full_native_chain_admitted=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
    print('independent mixer/chain oracle',len(cases),'cases, 64 steps',flush=True)

if __name__=='__main__':main()
