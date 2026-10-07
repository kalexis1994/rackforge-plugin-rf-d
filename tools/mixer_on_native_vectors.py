"""Independent 80-digit resistor-node oracle for the Rust ON mixer stamp."""
from decimal import Decimal as D, localcontext
import hashlib,json
from pathlib import Path
import mixer_panel_bus_reference as prior
from vco1_panel_level_reference import pot_series_admittance

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/voice_mixer_on_vectors01.json'
NAMES=('OSC1','OSC2','OSC3','NOISE','EXT')
PROTOCOL='docs/MEZCLADOR_NATIVO_PROTOCOLO.md'
GATES=dict(admittance_s=1e-15,voltage_v=1e-10,current_a=1e-14,power_w=1e-13,
           voltage_slope=1e-10,resistance_slope_ohm=1e-9,current_slope=1e-12)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def solve(matrix,rhs):
    a=[list(row)+[b] for row,b in zip(matrix,rhs)];n=len(a)
    for col in range(n):
        pivot=max(range(col,n),key=lambda i:abs(a[i][col]))
        if not a[pivot][col]:raise ValueError('singular independent resistor nodes')
        a[col],a[pivot]=a[pivot],a[col]
        scale=a[col][col];a[col]=[v/scale for v in a[col]]
        for row in range(n):
            if row==col:continue
            scale=a[row][col]
            a[row]=[x-scale*y for x,y in zip(a[row],a[col])]
    return [a[i][-1] for i in range(n)]

def network(included,alpha,parts):
    edges=[];count=6
    for i,name in enumerate(NAMES):
        if not included[i]:continue
        p=parts[name]
        if i==4:edges.append((i,5,D(p['series_ohm'])));continue
        a=D(str(alpha[i]));track=D(p['pot_ohm']);series=D(p['series_ohm'])
        if a==0:
            edges.extend(((i,-1,track),(5,-1,series)))
        elif a==1:
            edges.extend(((i,-1,track),(i,5,series)))
        else:
            cursor=count;count+=1
            edges.extend(((i,cursor,(1-a)*track),(cursor,-1,a*track),(cursor,5,series)))
    g=[[D(0) for _ in range(count)] for _ in range(count)]
    for left,right,resistance in edges:
        conductance=1/resistance
        if left>=0:g[left][left]+=conductance
        if right>=0:g[right][right]+=conductance
        if min(left,right)>=0:g[left][right]-=conductance;g[right][left]-=conductance
    return g,edges

def imposed_ports(g,values):
    n=len(g);unknown=list(range(6,n));v=list(values)+[D(0)]*(n-6)
    if unknown:
        a=[[g[i][j] for j in unknown] for i in unknown]
        rhs=[-sum(g[i][j]*v[j] for j in range(6)) for i in unknown]
        for i,x in zip(unknown,solve(a,rhs)):v[i]=x
    currents=[sum(g[i][j]*v[j] for j in range(n)) for i in range(6)]
    return v,currents

def imposed_board(g,sources,board):
    n=len(g);unknown=list(range(5,n));v=list(sources)+[D(0)]*(n-5)
    a=[[g[i][j] for j in unknown] for i in unknown]
    rhs=[-sum(g[i][j]*v[j] for j in range(5))-(board if i==5 else 0) for i in unknown]
    for i,x in zip(unknown,solve(a,rhs)):v[i]=x
    currents=[sum(g[i][j]*v[j] for j in range(n)) for i in range(6)]
    return v,currents

