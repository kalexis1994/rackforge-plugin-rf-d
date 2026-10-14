"""Independent resistor-star oracle and admitted continuous voice observations."""
import base64,gzip,json,math,os,subprocess,traceback
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
COMPILER='C:/Users/kalex/.rustup/toolchains/stable-x86_64-pc-windows-gnu/bin/rustc.exe'

def star(alpha,v):
    source,ground,bus=v
    if alpha==0:
        cursor=ground;i=(source-ground)/25000.;b=(bus-ground)/33000.
        return [i,-i-b,b],cursor
    if alpha==1:
        cursor=source;g=(ground-source)/25000.;b=(bus-source)/33000.
        return [-g-b,g,b],cursor
    upper=25000.*(1.-alpha);lower=25000.*alpha
    cursor=(source/upper+ground/lower+bus/33000.)/(1./upper+1./lower+1./33000.)
    return [(source-cursor)/upper,(ground-cursor)/lower,(bus-cursor)/33000.],cursor

def main():
    out=ROOT/'evidence/vco_panel_port01.json';assert not out.exists()
    work=ROOT/'tmp/lab-current';work.mkdir(exist_ok=True)
    # A populated shared work area requires explicit retirement first.
    assert not list(work.iterdir())
    names=['tools/check_vco_panel_port.py','tools/vco_panel_port_probe.rs','crates/rf-d-circuit/src/vco_panel_port.rs','docs/VCO_PUERTO_PANEL_PROTOCOLO.md','evidence/observed_note_tests01.json']
    r=dict(passed=False,source_sha256={n:sha(ROOT/n) for n in names},compiler_sha256=sha(Path(COMPILER)),temporary_area='tmp/lab-current',new_cargo_cache=False,physical_fidelity=False,real_time=False)
    assert r['compiler_sha256']=='fd6232f90a981e28472ce6900232946a1f1bcad8ec8270cd5ae6a3a357208b98'
    cases=[];full=[];private={}
    for alpha in [0.,.001,.01,.1,.25,.5,.75,.99,.999,1.]:
        for v in [[-10.,0.,0.],[-5.,0.,1.],[5.,0.,-2.],[15.,10.,8.],[-15.,-10.,-8.],[39.,39.,38.],[-39.,38.,0.]]:cases.append((alpha,v))
    native=json.loads((ROOT/'evidence/observed_note_native01.json').read_text(encoding='utf8'))
    for maximum in [16777216,8388608]:
        path=ROOT/native['output_directory']/f'profile-{maximum}.stdout.gz';private[path.relative_to(ROOT).as_posix()]=sha(path)
        for line in gzip.decompress(path.read_bytes()).decode('utf8').splitlines():
            tag,*tokens=line.split(',');x=list(map(float,tokens))
            if tag=='DC':state=x[4:]
            elif tag=='GRID':state=x[1:501]
            else:continue
            v=lambda k:state[k]+state[250+k]
            cases.append((.5,[v(46),0.,v(12)]));full.append((len(cases)-1,v(39),(v(12)-v(39))/33000.))
    ordinary=70;assert len(full)==1602
    fd=[]
    for alpha,v in cases[:ordinary]:
        pairs=[]
        for k in range(3):
            ids=[]
            for sign in [1.,-1.]:
                trial=list(v);trial[k]+=sign*1e-6;ids.append(len(cases));cases.append((alpha,trial))
            pairs.append(ids)
        fd.append(pairs)
    invalid=[[math.nan,0.,0.,0.],[-.1,0.,0.,0.],[1.1,0.,0.,0.],[math.inf,0.,0.,0.],[.5,math.nan,0.,0.],[.5,0.,math.inf,0.],[.5,0.,0.,41.]]
    text=''.join(','.join(format(v,'.17g') for v in [alpha,*x])+'\n' for alpha,x in cases)+''.join(','.join(str(v) for v in x)+'\n' for x in invalid)
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols',str(ROOT/'tools/vco_panel_port_probe.rs'),'-o',str(work/'probe.exe')]
    phase='compile'
    try:
        p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120)
        (work/'compile.stdout').write_bytes(p.stdout);(work/'compile.stderr').write_bytes(p.stderr);r['compile_exit_code']=p.returncode
        assert p.returncode==0,p.stderr.decode('utf8',errors='replace')
        phase='probe';command=[str(work/'probe.exe')]
        p=subprocess.run(command,cwd=ROOT,env=env,input=text.encode(),capture_output=True,timeout=60)
        (work/'probe.stdout').write_bytes(p.stdout);(work/'probe.stderr').write_bytes(p.stderr)
        assert p.returncode==0,p.stderr.decode('utf8',errors='replace')
        lines=p.stdout.decode().splitlines();assert len(lines)==len(cases)+len(invalid) and all(v=='REJECT' for v in lines[len(cases):])
        values=[list(map(float,v.split(','))) for v in lines[:len(cases)]]
        current=cursor=jacobian=power=kcl=derivative=full_cursor=full_current=0.
        for (alpha,v),z in zip(cases[:ordinary],values[:ordinary]):
            i,w=star(alpha,v);zero=star(alpha,[0.,0.,0.])[0]
            for k in range(3):current=max(current,abs(z[k]-i[k])/(2e-15+2e-12*abs(i[k])))
            cursor=max(cursor,abs(z[12]-w)/(2e-12+2e-12*abs(w)))
            for column in range(3):
                basis=[0.,0.,0.];basis[column]=1.;expected=star(alpha,basis)[0]
                for row in range(3):
                    y=expected[row]-zero[row];jacobian=max(jacobian,abs(z[3+3*row+column]-y)/(2e-16+2e-12*abs(y)))
            kcl=max(kcl,abs(sum(z[:3]))/2e-15)
            delivered=sum(a*b for a,b in zip(v,z[:3]));assert z[15]>=0
            power=max(power,abs(delivered-z[15])/(2e-15+2e-12*abs(z[15])))
        for row,pairs in enumerate(fd):
            for column,(a,b) in enumerate(pairs):
                for k in range(3):
                    measured=(values[a][k]-values[b][k])/2e-6;y=values[row][3+3*k+column]
                    derivative=max(derivative,abs(measured-y)/(2e-12+2e-7*abs(y)))
        for k,w,i in full:
            full_cursor=max(full_cursor,abs(values[k][12]-w)/(2e-12+2e-12*abs(w)))
            full_current=max(full_current,abs(values[k][2]-i)/(2e-15+2e-12*abs(i)))
        fractions=dict(current=current,cursor=cursor,jacobian=jacobian,power=power,kcl=kcl,finite_difference=derivative,full_voice_cursor=full_cursor,full_voice_bus_current=full_current)
        assert max(fractions.values())<=1,fractions
        r.update(passed=True,star_cases=ordinary,fd_columns=ordinary*3,full_voice_observations=len(full),invalid_rejections=len(invalid),gate_fractions=fractions,all_terminal_currents=True,physical_memory_removed=False,spatial_cursor_eliminated=True,oscillator_waveform_changed=False,private_used_sha256=private)
    except Exception:
        r['failure']=traceback.format_exc();r['failed_phase']=phase
        r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
        replay=subprocess.run(command,cwd=ROOT,env=env,input=text.encode() if phase=='probe' else None,capture_output=True,timeout=120)
        r['unchanged_replay_exit_code']=replay.returncode;r['unchanged_replay_stdout_sha256']=__import__('hashlib').sha256(replay.stdout).hexdigest()
        r['unchanged_replay_stderr_base64']=base64.b64encode(replay.stderr).decode()
        # Keep a bounded full probe fixture, including rejected input text.
        r['failed_probe_input']=text;r['failed_probe_stdout']=p.stdout.decode('utf8',errors='replace')
    assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items())
    r['temporary_files_sha256']={p.name:sha(p) for p in work.iterdir() if p.is_file()}
    # Exact explicit files in this new work area; never recursively delete.
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());write(out,r)
    print('VCO_PANEL_PORT',r['passed'],r.get('gate_fractions'),r.get('failure',''))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
