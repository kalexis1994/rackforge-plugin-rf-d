"""Own DC publication guards and explicit initial capacitor/junction ledger."""
import json,os,struct,subprocess,traceback
from decimal import localcontext
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from run_chain_startup import OWN as BASE,parse
from check_vco_phase import COMPILER,LIB
from check_hybrid_voice import packed,unpack
from c5_trigger_reference import CAPS as CONTOUR,LATCH,junction,D
from chain_charge_reference import CAPS as AUDIO
from dual_chain_reference import ci
def ledger(values):
    x=[D(values[k])+D(values[118+k]) for k in range(118)];linear=[];nonlinear=[]
    branches=[(a,b if b<54 else None,c) for a,b,c in CONTOUR]+[(ci(a),ci(b) if isinstance(b,int) else ci(66) if b=='BUS' else None,c) for a,b,c in AUDIO if a!=62]+[(ci(67),ci(7),1e-5)]
    for a,b,c in branches:
        v=x[a]-(x[b] if b is not None else D(0));linear.append(dict(positive_node=a,negative_node=b,capacitance_f=c,voltage_v_decimal=str(v),charge_c_decimal=str(D(c)*v)))
    for b,c in LATCH:
        for be,v in[(True,x[b]),(False,x[b]-x[c])]:nonlinear.append(dict(base_node=b,other_node=None if be else c,junction='BE' if be else 'BC',voltage_v_decimal=str(v),charge_c_decimal=str(junction(v,be))))
    assert len(linear)==24 and len(nonlinear)==12;return dict(linear=linear,junctions=nonlinear,zero_charge_reset=False)
def main():
    native='evidence/chain_startup_native02.json';r0=json.loads((ROOT/native).read_text());assert r0['passed'];data=parse(unpack(r0['profiles'][0]['stdout']));x=data['dc'][0]['state'];raw=unpack(r0['profiles'][0]['stdout']);guess=list(map(float,next(s for s in raw.decode().splitlines() if s.startswith('SEED,0,')).split(',')[2:]));assert len(guess)==236
    inp=struct.pack('<472d',*x,*guess);work=ROOT/'tmp/lab-current';assert not list(work.iterdir());sources=Sources(BASE+['tools/check_chain_startup_guards.py','tools/chain_startup_guards.rs','tools/chain_charge_reference.py','tools/dual_chain_reference.py'])
    r=dict(passed=False,native=native,native_sha256=sha(ROOT/native),**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),input=packed(inp),physical_fidelity=False,real_time=False);exe=work/'guards.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);last=None;stdin=None
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(ROOT/'tools/chain_startup_guards.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    try:
        last=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace')
        command=[str(exe)];stdin=inp;last=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=120);assert last.returncode==0,last.stderr.decode(errors='replace');v=list(map(int,last.stdout.decode().strip().split(',')[1:]));assert v==[18,18,0];r['stdout']=packed(last.stdout);r['guards']=dict(rejections=v[0],exact_retries=v[1],heap_allocations=v[2])
        with localcontext() as ctx:ctx.prec=100;r['initial_memories']=ledger(x)
        r['passed']=True
    except Exception:
        r.update(failure=traceback.format_exc(),failed_command=command)
        if last is not None:r['failed_process']=dict(exit_code=last.returncode,stdout=packed(last.stdout),stderr=last.stderr.decode(errors='replace'))
        replay=subprocess.run(command,cwd=ROOT,env=env,input=stdin,capture_output=True,timeout=120);r['unchanged_replay']=dict(exit_code=replay.returncode,stdout=packed(replay.stdout),stderr=replay.stderr.decode(errors='replace'))
    sources.unchanged()
    for p in list(work.iterdir()):assert p.is_file() and p.resolve().parent==work.resolve();p.unlink()
    r['temporary_area_empty']=not list(work.iterdir());k=1
    while (ROOT/f'evidence/chain_startup_guards{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/chain_startup_guards{k:02d}.json',r);print('CHAIN_STARTUP_GUARDS',r['passed'],r.get('guards'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
