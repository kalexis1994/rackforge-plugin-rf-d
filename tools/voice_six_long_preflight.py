"""Resource gate for four six-correction 350 ms notes; no SPICE launch."""
import json,math,os,shutil,sys
from pathlib import Path
import numpy as np
import voice_six_runner as runner
import voice_six_build as build
import voice_full_note as note
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def estimate():
    bank_path=ROOT/'evidence/voice_six_short_runs01.json'
    audit_path=ROOT/'evidence/voice_six_short_validation01.json'
    bank=vco.read(bank_path);audit=vco.read(audit_path)
    if not audit['passed'] or not audit['joint_admitted_locally'] or audit['bank_sha256']!=vco.sha(bank_path):raise ValueError('admitted audited six short bank required')
    for source in (bank['wrapper_sha256'],audit['analysis_source_sha256']):
        for name,digest in source.items():
            if vco.sha(ROOT/name)!=digest:raise ValueError('short input changed')
    estimates={}
    for name in note.scenes():
        r=bank['records']['joint-'+name];p=runner.WORK/('joint-'+name+'.txt')
        if not r['trajectory_complete'] or vco.sha(p)!=r['raw_export_sha256'] or p.stat().st_size!=r['raw_export_bytes']:raise ValueError('six short export identity')
        estimates[name]=dict(short_rows=r['rows'],short_export_bytes=p.stat().st_size,duration_ratio=8.75,
            estimated_long_rows=math.ceil(r['rows']*8.75),estimated_long_export_bytes=math.ceil(p.stat().st_size*8.75),short_wall_s=r['wall_s'])
    required=sum(x['estimated_long_export_bytes'] for x in estimates.values());margin=2*1024**3
    free=shutil.disk_usage(ROOT).free
    return dict(schema='rf-d/active-six-long-preflight/v1',passed=free>=required+margin,estimates=estimates,
        estimated_exports_bytes=required,margin_bytes=margin,required_free_bytes=required+margin,available_free_bytes=free,
        estimates_are_not_bounds=True,processes=4,wall_limit_s_per_process=7200,logical_cpus=os.cpu_count(),
        short_bank_sha256=vco.sha(bank_path),short_audit_sha256=vco.sha(audit_path),
        protocol_sha256=vco.sha(ROOT/build.PROTOCOL),long_protocol_sha256=vco.sha(ROOT/note.PROTOCOL),
        helper_sha256=vco.sha(Path(__file__)),new_spice_solves=0,new_audio=False,
        python_version=sys.version,numpy_version=np.__version__)

def main():
    output=ROOT/'evidence/voice_six_long_preflight01.json'
    if output.exists():raise ValueError('preserve long preflight')
    report=estimate()
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('six long resources:',report['passed'],'available:',report['available_free_bytes'],'required:',report['required_free_bytes'],'new solves: 0')

if __name__=='__main__':main()
