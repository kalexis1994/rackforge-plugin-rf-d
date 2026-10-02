"""Independent outgoing-current static graph; Decimal currents and analytic stamps.

Same conditional Ebers-Moll/Shockley laws and binary64 parameters as the
66-node oracle. No charge, Newton solve, physical fit or audio callback.
"""
from decimal import Decimal as D, localcontext
import math
from cutoff_ebers_moll_reference import panel_equivalent
from filter_ladder_ebers_moll_dc_reference import DEVICE_NODES
from headphone_amp_active_dc_reference import _graph, NODES as HP_NODES
from semiconductor_ideal import thermal_voltage_v


def lift(value):
    if isinstance(value, D):
        return value
    if isinstance(value, int):
        return D(value)
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("finite coefficients required")
    return D.from_float(value)


def graph(values):
    ladder, recovery, output, hp, controls, _, _ = values
    lp = ladder["network_parameters"]; rp = recovery["network_parameters"]
    op = output["network_parameters"]
    p1 = op["first_parameters"]["core_parameters"]; p2 = op["second_parameters"]
    po = op["output_parameters"]
    fixed = {"GND": 0., "PLUS": lp["plus"], "MINUS": p1["minus_v"],
        "HP_MINUS10": -10., "HP_MINUS20": -20., "LOUD": p1["loudness_v"],
        "Q21_BASE": p2["q21_base_v"]}
    result = dict(node_count=66, fixed=fixed, resistors=[], conductances=[], bjts=[], diodes=[])

    def resistor(ref, left, right, ohm):
        if not math.isfinite(ohm) or ohm <= 0:
            raise ValueError("positive finite static branch required")
        result["resistors"].append(dict(ref=ref,left=left,right=right,ohm=ohm))

    def bjt(ref, base, collector, emitter, parameters, polarity=1):
        result["bjts"].append(dict(ref=ref,base=base,collector=collector,emitter=emitter,
            polarity=polarity,is_a=parameters["is_a"][ref],vt=parameters["vt"],
            beta_forward=parameters["beta_forward"][ref],beta_reverse=parameters["beta_reverse"][ref]))

    for i, ohm in enumerate(lp["spine_resistances"]):
        resistor("ladder-spine-"+str(i), "PLUS" if i == 0 else i-1, i, ohm)
    resistor("R61",4,"GND",lp["r61_ohm"])
    resistor("R54",4,6,lp["r54"]); resistor("R30-ladder",4,7,lp["r30"])
    for ref, (base, collector, emitter) in DEVICE_NODES.items():
        bjt(ref,base,"PLUS" if collector is None else collector,emitter,
            dict(is_a=lp["values_is"],beta_forward=lp["values_bf"],beta_reverse=lp["reverse_beta"],vt=lp["vt"]))
    for ref, a, b in (("R31",16,"GND"),("R38",17,"GND"),("R24",18,"MINUS"),
                     ("R20",19,"MINUS"),("R26",20,"MINUS"),("R3",22,21),
                     ("R7",23,22),("R6","PLUS",23)):
        resistor(ref+"-recovery",a,b,rp["resistance"][ref])
    for ref, b, c, e in (("Q8",16,21,18),("Q6",17,"PLUS",19),("Q7",18,21,20),("Q5",19,"PLUS",20)):
        bjt(ref+"-recovery",b,c,e,{k:({ref+"-recovery":v[ref]} if isinstance(v,dict) else v)
            for k,v in rp.items() if k in ("is_a","beta_forward","beta_reverse","vt")})
    resistor("R2-input",21,24,82000)
    r=p1["r"]; left=p1["left_ohm"]
    for ref,a,b,ohm in (("R34",25,26,r["R34"]),("R22",33,26,r["R22"]),("R36",26,"GND",r["R36"]),
        ("R35",27,28,r["R35"]),("R37",29,"GND",r["R37"]),("R43",29,"MINUS",r["R43"]),
        ("R19+R14L",33,30,r["R19"]+left),("R23+R14R",33,31,r["R23"]+r["R14_BOARD4"]-left),
        ("R59",32,"LOUD",r["R59"]),("R13",39,33,r["R13"])):
        resistor(ref+"-VCA1",a,b,ohm)
    for ref,b,c,e in (("Q16",25,30,27),("Q15",26,31,27),("Q18",32,28,29)):
        bjt(ref+"-VCA1",b,c,e,{k:({ref+"-VCA1":v[ref]} if isinstance(v,dict) else v)
            for k,v in p1.items() if k in ("is_a","beta_forward","beta_reverse","vt")})
    r=p2["r"]; left=p2["left_ohm"]
    for ref,a,b,ohm in (("R33",34,35,r["R33"]),("R42",36,"GND",r["R42"]),("R44",36,"MINUS",r["R44"]),
        ("R18+R12L",39,37,r["R18"]+left),("R21+R12R",39,38,r["R21"]+r["R12"]-left),
        ("R11",40,39,r["R11"])):
        resistor(ref+"-VCA2",a,b,ohm)
    for ref,b,c,e in (("Q14",30,37,34),("Q13",31,38,34),("Q21","Q21_BASE",35,36)):
        bjt(ref+"-VCA2",b,c,e,{k:({ref+"-VCA2":v[ref]} if isinstance(v,dict) else v)
            for k,v in p2.items() if k in ("is_a","beta_forward","beta_reverse","vt")})
    r=po["r"]
    for ref,a,b in (("R9","PLUS",41),("R8",42,43),("R28",42,44),("R30",45,"GND"),
                    ("R29",46,"GND"),("R10","PLUS",40)):
        resistor(ref+"-conversion",a,b,r[ref])
    for ref,b,c,e in (("Q1",40,42,41),("Q12",37,45,43),("Q17",38,46,44)):
        bjt(ref+"-conversion",b,c,e,{k:({ref+"-conversion":v[ref]} if isinstance(v,dict) else v)
            for k,v in po.items() if k in ("is_a","beta_forward","beta_reverse","vt")},-1)

    def diode(ref,a,c,model,vt):
        result["diodes"].append(dict(ref=ref,anode=a,cathode=c,is_a=model["is_a"],
            ideality=model["ideality"],vt=vt))

    if po["diode_model"] is not None:
        diode("CR1-conversion",46,"PLUS",po["diode_model"],po["vt"])
        diode("CR2-conversion","GND",46,po["diode_model"],po["vt"])
    # Preserve the same rounded Thevenin constants used by the binary oracle.
    cursor=1/(1/2500+1/10000+1/(33000+1/(1/1000+1/100000)))
    resistor("R20-ON-equivalent",47,"GND",1000+2500+cursor)
    resistor("R77",47,48,1000);resistor("R21-upper",48,49,3000);resistor("R21-lower",49,"GND",2000)
    hg=_graph();hi={name:50+i for i,name in enumerate(HP_NODES)}
    hi.update(MINUS_10="HP_MINUS10",MINUS_20="HP_MINUS20",GROUND="GND")
    for row in hg["resistors"]:
        resistor(row["ref"]+"-HP",*(hi[v] for v in row["between"]),row["ohm"])
    ht=thermal_voltage_v(hp["temperature_k"])
    for row in hg["active_devices"]:
        if row["ref"].startswith("Q"):
            ref=row["ref"]+"-HP"
            bjt(ref,*(hi[row[k]] for k in ("base","collector","emitter")),
                dict(is_a={ref:hp["transistor_is_a"]},beta_forward={ref:hp["beta_forward"]},
                     beta_reverse={ref:hp["beta_reverse"]},vt=ht),-1 if row["marking"]=="TIS-93" else 1)
        else:
            diode(row["ref"]+"-HP",hi[row["anode"]],hi[row["cathode"]],hp["diode_model"],ht)
    result["conductances"].append(dict(ref="J7-load",left=61,right="GND",siemens=1/390+1/32+1/32))
    pv,pg=panel_equivalent(controls["panel"]);fixed["PANEL"]=pv
    result["conductances"].append(dict(ref="panel-Thevenin",left=62,right="PANEL",siemens=pg))
    fraction=controls["range_fraction"];fixed["RANGE"]=10*fraction
    resistor("RANGE-Thevenin",63,"RANGE",68000+10000*fraction*(1-fraction))
    fixed["CONTROL_MINUS"]=-10.;resistor("R39-control",64,"CONTROL_MINUS",330)
    resistor("R60-tail",5,65,680)
    for ref,b,c,e,s in (("q26",62,64,63,-1),("q28",63,65,"GND",1)):
        param=controls[ref];tag=ref.upper()+"-control"
        bjt(tag,b,c,e,dict(is_a={tag:param["is_a"]},beta_forward={tag:param["beta_forward"]},
            beta_reverse={tag:param["beta_reverse"]},vt=thermal_voltage_v(param["temperature_k"])),s)
    return result


