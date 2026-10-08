"""Preserved diagnosis of a test's unproven nonlinear-rejection assumption."""
import json,os,subprocess
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
def main():
    out=ROOT/'evidence/voice_vco1_portable_diagnostic01.json'
    folder=ROOT/'references-local/vco1-portable-diagnostic01';assert not out.exists() and not folder.exists()
    folder.mkdir();v=json.loads((ROOT/'evidence/voice_vco1_portable_vectors01.json').read_text())['diagnostic']
    def rs(a): return '['+','.join(repr(x) for x in a)+']'
    text='''use rf_d_circuit::{vco1_engine::{Engine,State,Settings,Checkpoint},vco1_stamp::Controls};
fn main() { let state=State {high:HIGH,low:LOW};
 for scene in 0..8 { let mut c=Controls::default();
 match scene {0=>c.external_neg4_load_a=1.,1=>c.external_neg4_load_a=-1.,2=>c.cv_v[5]=40.,3=>c.cv_v[5]=-40.,4=>c.mixer_v=40.,5=>c.mixer_v=-40.,6=>c.cv_v=[40.;6],_=>c.cv_v=[-40.;6]};
 let q=Checkpoint {state,controls:c,settings:Settings{maximum_half_ticks:65536,attempt_limit:1},elapsed_ticks:0,next_full_ticks:8};
 let mut engine=Engine::restore(q).unwrap();
 match engine.advance_to(8) {Ok(a)=>println!("scene={scene},accepted={},attempts={}",a.error_ratio,a.attempts),Err(e)=>println!("scene={scene},error={e:?}")}
 assert_eq!(engine.checkpoint().controls,c);
 }}
'''.replace('HIGH',rs(v['previous_high'])).replace('LOW',rs(v['previous_low']))
    src=folder/'probe.rs';src.write_text(text,encoding='utf8',newline='\n')
    compiler=json.loads((ROOT/'evidence/voice_vco1_portable_native02.json').read_text())['compiler']
    lib=next((ROOT/'tmp/vco1-portable-build02/debug/deps').glob('librf_d_circuit-*.rlib'))
    exe=folder/'probe.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
    commands=[]
    cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608',str(src),'--extern','rf_d_circuit='+str(lib),'-L','dependency='+str(lib.parent),'-o',str(exe)]
    for command in [cmd,[str(exe)],[str(exe)]]:
        r=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
        commands.append(dict(command=command,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        if r.returncode:break
    report=dict(schema='rf-d/portable-rejection-diagnosis/v1',commands=commands,compiler=compiler,
        library_sha256=sha(lib),sources={str(src.relative_to(ROOT)):sha(src)},
        failed_attempt_sha256=sha(ROOT/'evidence/voice_vco1_portable_native02.json'),new_physical_admission=False)
    if exe.exists():report['executable_sha256']=sha(exe)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(commands[-1]['stdout']+commands[-1]['stderr'])
if __name__=='__main__':main()
