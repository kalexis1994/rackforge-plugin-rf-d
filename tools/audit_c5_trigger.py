"""Original network checks and clock refinement; never replay old voice audio."""
import base64
import csv
import hashlib
import json
import math
import time
import traceback
from pathlib import Path
from c5_trigger_reference import ROOT,network,expanded,fd,charge_increment,_solve_linear

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
def physical(s):return [h+l for h,l in zip(s[:54],s[54:])]
def perturb(s,col,h):
    v=s.copy();v[col]+=h
    return v

def static(n,s,key):return n.evaluate(expanded(physical(s)),key,jacobian=False)[0]

def port_currents(n,s,key):
    ports=[0.]*9
    slots={'GROUND':0,'EXTERNAL_S_TRIGGER':0,'CONTOUR_SUPPLY':1,'MINUS_10':2,'PLUS_10':3,'KEYBOARD_TRIGGER':4,'VCA_CONTROL_LOAD':5,'TAIL':6,'CUTOFF_TH':7,'RANGE_TH':8}
    v=dict(n.rails,KEYBOARD_TRIGGER=key);v.update(zip(n.nodes,expanded(physical(s))))
    def add(name,i):
        if name in slots:ports[slots[name]]+=i
    for _,a,b,r in n.resistors:
        current=(v[a]-v[b])/r;add(a,current);add(b,-current)
    vt=n.vt
    for p in n.bjts:
        b,c,e=(p[k] for k in ['base','collector','emitter']);sign=1 if p['kind']=='NPN' else -1
        f=1e-14*math.expm1(sign*(v[b]-v[e])/vt);r=1e-14*math.expm1(sign*(v[b]-v[c])/vt)
        ib=sign*(f/100.+r/5.);ic=sign*(f-1.2*r);add(b,ib);add(c,ic);add(e,-ib-ic)
    for p in n.diodes:
        a,b=p['anode'],p['cathode'];isat=1e-8 if p['marking']=='1N34A' else 1e-12
        current=isat*math.expm1((v[a]-v[b])/(1.5*vt));add(a,current);add(b,-current)
    return ports

def stamp_reference(n,old,now,key,h):
    # All 54 columns, fixed old history. Cursor recomputed from original star.
    j=fd(lambda x:static(n,x+now[54:],key)[:54],now[:54])
    mass=fd(lambda x:[q/h for q in charge_increment(old,x+now[54:],n.optional)],now[:54])
    return j,mass

def compare_matrix(native,reference):
    fractions=[abs(a-b)/(2e-9+2e-5*abs(b)) for a,b in zip(native,[v for row in reference for v in row])]
    assert len(fractions)==2916 and max(fractions)<=1,('FD matrix gate',max(fractions))
    return max(fractions)

