"""Full uneliminated nodal finite-difference loaded source-port oracle."""
import json
from pathlib import Path
import numpy as np
from mixer_on_native_vectors import ROOT,sha,network
from mixer_chain_vectors import solve
from circuit66_vca_release_probes import transient_evaluator
from cutoff_j7_vectors import setup
import mixer_panel_bus_reference as panel

OUTPUT=ROOT/'evidence/voice_mixer_chain_port_vectors01.json'
TEXT=ROOT/'evidence/voice_mixer_chain_port_vectors01.txt'
PROTOCOL='docs/MEZCLADOR_PUERTO_CARGADO_PROTOCOLO.md'

def fixtures():
    bank=json.loads((ROOT/'evidence/voice_mixer_chain_vectors01.json').read_text(encoding='utf8'));cases=[];lines=[]
    setups={r:setup(r) for r in (200,200000)}
    for case in bank['cases']:
        row=case['rows'][3];old=case['rows'][2];source=row['source_v'];mask=case['mask'];alpha=case['alpha'];r61=case['r61_ohm']
        history=dict(node_v=old['node_v'],capacitor_v=old['capacitor_v'],c10_v=old['c10_v']);values=setups[r61]
        g,_=network([bool(mask&(1<<i)) for i in range(5)],alpha,panel._sources());g=np.array(g,dtype=float)
        b=dict(bus_v=0.,loudness_v=2.,q21_base_v=2.,r21_lower_ohm=2000.,dt_s=1/48000);core=transient_evaluator(values,history,b);gc=10e-6/b['dt_s']
        seed=old['node_v']+[old['bus_v']]+[0.]*(len(g)-6)
        def observed(src):
            def evaluate(x):
                rr,_=core(x[:66].tolist() if isinstance(x,np.ndarray) else x[:66]);rr[6]+=gc*x[66]
                resistive=g@np.array([*src,*x[66:]])
                return [*rr,float(resistive[5])-gc*(x[6]-x[66]-history['capacitor_v'][5]),*resistive[6:].tolist()]
            x,kcl,correction=solve(seed,evaluate)
            current=(g@np.array([*src,*x[66:]]))[:5].tolist()
            return x,current,kcl,correction
        x,current,kcl,correction=observed(source);matrix=np.empty((5,5));gradient=np.empty((66,5));bus=[]
        for col in range(5):
            plus=source.copy();minus=source.copy();plus[col]+=.001;minus[col]-=.001
            xp,ip,_,_=observed(plus);xm,im,_,_=observed(minus)
            matrix[:,col]=(np.array(ip)-im)/.002;gradient[:,col]=(np.array(xp[:66])-xm[:66])/.002;bus.append((xp[66]-xm[66])/.002)
        result=dict(r61_ohm=r61,mask=mask,alpha=alpha,dt_s=b['dt_s'],source_v=source,previous=history,
            node_v=x[:66],bus_v=x[66],current_a=current,admittance_s=matrix.tolist(),node_gradient_v_per_v=gradient.tolist(),bus_gradient_v_per_v=bus,
            kcl_a=kcl,correction_v=correction)
        cases.append(result)
        flat=[r61,mask,*alpha,b['dt_s'],*source,*history['node_v'],*history['capacitor_v'],history['c10_v'],
              *x[:66],x[66],*current,*matrix.flatten(),*gradient.flatten(),*bus]
        lines.append(' '.join(format(float(v),'.17e') for v in flat));print('full source-port FD',r61,mask,flush=True)
    return cases,'\n'.join(lines)+'\n'

def main():
    if OUTPUT.exists() or TEXT.exists():raise ValueError('preserve full source-port oracle')
    qa=ROOT/'evidence/voice_mixer_chain_tests01.json';q=json.loads(qa.read_text(encoding='utf8'))
    sources={**q['source_sha256'],qa.relative_to(ROOT).as_posix():sha(qa),PROTOCOL:sha(ROOT/PROTOCOL),
        'tools/mixer_chain_port_vectors.py':sha(Path(__file__))}
    before={n:sha(ROOT/n) for n in sources}
    if sources!=before:raise ValueError('fixed incoming chain release')
    cases,text=fixtures();after={n:sha(ROOT/n) for n in before}
    if after!=before:raise ValueError('port oracle sources changed')
    TEXT.write_text(text,encoding='utf8',newline='\n')
    OUTPUT.write_text(json.dumps(dict(schema='rf-d/mixer-chain-loaded-port-vectors/v1',passed=True,cases=cases,
        source_sha256=before,source_sha256_after=after,columns=528,case_count=4,fd_source_delta_v=.001,
        text_sha256=sha(TEXT),new_spice_solves=0,native_seeds_used=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
    print('loaded source-port oracle 4 cases; columns',len(text.splitlines()[0].split()),flush=True)

if __name__=='__main__':main()