def fixtures():
    parts=prior._sources()
    profiles=([0.]*4,[1.]*4,[1e-9]*4,[1-1e-9]*4,[.25]*4,[.5]*4,[.75]*4,
              [0.,.25,.75,1.],[1e-9,.2,.8,1-1e-9])
    cases=[];maxima=dict(legacy_bus_voltage_v=0.,legacy_bus_current_a=0.,legacy_bus_weight=0.,
        legacy_board_resistance_ohm=0.,legacy_two_port_admittance_s=0.)
    worst={}
    with localcontext() as context:
        context.prec=80
        for mask in range(1,32):
            included=[bool(mask&(1<<i)) for i in range(5)]
            for profile,alpha in enumerate(profiles):
                g,edges=network(included,alpha,parts)
                matrix=[[D(0)]*6 for _ in range(6)]
                for column in range(6):
                    basis=[D(int(i==column)) for i in range(6)];_,currents=imposed_ports(g,basis)
                    for row in range(6):matrix[row][column]=currents[row]
                source=[D(str(x)) for x in (1.2,-.4,.3,-.2,.5)]
                if mask%2==0:source=[-2*x for x in source]
                bus=D(str((profile-4)*.7));port_v=[*source,bus]
                nodes,currents=imposed_ports(g,port_v)
                power=sum((nodes[l]-(nodes[r] if r>=0 else 0))**2/res for l,r,res in edges)
                board=D(str((-2e-6,0.,3e-6)[(mask+profile)%3]))
                solved,solved_currents=imposed_board(g,source,board)
                weights=[];reduced=[[D(0)]*5 for _ in range(5)]
                for column in range(5):
                    basis=[D(int(i==column)) for i in range(5)];v,ci=imposed_board(g,basis,D(0))
                    weights.append(v[5])
                    for row in range(5):reduced[row][column]=ci[row]
                load_v,load_i=imposed_board(g,[D(0)]*5,D(1))
                av={NAMES[i]:alpha[i] for i in range(4) if included[i]}
                legacy=prior.solve_mixer_bus({NAMES[i]:float(source[i]) for i in range(5) if included[i]},av,float(board))
                differences=dict(legacy_bus_voltage_v=abs(legacy['bus_voltage_v']-float(solved[5])),
                    legacy_bus_current_a=0.,
                    legacy_bus_weight=max(abs(legacy['reference']['boundary_voltage_coefficients'][NAMES[i]]-float(weights[i])) for i in range(5) if included[i]),
                    legacy_board_resistance_ohm=abs(legacy['reference']['board_current_to_bus_voltage_ohm']-float(load_v[5])),
                    legacy_two_port_admittance_s=0.)
                # Per-branch currents from the original edge network at the solved bus.
                branch_deltas=[]
                for i,name in enumerate(NAMES):
                    if not included[i]:continue
                    one=[j==i for j in range(5)];sg,_=network(one,alpha,parts)
                    _,branch_currents=imposed_ports(sg,[*source,solved[5]])
                    branch_deltas.append(abs(float(branch_currents[5])-legacy['currents_leaving_bus_to_panel_a'][name]))
                    if i<4:
                        old=pot_series_admittance(alpha[i],parts[name]['pot_ohm'],parts[name]['series_ohm'])
                        cols=[]
                        for column in (i,5):
                            _,c=imposed_ports(sg,[D(int(j==column)) for j in range(6)]);cols.append(c)
                        differences['legacy_two_port_admittance_s']=max(differences['legacy_two_port_admittance_s'],
                            *(abs(old[r][c]-float(cols[c][(i,5)[r]])) for r in range(2) for c in range(2)))
                differences['legacy_bus_current_a']=max(branch_deltas)
                for key,value in differences.items():
                    if value>maxima[key]:maxima[key]=value;worst[key]=dict(mask=mask,profile=profile)
                convert=lambda a:[float(v) for v in a]
                cases.append(dict(id=f'on{mask:02d}-profile{profile}',included_on=included,alpha=alpha,
                    terminal_v=convert(port_v),admittance_s=[convert(row) for row in matrix],current_a=convert(currents),
                    dissipated_power_w=float(power),board_current_a=float(board),bus_v=float(solved[5]),
                    solved_current_a=convert(solved_currents),d_bus_d_source=convert(weights),
                    d_bus_d_board_current_ohm=float(load_v[5]),d_source_current_d_source_s=[convert(row) for row in reduced],
                    d_source_current_d_board_current=convert(load_i[:5]),legacy_differences=differences))
    return cases,maxima,worst

def main():
    if OUTPUT.exists():raise ValueError('preserve native mixer vectors')
    sources=[Path(__file__),ROOT/PROTOCOL,ROOT/'tools/mixer_panel_bus_reference.py',
             ROOT/'tools/vco1_panel_level_reference.py',ROOT/'evidence/mixer_panel_bus.json',ROOT/'evidence/vco1_panel_pulse_width.json']
    before={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
    cases,maxima,worst=fixtures();after={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
    if before!=after:raise ValueError('oracle inputs changed')
    legacy_passed=(maxima['legacy_bus_voltage_v']<=GATES['voltage_v'] and maxima['legacy_bus_current_a']<=GATES['current_a']
        and maxima['legacy_bus_weight']<=GATES['voltage_slope'] and maxima['legacy_board_resistance_ohm']<=GATES['resistance_slope_ohm'])
    report=dict(schema='rf-d/mixer-on-native-vectors/v1',source_sha256=before,source_sha256_after=after,
        precision_digits=80,oracle='full resistor-node elimination; Decimal Gauss-Jordan with pivoting',
        gates=GATES,source_names=list(NAMES),cases=cases,case_count=len(cases),legacy_bus_comparison_passed=legacy_passed,
        legacy_maxima=maxima,legacy_worst_cases=worst,legacy_two_port_diagnostic_only=True,
        new_spice_solves=0,new_audio=False,physical_fidelity=False,real_time=False)
    OUTPUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('mixer vectors:',len(cases),'legacy bus gate:',legacy_passed,'legacy matrix diagnostic:',maxima['legacy_two_port_admittance_s'],flush=True)

if __name__=='__main__':main()
