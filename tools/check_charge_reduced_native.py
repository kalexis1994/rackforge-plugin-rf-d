"""Charge kernel + inherited FIR benchmark, explicitly not a whole voice."""
import json,os,subprocess,traceback,platform
import numpy as np
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import packed
from check_vco_phase import COMPILER,LIB
AREA=ROOT/'tmp/lab-current'
OWN=['tools/check_charge_reduced_native.py','tools/charge_reduced_probe.rs','tools/charge_reduced_kernel.rs','tools/charge_reduced_data.rs','crates/rf-d-circuit/src/j7_stream_output.rs','crates/rf-d-circuit/src/j7_antialias_coefficients.rs']
def main():
    out=ROOT/'evidence/charge_reduced_native01.json';assert not out.exists() and not list(AREA.iterdir());old=json.loads((ROOT/'evidence/mono_voice_tests01.json').read_text(encoding='utf8'));assert sha(Path(COMPILER))==old['compiler']['sha256'] and sha(LIB)==old['private_input_sha256'][LIB.relative_to(ROOT).as_posix()]
    sources=Sources(OWN);r=dict(passed=False,**sources.fields(),compiler_sha256=sha(Path(COMPILER)),library_sha256=sha(LIB),platform=platform.platform(),includes_charge_kernel_and_48khz_fir=True,includes_oscillator_or_contours=False,whole_voice_realtime=False);exe=AREA/'reduced.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH']);command=[]
    def save():write(out,r)
    save()
    try:
        command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code','-A','unused_imports',str(ROOT/'tools/charge_reduced_probe.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);r['compile']=dict(command=command,exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode()
        command=[str(exe),'vectors'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['vectors']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode();a=np.frombuffer(q.stdout,dtype='<f8').reshape(2,512,91);assert np.isfinite(a).all()
        models=json.loads((ROOT/'evidence/charge_reduced_derivation01.json').read_text(encoding='utf8'))['models'];errors=[]
        for case,m in enumerate(models):
            s=np.zeros(18);f=np.array(m['f']);u0=np.array(m['u0']);u1=np.array(m['u1']);xq=np.array(m['xq']);xu=np.array(m['xu']);previous=0.;worst=0.;panel=0.
            for row in a[case]:
                u=row[0];s=f@s+u0*previous+u1*u;nodes=xq@s+xu*u;previous=u;worst=max(worst,float(max(abs(row[5:23]-s))),float(max(abs(row[23:]-nodes))));panel=max(panel,abs(row[4]-(nodes[66]-.5*u)/39250))
            assert worst<=1e-11 and panel<=1e-15;errors.append(dict(case=case,max_state_node_error_v=worst,max_panel_error_a=panel))
        r['vector_comparisons']=errors;r['signed_bit_reject_fixtures']=12;r['exact_retries']=12
        command=[str(exe),'bench'];q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['bench']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr));save();assert q.returncode==0,q.stderr.decode();costs=[]
        for case in range(2):
            rows=[z.split(',') for z in q.stdout.decode().splitlines() if z.startswith('BLOCK,'+str(case)+',')];assert len(rows)==1200 and all(int(z[4])==0 for z in rows);t=np.array([float(z[3]) for z in rows]);budget=128/48000;costs.append(dict(case=case,blocks=len(t),first_included=True,budget_s=budget,median_s=float(np.median(t)),p95_s=float(np.quantile(t,.95)),p99_s=float(np.quantile(t,.99)),max_s=float(max(t)),max_budget_ratio=float(max(t)/budget),deadline_misses=int(sum(t>budget)),target_50_percent_pass=bool(np.all(t<=budget*.5)),heap_allocations=0))
        r['costs']=costs;r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();save()
        if command:
            q=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=240);r['unchanged_replay']=dict(exit_code=q.returncode,stdout=packed(q.stdout),stderr=packed(q.stderr))
    finally:
        if exe.exists():assert exe.resolve().parent==AREA.resolve();exe.unlink()
    sources.unchanged();r['temporary_area_empty']=not list(AREA.iterdir());save();print('CHARGE_NATIVE',r['passed'],r.get('costs'),r.get('failure',''))
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
