"""Reuse checked coarse equations and check every preserved fine segment.
The original checker and its coarse receipt remain byte-identical. Cache
reuse avoids recounting/reexecuting the same 24 stages as new coverage.
"""
import argparse,json,time,traceback
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from check_joint_cycles import check

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);parser.add_argument('--continuations',required=True);a=parser.parse_args()
    out=ROOT/f'evidence/voice_joint_cycles_reference{a.attempt:02d}.json';require(not out.exists(),'new final reference receipt')
    coarse_name='evidence/voice_joint_cycles_coarse_reference01.json';cache=json.loads((ROOT/coarse_name).read_text())
    require(cache['passed'] and cache['coarse_only'] and cache['source_sha256']==cache['source_sha256_after'],'admitted coarse reference')
    for n,h in {**cache['source_sha256'],**cache['input_sha256']}.items():require(sha(ROOT/n)==h,'unchanged coarse input '+n)
    native=json.loads((ROOT/'evidence/voice_joint_cycles_native01.json').read_text());extension=json.loads((ROOT/a.continuations).read_text());require(extension['passed'] and extension['exact_seams'],'complete aggregated continuation')
    names=[*cache['source_sha256'],coarse_name,'tools/check_joint_cycles_completed.py',a.continuations]
    before={n:sha(ROOT/n) for n in names};report=dict(schema='rf-d/joint-cycles-reference/v1',passed=False,source_sha256=before,native_candidate_points_used=True,independent_root_solve=False,new_spice_processes=0,current_gate_a=2e-11,coarse_only=False,cached_coarse_receipt=coarse_name)
    parts=[native['profiles'][1],*extension['profiles']];started=time.perf_counter()
    try:
        with localcontext() as ctx:ctx.prec=100;result=check(parts)
        for key in ['root_checks','temporal_checks','current_checks']:result[key]=cache[key]+result[key]
        result['input_sha256']={**cache['input_sha256'],**result['input_sha256']};report.update(result);report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']=(ROOT/'tools/check_joint_cycles_completed.py').read_text()
        try:
            with localcontext() as ctx:ctx.prec=100;check(parts)
            report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['wall_s']=time.perf_counter()-started;report['source_sha256_after']={n:sha(ROOT/n) for n in names};require(before==report['source_sha256_after'],'unchanged reference sources')
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('CYCLES_REFERENCE',report['passed'],'rows',sum(c['rows'] for c in report.get('root_checks',[])),'currents',len(report.get('current_checks',[])),report.get('failure',''))
if __name__=='__main__':main()
