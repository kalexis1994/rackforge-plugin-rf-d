"""Collect every linear/port observation after preserved gate rejection; never admit."""
import json,os,subprocess,time,base64,re
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
from run_dynamic_schur_scaled_diagnostic import PROXY,MAIN
from prepare_dynamic_schur import maps

def main():
    work=ROOT/'references-local/dynamic-schur-observations01';require(not work.exists(),'exclusive observations');work.mkdir()
    names=['tools/observe_dynamic_schur_diagnostic.py','tools/run_dynamic_schur_scaled_diagnostic.py','tools/dynamic_schur_fast_solver.rs','tools/joint_dynamic_schur_fast_kernel.rs','tools/dynamic_schur_fast_bench.rs','docs/SCHUR_DINAMICO_ESCALA_RESIDUAL.md','docs/SCHUR_DINAMICO_OBSERVACIONES.md']
    sources={n:sha(ROOT/n) for n in names};packet='references-local/newton-reuse-inputs01/pairs.bin';lib='references-local/joint-startup01/librf_d_circuit.rlib';private={n:sha(ROOT/n) for n in [packet,lib]}
    compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler')
    proxy=work/'proxy.rs';s=PROXY.replace('SOLVER_PATH',(ROOT/'tools/dynamic_schur_fast_solver.rs').as_posix())
    # Collect rejected values without changing the solver; the receipt retains failed admission.
    s=s.replace('assert!(a.1<=1e-11&&c.1<=1e-11,"scaled backward {a:?} {c:?}");','')
    proxy.write_text(s,encoding='utf8',newline='\n')
    s=(ROOT/'tools/joint_dynamic_schur_fast_kernel.rs').read_text(encoding='utf8')
    for old,new in [('dynamic_schur_fast_solver.rs',proxy.as_posix()),('latch_charge_driver.rs',(ROOT/'tools/latch_charge_driver.rs').as_posix()),('contour_closed_driver.rs',(ROOT/'tools/contour_closed_driver.rs').as_posix())]:s=s.replace('path="'+old+'"','path="'+new+'"')
    kp=work/'kernel.rs';kp.write_text(s,encoding='utf8',newline='\n')
    s=(ROOT/'tools/dynamic_schur_fast_bench.rs').read_text(encoding='utf8').split('fn main(){')[0]
    for old,new in [('joint_lu_extent_kernel.rs',(ROOT/'tools/joint_lu_extent_kernel.rs').as_posix()),('joint_dynamic_schur_fast_kernel.rs',kp.as_posix()),('../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',(ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs').as_posix())]:s=s.replace(old,new)
    _,_,_,raw=maps();node=lambda k:'usize::MAX' if k==134 else str(k if k<108 else k-1);maptext='['+','.join('['+','.join(node(k) for k in row)+']' for row in raw)+']'
    p=work/'observations.rs';p.write_text(s+MAIN.replace('MAPS',maptext),encoding='utf8',newline='\n');exe=work/'observe.exe'
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[]
    def run(cmd,limit):
        t=time.perf_counter();q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);out=dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-t);commands.append(out);return out
    q=run([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(p),'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)],120);require(q['exit_code']==0,'observation compile')
    a=run([str(exe),str(ROOT/packet)],600);b=run(a['command'],600);require(a['exit_code']==b['exit_code']==0 and (a['stdout'],a['stderr'])==(b['stdout'],b['stderr']),'identical complete observations')
    linear=[list(map(float,x.split(',')[1:])) for x in a['stdout'].splitlines() if x.startswith('LINEAR,')];ports=[list(map(float,x.split(',')[1:])) for x in a['stdout'].splitlines() if x.startswith('PORT,')]
    require(len(ports)==336 and 'DIAGNOSTIC_PASSED,84,336,1680,2016' in a['stdout'],'complete memory and current observations')
    metrics=dict(linear_solves=len(linear),correction_max_ratio=max(x[0] for x in linear),schur_pure_max=max(x[1] for x in linear),schur_mixed_max=max(x[2] for x in linear),schur_pure_failed_rows=sum(int(x[3]) for x in linear),schur_mixed_failed_solves=sum(x[2]>1e-11 for x in linear),reference_pure_max=max(x[5] for x in linear),reference_mixed_max=max(x[6] for x in linear),reference_pure_failed_rows=sum(int(x[7]) for x in linear),reference_mixed_failed_solves=sum(x[6]>1e-11 for x in linear),memory_max_ratio=max(x[2] for x in ports),port_current_max_a=max(x[3] for x in ports))
    require(metrics['correction_max_ratio']<=1 and metrics['memory_max_ratio']<=1 and metrics['port_current_max_a']<=2e-11,'corrections, storage and ports')
    require(metrics['schur_mixed_failed_solves']>0 and metrics['reference_mixed_failed_solves']>0,'rejection remains visible')
    require(sources=={n:sha(ROOT/n) for n in names} and private=={n:sha(ROOT/n) for n in private},'stable sources and inputs')
    write('evidence/voice_dynamic_schur_observations01.json',dict(passed=False,collection_passed=True,full_trajectory_admitted=False,physical_fidelity=False,real_time=False,numerical_gates_changed=False,rejected_gate='scaled backward <=1e-11, retained from diagnostic02',identical_replay=True,metrics=metrics,roots=84,opamp_candidate_observations=336,memory_observations=1680,terminal_and_ground_currents=2016,source_sha256=sources,private_used_sha256=private,commands=commands,outputs=[dict(path=x.relative_to(ROOT).as_posix(),sha256=sha(x),bytes=x.stat().st_size) for x in work.iterdir() if x.is_file()]))
    print('COMPLETE_SCHUR_OBSERVATIONS_UNADMITTED',json.dumps(metrics))

if __name__=='__main__':main()
