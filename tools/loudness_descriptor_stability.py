"""Frozen local descriptor modes; no branch-selection or physical admission.

Eliminate algebraic variables in capacitor-voltage coordinates, with exact
zero mass retained on other nodes. C10's series resistor needs a real internal
node; replacing it by a capacitor directly across x22/x7 would change modes.
"""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import numpy as np

from loudness_chain94_reference import JointNetwork
from loudness_contour_reference import Network
from circuit66_vca_release_probes import CAPS
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence/loudness_descriptor_stability.json"

def pole_matching_error(a,b):
    """Conservative one-to-one matching retains multiplicity, without SciPy."""
    if len(a)!=len(b):raise ValueError("same finite-mode count required")
    pa=[complex(p["real_per_s"],p["imag_per_s"]) for p in a]
    pb=[complex(p["real_per_s"],p["imag_per_s"]) for p in b]
    pairs=sorted((abs(x-y)/(1+abs(x)),i,j) for i,x in enumerate(pa) for j,y in enumerate(pb))
    used_a=set();used_b=set();errors=[]
    for error,i,j in pairs:
        if i not in used_a and j not in used_b:
            used_a.add(i);used_b.add(j);errors.append(error)
    return max(errors)


def reduced_modes(g,capacitors,dt):
    n=len(g); k=len(capacitors)
    incidence=np.zeros((n,k))
    for col,(a,b,c) in enumerate(capacitors):
        if not np.isfinite(c) or c<=0:raise ValueError("positive finite capacitance required")
        incidence[a,col]=1.0
        if b is not None:incidence[b,col]=-1.0
    pivots=[a for a,_,_ in capacitors]
    if len(set(pivots))!=k:raise ValueError("declared independent capacitor coordinates required")
    algebraic=[i for i in range(n) if i not in pivots]
    bp=incidence[pivots,:].T
    td=np.zeros((n,k)); td[pivots,:]=np.linalg.solve(bp,np.eye(k))
    ta=np.zeros((n,n-k));ta[algebraic,:]=np.eye(n-k)
    ta[pivots,:]=-np.linalg.solve(bp,incidence[algebraic,:].T)
    transform=np.column_stack((td,ta))
    projected=incidence.T@transform
    target=np.column_stack((np.eye(k),np.zeros((k,n-k))))
    coordinate_error=float(np.max(np.abs(projected-target)))
    if coordinate_error>1e-12:raise ValueError("capacitor coordinate transformation failed")
    conductance=transform.T@g@transform
    gad=conductance[k:,:k]; gaa=conductance[k:,k:]
    back=np.linalg.solve(gaa,-gad)
    reduced=conductance[:k,:k]+conductance[:k,k:]@back
    cap=np.array([c for _,_,c in capacitors])
    generator=-reduced/cap[:,None]
    poles,vectors=np.linalg.eig(generator)
    full_vectors=(td+ta@back)@vectors
    mass=(incidence*cap)@incidence.T
    normg=np.linalg.norm(g,2);normc=np.linalg.norm(mass,2)
    rows=[]
    for col,pole in enumerate(poles):
        v=full_vectors[:,col]
        residual=np.linalg.norm((g+pole*mass)@v)/( (normg+abs(pole)*normc)*np.linalg.norm(v))
        amplification=1/(1-dt*pole)
        rows.append(dict(real_per_s=float(pole.real),imag_per_s=float(pole.imag),
            descriptor_relative_residual=float(residual),
            implicit_euler_amplification_abs=float(abs(amplification))))
    rows.sort(key=lambda p:(p["real_per_s"],p["imag_per_s"]))
    # A positive finite pole is a growing local mode. A transient snapshot is
    # not an equilibrium; negative frozen poles cannot admit latch switching.
    return dict(dynamic_rank=k,algebraic_unknowns=n-k,coordinate_error=coordinate_error,
        algebraic_condition_number=float(np.linalg.cond(gaa)) if n>k else None,poles=rows,
        max_real_per_s=max(p["real_per_s"] for p in rows),
        growing_modes=sum(p["real_per_s"]>1e-6 for p in rows),
        max_eigen_residual=max(p["descriptor_relative_residual"] for p in rows),
        max_implicit_euler_amplification=max(p["implicit_euler_amplification_abs"] for p in rows))


