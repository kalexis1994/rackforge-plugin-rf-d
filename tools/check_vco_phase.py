"""Nominal source/port contrast with reserved loaded observations; bounded work."""
import base64,json,os,subprocess,traceback
import numpy as np
from prepare_dual_chain import ROOT,sha,write
from prepare_vco_phase import voice,crossings
from render_vco1_circuit import coefficients
COMPILER='C:/Users/kalex/.rustup/toolchains/stable-x86_64-pc-windows-gnu/bin/rustc.exe'
LIB=ROOT/'references-local/voice-assembly-public01/librf_d_circuit.rlib'

def star(alpha,v):
    # Original three internal nodes, with explicit end contacts.
    drive,tri,ground,bus=v
    y=np.zeros((3,3));rhs=np.zeros(3)
    def branch(a,b,r):
        g=1/r;y[a,a]+=g
        if isinstance(b,int):y[a,b]-=g;y[b,b]+=g;y[b,a]-=g
        else:rhs[a]+=g*b
    branch(0,float(ground),4700.);branch(0,float(drive),4300.);branch(0,1,47000.);branch(1,float(tri),10000.);branch(2,float(bus),33000.)
    if alpha in [0.,1.]:
        if alpha==0:
            branch(0,float(ground),25000.);y[2,:]=0.;y[2,2]=1.;rhs[2]=ground
        else:
            branch(2,float(ground),25000.);y[2,0]-=1.;y[2,2]+=1.
            # Short wiper=saw; add row2 to row0 then replace row2.
            y[0]+=y[2]-np.array([-1.,0.,1.]);rhs[0]+=rhs[2]
            y[2,:]=[-1.,0.,1.];rhs[2]=0.
    else:branch(0,2,25000.*(1.-alpha));branch(2,float(ground),25000.*alpha)
    s,t,w=np.linalg.solve(y,rhs)
    currents=[(drive-s)/4300.,(tri-t)/10000.,(ground-s)/4700.,(bus-w)/33000.]
    currents[2]+= (ground-w)/25000. if alpha==1 else (ground-s)/25000. if alpha==0 else (ground-w)/(25000.*alpha)
    if alpha==0:currents[2]+=(ground-bus)/33000.
    return np.array(currents),np.array([s,t,w])

def phase_projection(time,value,frequency,epoch):
    p=((time-epoch)*frequency)%1;order=np.argsort(p);p=p[order];value=value[order]
    assert np.all(np.diff(p)>0)
    left=(value[-1]*p[0]+value[0]*(1.-p[-1]))/(p[0]+1.-p[-1])
    phase=np.r_[0.,p,1.];values=np.r_[left,value,left]
    return coefficients(phase,values,8),float(max(np.diff(phase)))

