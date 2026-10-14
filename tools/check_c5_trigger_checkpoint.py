"""Restore measured GRID states with an explicit next proposal; no trace rerender."""
import base64,csv,json,struct,subprocess,time,os
from pathlib import Path
from run_c5_trigger import ROOT,sha,write,LIB,COMPILER
OWN=['crates/rf-d-circuit/src/dual_contour.rs','crates/rf-d-circuit/src/dual_contour_checkpoint.rs','tools/c5_trigger_checkpoint_bank.rs','tools/check_c5_trigger_checkpoint.py']
def main():
    out=ROOT/'references-local/c5-trigger-checkpoint01';out.mkdir()
    receipts=json.loads((ROOT/'evidence/c5_trigger_native02.json').read_text());payload=bytearray();count=0
    for p in receipts['profiles']:
        path=ROOT/receipts['output_directory']/(p['label']+'.stdout');assert sha(path)==p['stdout_sha256']
        for row in csv.reader(path.read_text().splitlines()):
            if row[0]!='GRID':continue
            v=list(map(float,row[1:]));ticks=int(v[0])
            if ticks//1073741824 not in [2000,8500,12000,22000,32000]:continue
            flags=p['optional']|(int(v[2])<<1)
            payload+=struct.pack('<8sQQI4xd108d',b'RFDC5011',ticks,p['maximum_us']*1073741824,flags,v[1],*v[3:111]);count+=1
    (out/'fixtures.bin').write_bytes(payload);assert count==40
    sources={n:sha(ROOT/n) for n in OWN}
    env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    exe=out/'check.exe';command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','dead_code',str(ROOT/'tools/c5_trigger_checkpoint_bank.rs'),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    started=time.monotonic();r=dict(passed=False,source_sha256=sources,fixtures=40,fixture_sha256=sha(out/'fixtures.bin'))
    def run(cmd,label):
        p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=120);(out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr);return p
    phase='compile'
    try:
        p=run(command,'compile');assert p.returncode==0,p.stderr.decode()
        phase='run';p=run([str(exe),str(out/'fixtures.bin')],'run');assert p.returncode==0,p.stderr.decode();assert p.stdout.strip()==b'PASSED,40,320';r['passed']=True;r['complete_pair_replays']=40;r['corruptions_rejected']=320
    except Exception as e:
        r['error']=repr(e);r['failed_phase']=phase
        write(out/'failed_sources.json',{n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in OWN})
        replay=run(command if phase=='compile' else [str(exe),str(out/'fixtures.bin')],'replay');r['unchanged_replay']=dict(exit_code=replay.returncode,stdout_identical=replay.stdout==p.stdout,stderr_identical=replay.stderr==p.stderr)
    r['wall_s']=time.monotonic()-started;r['source_unchanged']=sources=={n:sha(ROOT/n) for n in OWN};assert r['source_unchanged']
    r['private_sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir() if p.is_file()};write(ROOT/'evidence/c5_trigger_checkpoint01.json',r);print(json.dumps({k:v for k,v in r.items() if k not in ['source_sha256','private_sha256']},indent=2));assert r['passed']
if __name__=='__main__':main()
