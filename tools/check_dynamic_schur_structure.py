"""Finite structural regressions for the lab Schur partition and explicit rejection."""
import json,os,subprocess
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
MAIN='''#[path="KERNEL"] mod kernel;
fn identity()->[[f64;458];458]{std::array::from_fn(|i|std::array::from_fn(|k|if i==k{1.}else{0.}))}
fn compare(j:[[f64;458];458]){let x:[f64;458]=std::array::from_fn(|k|((k%17) as f64-8.)*1e-3);let b=std::array::from_fn(|i|(0..458).map(|k|j[i][k]*x[k]).sum());let d=kernel::dynamic_schur::solve(j,b).unwrap();let full=kernel::solve_linear_extent(j,b).unwrap();for i in 0..458{assert!((d[i]-x[i]).abs()<1e-12);assert!((d[i]-full[i]).abs()<1e-12);}}
fn main(){
 compare(identity());println!("STRUCTURE,identity");
 let mut j=identity();for(a,b,p,q)in[(56,285,8,237),(77,306,35,264)]{j[a][a]=3.;j[b][b]=4.;j[a][b]=0.75;j[b][a]=-0.5;j[a][p]=-0.2;j[b][q]=-0.3;j[p][a]=0.4;j[q][b]=-0.6;j[p][q]=0.125;}compare(j);println!("STRUCTURE,two_stage_loaded_ports");
 let mut j=identity();j[56][56]=0.;j[56][57]=1.;j[57][56]=1.;j[57][57]=2.;compare(j);println!("STRUCTURE,interior_pivot");
 let mut j=identity();j[0][0]=0.;j[0][1]=1.;j[1][0]=1.;j[1][1]=2.;compare(j);println!("STRUCTURE,exterior_pivot");
 for(label,j)in[("interior_singular",{let mut j=identity();j[56]=[0.;458];j}),("exterior_singular",{let mut j=identity();j[0]=[0.;458];j}),("foreign_voltage_coupling",{let mut j=identity();j[56][134]=1.;j}),("cross_chip_coupling",{let mut j=identity();j[56][77]=1.;j}),("foreign_return_coupling",{let mut j=identity();j[134][56]=1.;j})]{assert!(kernel::dynamic_schur::solve(j,[0.;458]).is_err());println!("STRUCTURE,{label}");}
 println!("STRUCTURAL_PASSED,9");
}
'''
def main():
    work=ROOT/'references-local/dynamic-schur-structure01';require(not work.exists(),'exclusive structure');work.mkdir();p=work/'structure.rs';p.write_text(MAIN.replace('KERNEL',(ROOT/'tools/joint_dynamic_schur_fast_kernel.rs').as_posix()),encoding='utf8',newline='\n');exe=work/'structure.exe';lib='references-local/joint-startup01/librf_d_circuit.rlib';compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[]
    for cmd in [[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(p),'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)],[str(exe)]]:
        q=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);commands.append(dict(command=cmd,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr));require(q.returncode==0,'structure command')
    require(commands[-1]['stdout'].splitlines()[-1]=='STRUCTURAL_PASSED,9','structure scope')
    write('evidence/voice_dynamic_schur_structure01.json',dict(passed=True,regressions=9,full_trajectory_admitted=False,source_sha256={n:sha(ROOT/n) for n in ['tools/check_dynamic_schur_structure.py','tools/dynamic_schur_fast_solver.rs','tools/joint_dynamic_schur_fast_kernel.rs']},private_used_sha256={lib:sha(ROOT/lib)},commands=commands,outputs=[dict(path=x.relative_to(ROOT).as_posix(),sha256=sha(x),bytes=x.stat().st_size) for x in work.iterdir() if x.is_file()]))
    print('SCHUR_STRUCTURE',9)
if __name__=='__main__':main()
