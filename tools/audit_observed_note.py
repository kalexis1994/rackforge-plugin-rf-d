"""Same-clock electrical/audio gates; original selected circuit equations."""
import base64,json,sys,time,traceback,gzip
from decimal import localcontext
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from audit_voice_sparse import assemble,gate,di,N,B
from dual_chain_reference import Original,matrix

def trace(path):
    grid={};roots=[];dc=None;final=None
    text=path.read_text(encoding='utf8') if path.exists() else gzip.decompress(path.with_suffix(path.suffix+'.gz').read_bytes()).decode('utf8')
    for line in text.splitlines():
        tag,*tokens=line.split(',');x=list(map(float,tokens))
        if tag=='DC':dc=x[4:];grid[0]=(dc,None)
        elif tag=='ROOT':roots.append(x)
        elif tag=='GRID':grid[int(tokens[0])]=(x[1:501],x[-2:])
        elif tag=='FINAL':final=dict(ticks=int(tokens[0]),steps=int(tokens[1]),selected_pairs=int(tokens[2]),atomic_rejections=int(tokens[3]),wall_s=x[4],max_bus_kcl_a=x[5])
    assert dc is not None and final and final['max_bus_kcl_a']<=2e-11
    assert len(roots)==final['selected_pairs']
    return grid,roots,final

def absolute(state):return np.array(state[:250])+np.array(state[250:])

def compare(a,b,refine=False):
    assert a.keys()==b.keys()
    vf=cf=lf=0.;worst={};j7a=[];j7b=[]
    for clock in a:
        x=absolute(a[clock][0]);y=absolute(b[clock][0])
        v=float(np.max(abs(x[:56]-y[:56])/(.020+.002*abs(y[:56]))))
        ids=[di(k) for k in range(118)]
        c=float(np.max(abs(x[ids]-y[ids])/(.002+.001*abs(y[ids]))))
        if clock:
            load=float(np.max(abs(np.array(a[clock][1])-np.array(b[clock][1]))/(20e-9+.002*abs(np.array(b[clock][1])))))
            lf=max(lf,load)
        if v>vf:worst['vco_clock_s']=clock*rf_tick()
        if c>cf:worst['chain_clock_s']=clock*rf_tick()
        vf=max(vf,v);cf=max(cf,c);j7a.append(x[248]);j7b.append(y[248])
    x=np.array(j7a);y=np.array(j7b);error=x-y
    rms=float(np.sqrt(np.mean(error*error))/np.sqrt(np.mean(y*y)))
    peak=float(np.max(abs(error))/np.max(abs(y)))
    dc=float(abs(np.mean(error)))
    result=dict(clocks=len(a),vco_fraction=vf,chain_fraction=cf,load_fraction=lf,
        j7_rms_relative=rms,j7_peak_relative=peak,j7_mean_error_v=dc,
        j7_max_error_v=float(np.max(abs(error))),**worst)
    assert vf<=1 and cf<=1 and lf<=1,result
    assert rms<=(.005 if refine else .01) and peak<=(.015 if refine else .03) and dc<=5e-6,result
    return result

def rf_tick():return 125e-9/65536

def audit(native):
    r=json.loads((ROOT/native).read_text(encoding='utf8'));assert r['passed']
    n=Original();n.y=matrix(0);grids=[];profiles=[]
    for p in r['profiles']:
        path=ROOT/r['output_directory']/f"profile-{p['maximum_half_ticks']}.stdout"
        g,roots,final=trace(path);assert final['ticks']==r['duration_us']*524288 and len(g)==r['duration_us']//125+1
        current=g[0][0];f,_,j,_=assemble(n,current,current,0.);forcing=-f[43]
        f[43]=float(absolute(current)[43]);j[43,:]=0.;j[43,43]=1.
        checks=[gate(f,j,True)]
        for x in roots:
            h,key=x[:2];old,da,db,a,b=[x[2+i*500:2+(i+1)*500] for i in range(5)]
            fa,qa,ja,ma=assemble(n,old,a,key,h);fb,qb,jb,mb=assemble(n,old,b,key,h)
            rr=np.concatenate([fa+B[0,0]*qa+B[0,1]*qb,fb+B[1,0]*qa+B[1,1]*qb])
            jj=np.block([[ja+B[0,0]*ma,B[0,1]*mb],[B[1,0]*ma,jb+B[1,1]*mb]])
            checks.append(gate(rr,jj));assert abs(x[-1])<=2e-11
        profiles.append(dict(maximum_half_ticks=p['maximum_half_ticks'],original_checks=checks,original_rows=251+502*len(roots),**final));grids.append(g)
    refine=compare(grids[0],grids[1],True)
    strict=[]
    baseline=json.loads((ROOT/'evidence/voice_sparse_native01.json').read_text(encoding='utf8'))
    for g in grids:
        bg,_,_=trace(ROOT/baseline['output_directory']/'profile-524288.stdout')
        # Long hold shares only the prefix before the 6-ms release event.
        limit=24000 if r['gate_end_us']==6000 else 6000
        ga={k:v for k,v in g.items() if k<=limit*524288};gb={k:v for k,v in bg.items() if k<=limit*524288}
        strict.append(compare(ga,gb))
    return dict(profiles=profiles,original_rows=sum(p['original_rows'] for p in profiles),refinement=refine,strict_reference=strict,
        strict_reference_duration_s=(.024 if r['gate_end_us']==6000 else .006),
        full_spatial_circuit=True,independent_original_roots=False,physical_fidelity=False,real_time=False)

def main():
    native=sys.argv[1];k=1
    while (ROOT/f'evidence/observed_note_audit{k:02d}.json').exists():k+=1
    names=['tools/audit_observed_note.py','docs/VOZ_NOTA_OBSERVABLE_PROTOCOLO.md',native,'evidence/voice_sparse_native01.json','tools/audit_voice_sparse.py','tools/dual_chain_reference.py','tools/audit_dual_chain_star.py','tools/vco1_increment_circuit.py','tools/vco1_increment_devices.py']
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in names},native=native)
    start=time.monotonic()
    try:
        with localcontext() as ctx:ctx.prec=100;r.update(audit(native))
        r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['source_base64']=base64.b64encode((ROOT/'tools/audit_observed_note.py').read_bytes()).decode()
        try:
            with localcontext() as ctx:ctx.prec=100;audit(native)
            r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    r['wall_s']=time.monotonic()-start
    record=json.loads((ROOT/native).read_text(encoding='utf8'));old=json.loads((ROOT/'evidence/voice_sparse_native01.json').read_text(encoding='utf8'))
    r['private_used_sha256']={**record['private_sha256'],**{n:h for n,h in old['private_sha256'].items() if n.endswith('.stdout')}}
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    write(ROOT/f'evidence/observed_note_audit{k:02d}.json',r)
    print('OBSERVED_VOICE_AUDIT',r['passed'],r.get('refinement'),r.get('strict_reference'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
