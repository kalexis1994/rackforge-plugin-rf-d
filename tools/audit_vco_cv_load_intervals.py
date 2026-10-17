"""Independent roots at actually accepted native intervals, without another trajectory."""
import json,traceback,hashlib,struct
from decimal import Decimal,localcontext
from prepare_dual_chain import ROOT,write,sha
from affine_evidence import Sources
from check_hybrid_voice import unpack
from vco_cv_load_analysis import oracle,config,TICK
def calculate(r):
    out=[];cache={};native_bytes={}
    with localcontext() as ctx:
        ctx.prec=100
        for profile in r['profiles']:
            for line in unpack(profile['stderr']).decode().splitlines():
                z=line.split(',')
                if z[0]!='INTERVAL':continue
                start,ticks=map(int,z[1:3]);v=list(map(float,z[3:]));assert len(v)==804
                digest=hashlib.sha256(struct.pack('<11dQ268d',*config(5),ticks,*v[:268])).hexdigest();encoded=struct.pack('<536d',*v[268:]);repeated=digest in cache
                if repeated:assert encoded==native_bytes[digest]
                states=[[Decimal.from_float(a)+Decimal.from_float(b) for a,b in zip(v[k:k+134],v[k+134:k+268])] for k in [0,268,536]];old=states[0]
                if not repeated:cache[digest]=oracle.solve(old,ticks*TICK,config(5));native_bytes[digest]=encoded
                p=cache[digest];rows=[]
                for native,key in zip(states[1:],['stage','endpoint']):
                    err=[abs(a-b) for a,b in zip(native,p[key])];nv=float(max(err[:98]));na=float(max(err[98:]));assert nv<=2e-7 and na<=2e-10,(nv,na);rows.append(dict(stage=key,node_error_v=nv,branch_error_a=na,independent_decimal=[str(v) for v in p[key]]))
                rr,j,g=oracle.system([p['stage'],p['endpoint']],old,ticks*TICK,config(5));kcl=max(float(abs(rr[i*134+k])) for i in range(2) for k in range(98));constraint=max(float(abs(rr[i*134+k])) for i in range(2) for k in range(98,134));balance=max(float(abs(sum(rr[i*134:i*134+98])+g[i])) for i in range(2));assert kcl<=2e-14 and constraint<=2e-12 and balance<=1e-11
                out.append(dict(profile=profile['maximum_half_ticks'],start_ticks=start,half_ticks=ticks,problem_sha256=digest,independent_problem_reused=repeated,native_duplicate_bitwise_identical=True if repeated else None,roots=rows,kcl_a=kcl,constraint_v=constraint,ground_balance_a=balance))
    assert len(out)==4;return out
def main():
    name='evidence/vco_cv_load_native05.json';out=ROOT/'evidence/vco_cv_load_intervals01.json';assert not out.exists();s=Sources(['tools/audit_vco_cv_load_intervals.py','tools/vco1_radau_reference.py','tools/vco1_increment_circuit.py','tools/vco1_increment_devices.py','tools/vco_cv_load_analysis.py']);r=json.loads((ROOT/name).read_text(encoding='utf8'));assert r['passed'];q=dict(passed=False,**s.fields(),native=name,native_sha256=sha(ROOT/name),new_trajectories=0)
    try:q.update(intervals=calculate(r),passed=True)
    except Exception:
        q['failure']=traceback.format_exc()
        try:calculate(r);q['unchanged_replay']='unexpected pass'
        except Exception:q['unchanged_replay']=traceback.format_exc()
    s.unchanged();write(out,q);print('VCO_ACTUAL_INTERVALS',q['passed'],len(q.get('intervals',[])),q.get('failure',''),flush=True)
    if not q['passed']:raise SystemExit(1)
if __name__=='__main__':main()