def execute():
    work=ROOT/'tmp/lab-current';work.mkdir(exist_ok=True);assert not list(work.iterdir())
    names=['tools/check_vco_phase.py','tools/vco_phase_probe.rs','tools/assembly_vco_helper.rs','tools/prepare_vco_phase.py','crates/rf-d-circuit/src/vco_nominal_phase.rs','crates/rf-d-circuit/src/vco_output_port.rs','crates/rf-d-circuit/src/vco_panel_port.rs','crates/rf-d-circuit/src/vco_phase_profile.rs','evidence/vco_phase_profile01.json','docs/VCO_FASE_NOMINAL_PROTOCOLO.md']
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in names},compiler_sha256=sha(__import__('pathlib').Path(COMPILER)),library_sha256=sha(LIB),new_private_sound_inputs=0,physical_fidelity=False,full_voice=False,real_time=False)
    assert r['library_sha256']=='9dbada9779f30c4972b057befe092524d091d3444ea777206b618d701236385d'
    profile=json.loads((ROOT/'evidence/vco_phase_profile01.json').read_text(encoding='utf8'));freq=profile['frequency_hz'];epoch=profile['epoch_s']
    inputs=[];tasks=[];grids=[];private={};port_cases=[];fd=[]
    for alpha in [0.,.01,.5,.99,1.]:
        for v in [[4.,-1.,0.,.8],[-4.,1.,0.,-.8],[4.,6.,10.,9.],[-15.,-16.,-10.,-9.]]:
            port_cases.append((alpha,v));inputs.append('PORT,'+','.join(map(str,[alpha,*v])))
    for alpha,v in port_cases:
        columns=[]
        for k in range(4):
            ids=[]
            for sign in [1,-1]:
                w=list(v);w[k]+=sign*1e-6;ids.append(len(inputs));inputs.append('PORT,'+','.join(map(str,[alpha,*w])))
            columns.append(ids)
        fd.append(columns)
    for maximum in [16777216,8388608]:
        x,path=voice(maximum);private[path.relative_to(ROOT).as_posix()]=sha(path);reserved=x[(x[:,0]>=.04)&(x[:,0]<=.1)]
        begin=len(inputs)
        for row in reserved:inputs.append(f'TIME,{row[0]:.17g},{row[13]:.17g}')
        tasks.append((maximum,begin,reserved));grids.append(x)
    tangent=[]
    # Actual high/low snapshots, without recomputing the discarded states.
    import gzip
    native=json.loads((ROOT/'evidence/observed_note_native01.json').read_text(encoding='utf8'));path=ROOT/native['output_directory']/'profile-8388608.stdout.gz'
    selected={int(round((.04+k*.0025)/ (125e-9/65536))) for k in range(24)}
    for line in gzip.decompress(path.read_bytes()).decode('utf8').splitlines():
        z=line.split(',')
        if z[0]=='GRID' and int(z[1]) in selected:
            for h in [1e-6,8e-6,32e-6]:
                tangent.append((len(inputs),int(z[1])*(125e-9/65536),h));inputs.append('TANGENT,'+format(h,'.17g')+','+','.join(z[2:502]))
    assert len(tangent)==72
    inputs.append('BENCH');text='\n'.join(inputs)+'\n'
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code',str(ROOT/'tools/vco_phase_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(work/'probe.exe')]
    phase='compile'
    try:
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert p.returncode==0,p.stderr.decode()
        phase='probe';command=[str(work/'probe.exe')];p=subprocess.run(command,cwd=ROOT,env=env,input=text.encode(),capture_output=True,timeout=120)
        assert p.returncode==0,p.stderr.decode();lines=p.stdout.decode().splitlines()
        assert len(lines)==len(inputs)+3;assert lines[-1]=='DOMAIN,7,exact_retry=true'
        rows=[list(map(float,s.split(',')[1:])) for s in lines[:-4]]
        port_fraction=voltage_fraction=fd_fraction=kcl=power=0.
        for index,(alpha,v) in enumerate(port_cases):
            expected,internal=star(alpha,v);z=np.array(rows[index]);actual=z[:4]
            port_fraction=max(port_fraction,float(max(abs(actual-expected)/(2e-15+2e-12*abs(expected)))))
            voltage_fraction=max(voltage_fraction,float(max(abs(z[20:23]-internal)/(2e-12+2e-12*abs(internal)))))
            kcl=max(kcl,float(abs(sum(actual))/2e-15));power=max(power,abs(sum(np.array(v)*actual)-z[23])/(2e-15+2e-12*abs(z[23])))
            for column,(a,b) in enumerate(fd[index]):
                measured=(np.array(rows[a][:4])-np.array(rows[b][:4]))/2e-6;y=z[4:20].reshape(4,4)[:,column]
                fd_fraction=max(fd_fraction,float(max(abs(measured-y)/(2e-12+2e-7*abs(y)))))
        assert max(port_fraction,voltage_fraction,fd_fraction,kcl,power)<=1,(port_fraction,voltage_fraction,fd_fraction,kcl,power)
        shape=[];epochs=[]
        for maximum,begin,reserved in tasks:
            predicted=np.array(rows[begin:begin+len(reserved)])
            # Compare deembedded saw at BUS=0 and triangle; original resistor map.
            g=1/4700+1/4300+1/57000+1/25000+.25/39250
            y=(reserved[:,49]/4300+reserved[:,55]/57000)/g
            predicted_saw=predicted[:,20]-.5*reserved[:,13]/(39250*g)
            # Reconstruct triangle driver from its terminal current and the tap.
            predicted_tri=predicted[:,21]+10000.*predicted[:,1]
            metrics=[]
            for actual,approx in [(y,predicted_saw),(reserved[:,55],predicted_tri)]:
                a,gap=phase_projection(reserved[:,0],actual,freq,epoch);b,_=phase_projection(reserved[:,0],approx,freq,epoch)
                error=float(np.linalg.norm(a[1:]-b[1:])/np.linalg.norm(a[1:]));dc=float(abs(a[0]-b[0]))
                metrics.append(dict(ac_harmonics_1_to_8_relative=error,dc_error_v=dc,max_phase_gap=gap,raw_rms_error_v=float(np.sqrt(np.mean((actual-approx)**2))),raw_peak_error_v=float(max(abs(actual-approx)))))
            assert all(z['ac_harmonics_1_to_8_relative']<=.02 and z['dc_error_v']<=.005 for z in metrics),metrics
            c=crossings(grids[len(shape)]);idx=np.arange(len(c));take=c>=.04;expected=epoch+profile['source_cycle_down_phase']/freq+idx[take]/freq
            error=float(max(abs((c[take]-expected)*freq)));cents=float(abs(1200*np.log2(1/np.mean(np.diff(c[take]))/freq)))
            assert error<=1e-4 and cents<=.01,(error,cents)
            shape.append(dict(maximum_half_ticks=maximum,observations=len(reserved),signals=metrics));epochs.append(dict(maximum_half_ticks=maximum,reserved_crossings=int(sum(take)),max_phase_error_cycles=error,frequency_error_cents=cents))
        nominal_y=rows[8][19];response=[]
        for index,t,h in tangent:
            y,backward=rows[index];error=abs(y-nominal_y)/abs(y)
            response.append(dict(time_s=t,h_s=h,native_admittance_s=y,reduced_admittance_s=nominal_y,relative_error=error,backward=backward))
        assert max(x['relative_error'] for x in response)<=.02 and max(x['backward'] for x in response)<=1e-10,response
        bench=[dict(rate_hz=v[0],elapsed_s=v[1],allocations=int(v[2]),phase_error_cycles=v[3],samples=1000000) for v in [list(map(float,s.split(',')[1:])) for s in lines[-4:-1]]]
        r.update(passed=True,port_cases=20,fd_columns=80,port_fractions=dict(current=port_fraction,voltage=voltage_fraction,fd=fd_fraction,kcl=kcl,power=power),shape=shape,epochs=epochs,local_responses=response,benchmark=bench,atomic_rejections=7,phase_wrap_cases=200,exact_valid_retry=True,private_used_sha256=private,isolated_to_loaded_cents=float(abs(1200*np.log2(freq/profile['source_isolated_frequency_hz']))))
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase,failed_source_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names},failed_probe_input=text,failed_probe_stdout=p.stdout.decode('utf8',errors='replace'),failed_probe_stderr=p.stderr.decode('utf8',errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,input=text.encode() if phase=='probe' else None,capture_output=True,timeout=120)
        r.update(unchanged_replay_exit_code=replay.returncode,unchanged_replay_stdout=replay.stdout.decode('utf8',errors='replace'),unchanged_replay_stderr=replay.stderr.decode('utf8',errors='replace'))
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    for item in list(work.iterdir()):assert item.is_file() and item.resolve().parent==work.resolve();item.unlink()
    r['temporary_area_empty']=not list(work.iterdir());return r
def main():
    k=1
    while (ROOT/f'evidence/vco_phase_native{k:02d}.json').exists():k+=1
    r=execute();write(ROOT/f'evidence/vco_phase_native{k:02d}.json',r)
    print('VCO_PHASE',r['passed'],r.get('shape'),r.get('benchmark'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
