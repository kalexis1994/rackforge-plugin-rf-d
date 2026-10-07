"""Compile a bound laboratory root for new chain code without changing live release."""
import argparse,json,os,re,shutil,subprocess,time
from pathlib import Path
from mixer_on_native_vectors import ROOT,sha

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);args=parser.parse_args()
    if not 1<=args.attempt<=99:raise ValueError('attempt 1..99')
    out=ROOT/f'evidence/voice_mixer_chain_native_attempt{args.attempt:02d}.json'
    work=ROOT/f'references-local/mixer-chain-native{args.attempt:02d}'
    if out.exists() or work.exists():raise ValueError('preserve chain attempt')
    lab=ROOT/'crates/rf-d-circuit/examples/bench_ladder_recovery_output.rs';text=lab.read_text(encoding='utf8')
    support=ROOT/'crates/rf-d-circuit/tests/support/mixer_chain_lab.rs'
    support.parent.mkdir(exist_ok=True)
    extracted='// Laboratory fragments from bench_ladder_recovery_output.rs; byte-bound by runner.\n'+text[text.index('use std::hint'):text.index('const SAMPLE_RATE')]
    extracted+='const SAMPLE_RATE: usize = 48_000;\n'+text[text.index('pub(crate) const SEED'):text.index('fn percentile')]
    extracted+=text[text.index('fn boundary(sample'):text.index('enum BenchState')]
    extracted+=text[text.index('pub(crate) fn controlled_boundary'):text.index('fn main()')]
    if support.exists():
        if support.read_bytes()!=extracted.encode():raise ValueError('preserved lab fragments changed')
    else:support.write_text(extracted,encoding='utf8',newline='\n')
    names=['tools/mixer_chain_native_run.py','docs/MEZCLADOR_CADENA_PROTOCOLO.md',
        lab.relative_to(ROOT).as_posix(),support.relative_to(ROOT).as_posix(),
        'tools/mixer_chain_vectors.py','tools/validate_mixer_chain_vectors.py',
        'evidence/voice_mixer_chain_vectors01.json','evidence/voice_mixer_chain_vectors01.txt',
        'evidence/voice_mixer_chain_vectors_validation01.json','crates/rf-d-circuit/tests/mixer_chain66.rs']
    names+=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'crates/rf-d-circuit/src').glob('*.rs'))
    before={n:sha(ROOT/n) for n in names};rustc=Path(subprocess.check_output(['rustup','which','rustc'],text=True,cwd=ROOT).strip())
    compiler=dict(path=rustc.as_posix(),sha256=sha(rustc),version=subprocess.check_output([str(rustc),'--version'],text=True).strip())
    free=shutil.disk_usage(ROOT).free;estimate=64*1024**2;margin=2*1024**3
    report=dict(schema='rf-d/mixer-chain-native-attempt/v1',passed=False,source_sha256=before,compiler=compiler,commands=[],outputs=[],
        estimated_build_bytes=estimate,margin_bytes=margin,available_free_bytes=free,resource_passed=free>=estimate+margin,
        estimates_are_not_bounds=True,production_lib_export_changed=False,new_spice_solves=0,new_audio=False,real_time=False,physical_fidelity=False)
    def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write()
    if not report['resource_passed']:print('chain compiler storage rejected',flush=True);return
    work.mkdir();root=(ROOT/'crates/rf-d-circuit/src/lib.rs').read_text(encoding='utf8')
    def module(match):
        name=match.group(1);path=(ROOT/f'crates/rf-d-circuit/src/{name}.rs').as_posix()
        return '#[path="'+path+'"]\npub mod '+name+';'
    root=re.sub(r'^pub mod (\w+);$',module,root,flags=re.M)
    root+='\n#[path="'+(ROOT/'crates/rf-d-circuit/src/mixer_chain66.rs').as_posix()+'"]\npub mod mixer_chain66;\n'
    rp=work/'lib.rs';rp.write_text(root,encoding='utf8',newline='\n');report['laboratory_root_sha256']=sha(rp)
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
    library=work/'librf_d_circuit.rlib';test=work/'chain.exe'
    commands=[('compile',[str(rustc),'--edition=2021','--crate-type','lib','--crate-name','rf_d_circuit',str(rp),'-o',str(library)]),
              ('compile',[str(rustc),'--edition=2021','--test','--crate-name','mixer_chain66',
                  'crates/rf-d-circuit/tests/mixer_chain66.rs','--extern','rf_d_circuit='+str(library),'-o',str(test)]),
              ('test',[str(test),'--nocapture','--test-threads=1'])]
    start=time.perf_counter()
    try:
        for kind,command in commands:
            process=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=900)
            report['commands'].append(dict(kind=kind,command=command,exit_code=process.returncode,stdout=process.stdout,stderr=process.stderr))
            if kind=='test' or process.returncode:print(process.stdout+process.stderr,flush=True)
            if process.returncode:raise RuntimeError('chain native '+kind+' rejected')
        report['passed']=True
    except (OSError,subprocess.TimeoutExpired,RuntimeError) as exc:
        report['error']=str(exc);report['failed_source_text']={n:(ROOT/n).read_text(encoding='utf8') for n in names if n.endswith(('.rs','.py','.md'))}
    report['outputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in (rp,library,test) if p.exists()]
    report.update(wall_s=time.perf_counter()-start,source_sha256_after={n:sha(ROOT/n) for n in names},compiler_sha256_after=sha(rustc))
    report['passed']=report['passed'] and before==report['source_sha256_after'] and compiler['sha256']==report['compiler_sha256_after']
    write();print('chain native attempt',args.attempt,report['passed'],flush=True)

if __name__=='__main__':main()
