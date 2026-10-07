"""Diagnostic only: compare a completed export prefix to the older long rejection."""
import argparse,hashlib,json,lzma,time
from pathlib import Path
import numpy as np
from mixer_on_native_vectors import ROOT,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--scene',required=True);args=p.parse_args()
    scene=args.scene;output=ROOT/f'evidence/voice_serial_prefix_{scene}01.json'
    if output.exists():raise ValueError('preserve prefix diagnostic')
    oldp=ROOT/'evidence/voice_full_note_runs01.json';oldbank=json.loads(oldp.read_text(encoding='utf8'))
    newbank=json.loads((ROOT/'evidence/voice_serial_runs01.json').read_text(encoding='utf8'))
    old=oldbank['records'][scene];new=newbank['records'][scene];archive=newbank['archives'][scene]
    oldraw=ROOT/'references-local/voice-circuit/full-note01'/f'{scene}.txt'
    work=ROOT/'references-local/voice-circuit/active-six-binary-long01'
    if Path(archive['archive_path']).name!=archive['archive_path']:raise ValueError('archive must be a campaign basename')
    ap=work/archive['archive_path'];manifest=work/f'{scene}.archive.json'
    paths=[Path(__file__),oldp,oldraw,ap,manifest]
    before={path.relative_to(ROOT).as_posix():sha(path) for path in paths}
    if before[oldraw.relative_to(ROOT).as_posix()]!=old['raw_export_sha256'] or sha(ap)!=archive['archive_sha256'] or sha(manifest)!=newbank['archive_manifest_sha256'][scene]:
        raise ValueError('archived prefix identities')
    start=time.perf_counter()
    # Decode in RAM, never restore a file or compete with serial phase disk gates.
    with lzma.open(ap,'rb') as f:blob=f.read()
    if len(blob)!=archive['original_bytes'] or hashlib.sha256(blob).hexdigest()!=archive['original_sha256'] or archive['codec']!='xz6-crc64':
        raise ValueError('complete prefix archive decode')
    layout=new['native_layout'];fresh=np.frombuffer(blob,dtype='<f8',offset=layout['header_bytes']).reshape(layout['rows'],layout['columns'])
    prior=np.loadtxt(oldraw,skiprows=1)
    header=oldraw.open(encoding='utf8').readline().split()
    if header!=layout['canonical_columns'] or not np.isfinite(prior).all() or not np.isfinite(fresh).all():raise ValueError('prefix columns/domain')
    same_shape=prior.shape==fresh.shape;delta={};counts={}
    if same_shape:
        for i,n in enumerate(header):
            delta[n]=float(np.max(np.abs(prior[:,i]-fresh[:,i])))
            counts[n]=int(np.count_nonzero(prior[:,i].view(np.uint64)!=fresh[:,i].view(np.uint64)))
    after={path.relative_to(ROOT).as_posix():sha(path) for path in paths}
    if before!=after:raise ValueError('prefix diagnostic source changed')
    report=dict(schema='rf-d/serial-long-prefix-diagnostic/v1',scene=scene,source_sha256=before,source_sha256_after=after,
        old_rows=int(prior.shape[0]),new_rows=int(fresh.shape[0]),old_last_s=float(prior[-1,0]),new_last_s=float(fresh[-1,0]),
        same_shape=same_shape,bit_difference_counts=counts,max_absolute_differences_by_unit=delta,
        same_prefix_bits=same_shape and not any(counts.values()),wall_s=time.perf_counter()-start,
        old_executable_sha256=old['executable_sha256'],new_executable_sha256=new['executable_sha256'],
        no_file_restoration=True,new_spice_solves=0,cause_identified=False,long_note_admitted=False,
        observation='accepted prefixes only; no coverage of absent time or proof of failure cause',physical_fidelity=False,real_time=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('prefix diagnostic',scene,'same bits',report['same_prefix_bits'],'rows',prior.shape[0],fresh.shape[0],flush=True)

if __name__=='__main__':main()