def audit(native_name):
    receipt=json.loads((ROOT/native_name).read_text());assert receipt['passed'] and receipt['source_unchanged'] and receipt['library_unchanged']
    for name,h in receipt['source_sha256'].items():assert sha(ROOT/name)==h,name
    for name,h in receipt['private_sha256'].items():assert sha(ROOT/name)==h,name
    directory=ROOT/receipt['output_directory'];inputs=json.loads((directory/'original_inputs.json').read_text())
    outputs=[];traces={};total_rows=0;fd_entries=0;begun=time.monotonic()
    for profile in receipt['profiles']:
        started=time.monotonic();optional=bool(profile['optional']);mode=profile['mode'];maximum=profile['maximum_us']
        rows=list(csv.reader((directory/(profile['label']+'.stdout')).read_text().splitlines()))
        summary=dict(optional=optional,mode=mode,maximum_us=maximum,max_original_kcl_a=0.,max_original_correction_v=0.,
                     max_fd_gate_fraction=0.,max_dc_error_v=0.,max_charge_ledger_error_c=0.,max_port_error_a=0.,
                     grid_count=0,root_count=0,stamp_entries=0)
        trace={};last=None;stage=0;event_states=[];ledger=None;dc_state=None;final=None
        for row in rows:
            kind=row[0]
            if kind=='DC':
                v=list(map(float,row[4:]));assert len(v)==108+54+9+2916
                dc_state=v[:108];original=inputs['dc'][int(optional)]['original_root']
                error=max(abs(a-b) for a,b in zip(physical(dc_state),original[:54]));assert error<=1e-6
                summary['max_dc_error_v']=error
                n=network(optional,False);res=static(n,dc_state,0.)
                assert max(map(abs,res))<=2e-11
                j=fd(lambda x:static(n,x+dc_state[54:],0.)[:54],dc_state[:54])
                summary['max_fd_gate_fraction']=compare_matrix(v[171:],j);fd_entries+=2916;summary['stamp_entries']+=2916
            elif kind=='EVENT':
                v=list(map(float,row[1:]));assert len(v)==3+108
                event_states.append(dict(tick=int(v[0]),key=v[1],short=bool(v[2]),c5_v=v[3+38]+v[3+54+38],c2_v=v[3+5]+v[3+54+5]))
            elif kind=='ROOT':
                v=list(map(float,row[1:]));assert len(v)==545
                h,key,short=v[:3];old=v[3:111];states=[v[327:435],v[435:543]]
                n=network(optional,bool(short));r=[static(n,s,key) for s in states]
                q=[charge_increment(old,s,optional) for s in states]
                residual=[[r[i][k]+(1.5 if i==0 else -4.5)*q[0][k]/h+(.5 if i==0 else 2.5)*q[1][k]/h for k in range(54)] for i in range(2)]
                error=max(abs(v) for block in residual for v in block);assert error<=2e-11,('original Radau KCL',profile['label'],h,error)
                assert max(abs(r[i][54]) for i in range(2))<=2e-11
                summary['max_original_kcl_a']=max(summary['max_original_kcl_a'],error)
                summary['root_count']+=1;total_rows+=110
                last=dict(old=old,states=states,n=n,key=key,h=h,residual=residual,matrices=[]);stage=0
            elif kind=='STAMP':
                v=list(map(float,row[1:]));assert len(v)==5832
                j,mass=stamp_reference(last['n'],last['old'],last['states'][stage],last['key'],last['h'])
                summary['max_fd_gate_fraction']=max(summary['max_fd_gate_fraction'],compare_matrix(v[:2916],j),compare_matrix(v[2916:],mass))
                fd_entries+=5832;summary['stamp_entries']+=5832;last['matrices'].append((j,mass));stage+=1
                if stage==2:
                    b=[[1.5,.5],[-4.5,2.5]]
                    a=[[b[i][jj]*last['matrices'][jj][1][r][col]+(last['matrices'][i][0][r][col] if i==jj else 0.)
                        for jj in range(2) for col in range(54)] for i in range(2) for r in range(54)]
                    direction=_solve_linear(a,[-v for rr in last['residual'] for v in rr]);correction=max(map(abs,direction))
                    assert correction<=2e-9,('original Newton correction',profile['label'],correction)
                    summary['max_original_correction_v']=max(summary['max_original_correction_v'],correction)
            elif kind=='GRID':
                v=list(map(float,row[1:]));assert len(v)==120
                tick=int(v[0]);key=v[1];short=bool(v[2]);s=v[3:111];ports=v[111:120]
                n=network(optional,short);refports=port_currents(n,s,key)
                error=max(abs(a-b) for a,b in zip(refports,ports));assert error<=2e-9
                summary['max_port_error_a']=max(summary['max_port_error_a'],error)
                trace[tick]=(s,ports);summary['grid_count']+=1
            elif kind=='LEDGER':
                ledger=list(map(float,row[1:]));assert len(ledger)==117
            elif kind=='FINAL':
                v=list(map(float,row[1:]));assert len(v)==6+216
                final=v[114:222];assert v[2]==4 and v[4]==4 and v[3]==summary['root_count']
                summary.update(accepted_steps=int(v[0]),local_replays=int(v[1]),events=int(v[2]),atomic_rejections=int(v[4]),native_wall_s=v[5])
            elif kind in ['SELECT','ACCEPT']:continue
            else:raise ValueError(kind)
        assert summary['grid_count']==144 and len(event_states)==4 and final is not None
        independent_q=charge_increment(dc_state,final,optional)
        qerror=max(abs(a-b) for a,b in zip(independent_q,ledger[54:108]))
        balance=max(abs(a+b) for a,b in zip(independent_q,ledger[:54]))
        assert qerror<=2e-11*.036 and balance<=2e-11*.036,(profile['label'],'charge ledger',qerror,balance)
        assert abs(sum(ledger[108:]))<=2e-11*.036,('terminal ledger',sum(ledger[108:]))
        summary['max_charge_ledger_error_c']=max(qerror,balance)
        summary['terminal_ledger_error_c']=abs(sum(ledger[108:]));summary['event_states']=event_states
        for timer in [5,38]:
            idle=physical(dc_state)[timer]
            at=lambda us:physical(trace[us*1073741824][0])[timer]
            held_peak=max(physical(s)[timer] for tick,(s,_) in trace.items() if 1000*1073741824<tick<=10000*1073741824)
            assert held_peak>idle+.1,(mode,timer,'no attack',held_peak,idle)
            release_peak=max(physical(s)[timer] for tick,(s,_) in trace.items() if 10000*1073741824<=tick<=20000*1073741824)
            assert at(20000)<release_peak-.1,(mode,timer,'no decay after actual peak',release_peak,at(20000))
            assert at(30000)>at(20000)+.1,(mode,timer,'no retrigger')
            summary['c5' if timer==38 else 'c2']=dict(idle_v=idle,first_peak_v=held_peak,post_source_release_peak_v=release_peak,release_v=at(20000),second_held_v=at(30000),final_v=at(36000))
        summary['audit_wall_s']=time.monotonic()-started
        assert summary['audit_wall_s']<=300
        outputs.append(summary);traces[(optional,mode,maximum)]=trace
    refinements=[]
    for optional in [False,True]:
        for mode in ['key','s']:
            a=traces[(optional,mode,8)];b=traces[(optional,mode,4)];maximum=0.;portmax=0.
            for tick,(s,ports) in a.items():
                t,tp=b[tick]
                maximum=max(maximum,max(abs(v-w)/(2e-5+2e-6*abs(w)) for v,w in zip(physical(s),physical(t))))
                portmax=max(portmax,max(abs(v-w)/(2e-9+2e-5*abs(w)) for v,w in zip(ports,tp)))
            assert maximum<=1 and portmax<=1,('refinement',optional,mode,maximum,portmax)
            refinements.append(dict(optional=optional,mode=mode,common_clocks=144,node_gate_fraction=maximum,port_gate_fraction=portmax))
    return dict(schema='rf-d/dual-contour/reference-v1',passed=True,native_receipt=native_name,
                native_receipt_sha256=sha(ROOT/native_name),source_sha256={str(Path(__file__).relative_to(ROOT)).replace('\\','/'):sha(Path(__file__))},
                profiles=outputs,refinement=refinements,original_rows=total_rows,fd_entries=fd_entries,
                wall_s=time.monotonic()-begun,physical_fidelity=False,real_time=False)

def main():
    native='evidence/c5_trigger_native02.json'
    try:r=audit(native)
    except Exception:
        first=traceback.format_exc()
        try:audit(native)
        except Exception:replay=traceback.format_exc()
        else:replay='unexpected pass'
        k=1
        while (ROOT/f'evidence/c5_trigger_reference_failure{k:02d}.json').exists():k+=1
        write(ROOT/f'evidence/c5_trigger_reference_failure{k:02d}.json',dict(passed=False,failure=first,replay=replay,
              source_base64=base64.b64encode(Path(__file__).read_bytes()).decode(),native_sha256=sha(ROOT/native)))
        raise
    write(ROOT/'evidence/c5_trigger_reference01.json',r)
    print('C5_TRIGGER_REFERENCE',r['passed'],r['original_rows'],r['fd_entries'],r['wall_s'])
if __name__=='__main__':main()
