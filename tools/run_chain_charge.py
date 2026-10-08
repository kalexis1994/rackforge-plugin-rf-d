import argparse,json,os,shutil,subprocess,time
from prepare_vco1_portable import ROOT,sha
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args()
    out=ROOT/f'evidence/voice_chain_charge_native{a.attempt:02d}.json';work=ROOT/f'references-local/chain-charge-native{a.attempt:02d}'
    assert not out.exists() and not work.exists()
    compiler=json.loads((ROOT/'evidence/voice_vco1_portable_native03.json').read_text())['compiler'];assert sha(__import__('pathlib').Path(compiler['path']))==compiler['sha256']
    sources=['docs/CADENA_CARGA_RADAU_PROTOCOLO.md','crates/rf-d-circuit/src/lib.rs',
        'crates/rf-d-circuit/src/chain_charge.rs','crates/rf-d-circuit/src/chain_radau.rs','crates/rf-d-circuit/tests/chain_charge.rs',
        'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','evidence/voice_chain_charge_reference06.json','evidence/voice_chain_charge_vectors06.txt','tools/run_chain_charge.py']
    before={n:sha(ROOT/n) for n in sources};free=shutil.disk_usage(ROOT).free
    report=dict(schema='rf-d/chain-charge-native/v1',passed=False,compiler=compiler,source_sha256=before,commands=[],replays=[],outputs=[],
        available_free_bytes=free,reserve_bytes=1024**3,estimated_build_bytes=128*1024**2,process_budget_s=900,lab_stack_bytes=8388608)
    def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write();assert free>=1024**3+128*1024**2,'preflight disk'
    work.mkdir();lib=work/'librf_d_circuit.rlib';exe=work/'tests.exe'
    prefix=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608']
    commands=[prefix+['--crate-type','lib','--crate-name','rf_d_circuit','crates/rf-d-circuit/src/lib.rs','-o',str(lib)],
        prefix+['--test','crates/rf-d-circuit/tests/chain_charge.rs','--extern','rf_d_circuit='+str(lib),'-o',str(exe)],
        [str(exe),'--nocapture','--test-threads=1']]
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='8388608'
    start=time.perf_counter()
    for cmd in commands:
        r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=900)
        report['commands'].append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));write()
        if r.returncode:
            report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in sources if n.endswith(('.rs','.py'))}
            rr=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=900)
            report['replays'].append(dict(command=cmd,exit_code=rr.returncode,stdout=rr.stdout,stderr=rr.stderr));break
    report['source_sha256_after']={n:sha(ROOT/n) for n in sources};report['wall_s']=time.perf_counter()-start
    report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()]
    report['passed']=len(report['commands'])==3 and all(c['exit_code']==0 for c in report['commands']) and before==report['source_sha256_after']
    write();print(report['commands'][-1]['stdout']+report['commands'][-1]['stderr']);print('CHAIN_NATIVE',a.attempt,report['passed'])
if __name__=='__main__':main()
