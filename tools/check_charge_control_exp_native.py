"""Implementation agreement and cost do not promote the rejected cutoff scene."""
import json,os,subprocess,traceback,platform
import numpy as np
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER,LIB
from check_charge_control import Y
from prepare_charge_control_exp import simulate
AREA=ROOT/'tmp/lab-current'
OWN=['tools/check_charge_control_exp_native.py','tools/charge_control_exp_probe.rs','tools/charge_control_exp_kernel.rs','tools/charge_control_exp_data.rs','crates/rf-d-circuit/src/j7_stream_output.rs']
def main():
    out=ROOT/'evidence/charge_control_exp_rust01.json';assert not out.exists() and not list(AREA.iterdir());old=json.loads((ROOT/'evidence/charge_reduced_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()];sources=Sources(OWN);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),platform=platform.platform(),dynamic_cutoff_physical_admission=False,whole_voice_rt=False);exe=AREA/'family.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[]
    def save():write(out,r)
    save()
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/charge_control_exp_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(command=command,exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode()
        command=[str(exe),'vectors'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['vectors']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode();a=np.frombuffer(q.stdout,dtype='<f8').reshape(1537,111);assert np.isfinite(a).all();models=json.loads((ROOT/'evidence/charge_control_native01.json').read_text(encoding='utf8'))['models'];reference,switches=simulate(models,a[:,0],a[:,1],1,True);error=float(np.max(abs(reference-a[:,43:])));assert error<=1e-11,error;pan=Y*(reference[:,66]-.5*a[:,1]);panel=float(max(abs(pan-a[:,6])));assert panel<=1e-15;assert np.array_equal(a[:,3:6].view('<u8'),a[:,[43+66,43+6,43+61]].view('<u8'))
        incidence=np.array(models[0]['incidence']);actual=a[:,7:25]+a[:,25:43];cap_error=float(np.max(abs(actual-a[:,43:]@incidence.T)));assert cap_error<=1e-11;r.update(rust_python_node_error_v=error,rust_python_panel_error_a=panel,physical_charge_coordinate_error_v=cap_error,all_published_ports_match_nodes_by_bits=True,signed_bit_reject_fixtures=8,exact_retries=8,conservative_relabel_checks=6,switches=switches)
        command=[str(exe),'bench'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['bench']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode();rows=[s.split(',') for s in q.stdout.decode().splitlines() if s.startswith('BLOCK,')];assert len(rows)==1200 and all(int(z[3])==0 for z in rows);elapsed=np.array([float(z[2]) for z in rows]);budget=128/48000;r['cost']=dict(blocks=1200,first_included=True,budget_s=budget,median_s=float(np.median(elapsed)),p95_s=float(np.quantile(elapsed,.95)),p99_s=float(np.quantile(elapsed,.99)),max_s=float(max(elapsed)),max_budget_ratio=float(max(elapsed)/budget),deadline_misses=int(sum(elapsed>budget)),target_50_percent_pass=bool(np.all(elapsed<=budget*.5)),heap_allocations=0,includes_control_selection_and_compensated_rebasing_and_fir=True,oscillator_contours_and_input_generator_outside=True,benchmark_does_not_validate_rejected_constitutive_model=True);r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();save()
        if command:
            q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['unchanged_replay']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr))
    finally:
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    sources.unchanged();r['temporary_area_empty']=not list(AREA.iterdir());save();print('CONTROL_RUST',r['passed'],r.get('cost'),r.get('failure',''))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
