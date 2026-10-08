"""Check 24 selected stages and step-doubling differences independently.
Native points are declared; physical equations inherited from nodal oracle.
"""
import argparse,json,time,traceback
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha
from check_joint_reference import evaluate,decode,D,N
def cases(receipt):
    lines=receipt['commands'][-1]['stdout'].splitlines();out=[]
    for i,line in enumerate(lines):
        if 'JOINT_ROOT,' in line:
            _,mask,h,res,corr=line[line.index('JOINT_ROOT,'):].split(',')
            assert all(s.startswith('JOINT_STATE,') for s in lines[i+1:i+6])
            out.append((int(mask),float(h),*[decode(s) for s in lines[i+1:i+6]]))
    assert len(out)==12;return out
def check(receipt):
    bank=cases(receipt);results=[evaluate(c) for c in bank];temporal=[]
    for i in range(0,12,3):
        full,mid,end=bank[i:i+3]
        assert full[0]==mid[0]==end[0] and full[1]==2*mid[1] and mid[1]==end[1]
        assert full[2]==mid[2] and mid[-1]==end[2],'common history and chained midpoint'
        ratio=max(abs(a-b)/D(2e-9 if 98<=k<133 else 2e-6) for k,(a,b) in enumerate(zip(full[-1],end[-1])))
        assert ratio<=1,ratio
        temporal.append(dict(other_ports_on=bool(full[0]),full_h_s=full[1],error_ratio_decimal=str(ratio)))
    return results,temporal
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args()
    out=ROOT/f'evidence/voice_joint_engine_reference{a.attempt:02d}.json';assert not out.exists()
    native='evidence/voice_joint_engine_native01.json';receipt=json.loads((ROOT/native).read_text());assert receipt['passed']
    sources=[native,'tools/check_joint_engine.py','tools/check_joint_reference.py','tools/vco1_increment_circuit.py','tools/vco1_increment_devices.py','tools/vco1_native_inventory.py','tools/lm741_port_reference.py','tools/chain_charge_reference.py','tools/circuit66_dc_vectors.py','tools/circuit66_vca_release_probes.py','tools/mixer_on_native_vectors.py','tools/cutoff_j7_vectors.py','docs/VOZ_MOTOR_TEMPORAL_PROTOCOLO.md']
    hashes={n:sha(ROOT/n) for n in sources};report=dict(schema='rf-d/joint-engine-reference/v1',passed=False,source_sha256=hashes,root_checks=[],temporal_checks=[],native_candidate_points_used=True,independent_root_solve=False,new_spice_processes=0)
    start=time.perf_counter()
    try:
        with localcontext() as ctx:
            ctx.prec=100;report['root_checks'],report['temporal_checks']=check(receipt)
        report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_joint_engine.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(receipt)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['wall_s']=time.perf_counter()-start;report['source_sha256_after']={n:sha(ROOT/n) for n in sources};assert hashes==report['source_sha256_after']
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('ENGINE_REFERENCE',report['passed'],'stage_rows',sum(c['rows'] for c in report['root_checks']),'full_mid_end',report['temporal_checks'],report.get('failure',''))
if __name__=='__main__':main()
