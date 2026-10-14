"""Bounded unchanged-matrix diagnostic; no admission or tolerance changes."""
import json,os,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from check_hybrid_voice import packed,unpack
from check_vco_phase import COMPILER,LIB

def main():
    assert not (ROOT/'evidence/hybrid_schur_diagnostic01.json').exists(), 'preserve the original diagnostic'
    work=ROOT/'tmp/lab-current';assert not list(work.iterdir())
    failed=json.loads((ROOT/'evidence/hybrid_schur_native01.json').read_text(encoding='utf8'));data=unpack(failed['local_input'])
    source=(ROOT/'tools/hybrid_schur_local.rs').read_text(encoding='utf8')
    source=source.replace('let worst=(0..M).fold', 'let refined=refine(j,rhs,full);let mut max_raw=0_f64;let mut max_refined=0_f64;let mut index=0;for k in 0..M{let raw=(d[k]-full[k]).abs()/(2e-9+1e-7*full[k].abs());if raw>max_raw{max_raw=raw;index=k;}max_refined=max_refined.max((d[k]-refined[k]).abs()/(2e-9+1e-7*refined[k].abs()));}println!("DIAG,{cases},{index},{max_raw:.17e},{max_refined:.17e},{:.17e},{:.17e},{:.17e}",d[index],full[index],refined[index]);let worst=(0..M).fold')
    source=source.replace('assert!(worst<=1.,"direction {worst}");','')
    source=source.replace('../crates/',(ROOT/'crates').as_posix()+'/')
    source+='''
fn refine(j:[[f64;M];M],b:[f64;M],mut d:[f64;M])->[f64;M]{
 for _ in 0..3{let mut r=[0.;M];for i in 0..M{let mut high=-b[i];let mut low=0.;for k in 0..M{let p=j[i][k]*d[k];let s=high+p;low+=if high.abs()>=p.abs(){(high-s)+p}else{(p-s)+high};low+=j[i][k].mul_add(d[k],-p);high=s;}r[i]=-(high+low);}
 let e=rf_d_circuit::block_decay_voice::solve_linear_extent(j,r).unwrap();for k in 0..M{d[k]+=e[k];}}
 d
}
'''
    path=work/'diagnostic.rs';path.write_text(source,encoding='utf8',newline='\n');exe=work/'diagnostic.exe';env=dict(os.environ,PATH='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+os.environ['PATH'])
    command=[COMPILER,'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432','-A','unused_imports','-A','dead_code',str(path),'--extern','rf_d_circuit='+str(LIB),'-o',str(exe)]
    c=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=120);assert c.returncode==0,c.stderr.decode(errors='replace')
    p=subprocess.run([str(exe)],cwd=ROOT,env=env,input=data,capture_output=True,timeout=120);assert p.returncode==0,p.stderr.decode(errors='replace')
    lines=[list(map(float,s.split(',')[1:])) for s in p.stdout.decode().splitlines() if s.startswith('DIAG,')]
    r=dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/diagnose_hybrid_schur.py','tools/hybrid_schur_local.rs','crates/rf-d-circuit/src/hybrid_schur_solver.rs','evidence/hybrid_schur_native01.json']},executed_source=packed(source.encode()),stdout=packed(p.stdout),input_sha256=__import__('hashlib').sha256(data).hexdigest(),cases=len(lines),max_raw_fraction=max(x[2] for x in lines),max_refined_fraction=max(x[3] for x in lines),worst_refined=sorted(lines,key=lambda x:x[3])[-8:],new_private_sound_inputs=0)
    write(ROOT/'evidence/hybrid_schur_diagnostic01.json',r)
    for item in list(work.iterdir()):assert item.is_file() and item.resolve().parent==work.resolve();item.unlink()
    print('SCHUR_DIAGNOSTIC',r['max_raw_fraction'],r['max_refined_fraction'],r['worst_refined'],flush=True)
if __name__=='__main__':main()