def joint_static(network,x,key,*,use_fd=False):
    _,g94=network.evaluator(key)(np.asarray(x),use_fd=use_fd)
    g=np.zeros((network.n+1,network.n+1));g[:-1,:-1]=g94
    # Series C10 MID--25.5k--Q30 base. Its open-DC midpoint equals x7.
    m=network.n;conductance=1/25500
    g[m,m]+=conductance;g[7,7]+=conductance
    g[m,7]-=conductance;g[7,m]-=conductance
    caps=[(a,b if isinstance(b,int) else None,c) for a,b,c in CAPS]
    caps.append((22,m,10e-6))
    contour=network.contour
    for _,a,b,c in contour.caps:
        a=66+contour.index[contour.alias[a]]
        bi=contour.index.get(contour.alias[b])
        caps.append((a,None if bi is None else 66+bi,c))
    return g,caps


def diagnostic_latch_caps(contour,offset,cbe_f,cbc_f):
    """Constant positive junction-shaped charge for singular-perturbation audit.

    These are NOT identified Q25/Q15 charge laws, and are never integrated.
    Orient BC collector->base to keep distinct declared coordinate pivots.
    """
    result=[]
    for ref in ("Q25","Q15"):
        device=next(p for p in contour.bjts if p["ref"]==ref)
        nodes=[contour.index.get(contour.alias[device[t]]) for t in ("base","collector","emitter")]
        b,c,e=[None if i is None else offset+i for i in nodes]
        result.extend([(b,e,cbe_f),(c,b,cbc_f)])
    return result


def generate():
    loaded=json.loads((ROOT/"evidence/loudness_chain94_fold.json").read_text())
    isolated=json.loads((ROOT/"evidence/loudness_contour_fold.json").read_text())
    cases=[]
    for label,roots,r61,key,dt in [("isolated",isolated["fold"]["analytic"]["roots"],None,10.0,.001)]+[
        ("loaded",c["analytic"]["roots"],c["r61_ohm"],c["fold"]["keyboard_v"],c["fold"]["dt_s"]) for c in loaded["cases"]]:
        network=Network() if r61 is None else JointNetwork(r61)
        for root in roots:
            state=root["state"]
            if r61 is None:
                x=np.array([state["node_v"][name] for name in network.nodes])
                _,g=network.evaluate(x,key)
                caps=[(network.index[network.alias[a]],network.index.get(network.alias[b]),c) for _,a,b,c in network.caps]
                gf=np.zeros((len(x),len(x)))
                for col in range(len(x)):
                    plus=x.copy();minus=x.copy();plus[col]+=1e-6;minus[col]-=1e-6
                    a,_=network.evaluate(plus,key,jacobian=False);b,_=network.evaluate(minus,key,jacobian=False)
                    gf[:,col]=(np.asarray(a)-np.asarray(b))/2e-6
                nodes=state["node_v"]
            else:
                x=state["node_v"]
                g,caps=joint_static(network,x,key)
                gf,_=joint_static(network,x,key,use_fd=True)
                nodes=state["contour"]["node_v"]
            a=reduced_modes(np.asarray(g),caps,dt)
            f=reduced_modes(gf,caps,dt)
            matching=pole_matching_error(a["poles"],f["poles"])
            cases.append(dict(scope=label,r61_ohm=r61,seed_policy=root["seed_policy"],
                q25_collector_v=nodes["RESET_COLLECTOR"],analytic=a,independent_fd=f,
                max_relative_pole_matching_error=matching,selected=None))
    paths=[ROOT/"tools/loudness_descriptor_stability.py",ROOT/"evidence/loudness_chain94_fold.json",ROOT/"evidence/loudness_contour_fold.json"]
    return dict(schema="rf-d/loudness-descriptor-stability/v1",cases=cases,
        method="frozen G+sC descriptor; exact rank-3/rank-21 capacitor coordinates; C10 internal series node",
        source_sha256={str(p.relative_to(ROOT)).replace("\\","/"):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        gates=dict(coordinate_error=1e-12,eigen_residual=1e-9,pole_matching_relative=5e-3),
        environment=environment(),selected=None,physical_switching_admitted=False,audio_admitted=False,
        limitation="Frozen Jacobian at transient roots, not equilibrium proof; missing junction/storage dynamics")

if __name__=="__main__":
    report=generate()
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    for c in report["cases"]:
        print(json.dumps(dict(scope=c["scope"],r61=c["r61_ohm"],q25=c["q25_collector_v"],
            max_real=c["analytic"]["max_real_per_s"],growing=c["analytic"]["growing_modes"],
            matching=c["max_relative_pole_matching_error"],residual=c["analytic"]["max_eigen_residual"])))