def evaluate(graph, node_v, precision=80, jacobian=True):
    if len(node_v)!=graph["node_count"] or precision < 40:
        raise ValueError("complete nodes and at least Decimal40 required")
    with localcontext() as ctx:
        ctx.prec=precision
        nodes=[lift(v) for v in node_v];fixed={k:lift(v) for k,v in graph["fixed"].items()}
        n=len(nodes);r=[D(0) for _ in nodes];j=[[D(0) for _ in nodes] for _ in nodes] if jacobian else None
        def voltage(node):return nodes[node] if isinstance(node,int) else fixed[node]
        def add(row,current,gradient):
            if not isinstance(row,int):return
            r[row]+=current
            if jacobian:
                for col,value in gradient:
                    if isinstance(col,int):j[row][col]+=value
        def branch(left,right,current,g):
            add(left,current,((left,g),(right,-g)));add(right,-current,((left,-g),(right,g)))
        for item in graph["resistors"]+graph["conductances"]:
            g=1/lift(item["ohm"]) if "ohm" in item else lift(item["siemens"])
            a,b=item["left"],item["right"];branch(a,b,g*(voltage(a)-voltage(b)),g)
        for q in graph["bjts"]:
            b,c,e=q["base"],q["collector"],q["emitter"];s=q["polarity"]
            vt=lift(q["vt"]);sat=lift(q["is_a"]);bf=lift(q["beta_forward"]);br=lift(q["beta_reverse"])
            be=s*(voltage(b)-voltage(e))/vt;bc=s*(voltage(b)-voltage(c))/vt
            if max(be,bc)>45:raise ValueError("BJT exponential domain exceeded")
            ef=sat*be.exp();er=sat*bc.exp();f=ef-sat;rev=er-sat
            ib=f/bf+rev/br;ic=f-(1+1/br)*rev
            gf=ef/vt;gr=er/vt
            gb=((b,gf/bf+gr/br),(e,-gf/bf),(c,-gr/br))
            gc=((b,gf-(1+1/br)*gr),(e,-gf),(c,(1+1/br)*gr))
            ge=((b,-(1+1/bf)*gf+gr),(e,(1+1/bf)*gf),(c,-gr))
            add(b,s*ib,gb);add(c,s*ic,gc);add(e,-s*(ib+ic),ge)
        for diode in graph["diodes"]:
            a,c=diode["anode"],diode["cathode"];vt=lift(diode["ideality"])*lift(diode["vt"])
            exponent=(voltage(a)-voltage(c))/vt
            if exponent>45:raise ValueError("diode exponential domain exceeded")
            ef=lift(diode["is_a"])*exponent.exp()
            branch(a,c,ef-lift(diode["is_a"]),ef/vt)
        return r,j
