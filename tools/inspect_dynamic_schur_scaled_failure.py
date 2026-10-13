"""Archive exact J/b/d of the first scaled rejection, replay, then Decimal100 audit."""
import json,os,struct,subprocess
from decimal import Decimal,localcontext
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    work=ROOT/'references-local/dynamic-schur-scaled-inspection01';require(not work.exists(),'exclusive scaled inspection');work.mkdir();old=ROOT/'references-local/dynamic-schur-diagnostic02';matrix=work/'failed-system.bin';proxy=work/'proxy.rs'
    s=(old/'proxy.rs').read_text(encoding='utf8');anchor='assert!(a.1<=1e-11&&c.1<=1e-11,';require(anchor in s,'unchanged rejecting gate')
    dump='''if a.1>1e-11||c.1>1e-11{let mut bytes=b"RFSCHJ01".to_vec();for row in j{for v in row{bytes.extend(v.to_le_bytes());}}for values in [b,d,full]{for v in values{bytes.extend(v.to_le_bytes());}}std::fs::write("DUMP",bytes).unwrap();}'''.replace('DUMP',matrix.as_posix())
    proxy.write_text(s.replace(anchor,dump+anchor),encoding='utf8',newline='\n');kp=work/'kernel.rs';kp.write_text((old/'kernel.rs').read_text(encoding='utf8').replace((old/'proxy.rs').as_posix(),proxy.as_posix()),encoding='utf8',newline='\n');p=work/'inspect.rs';p.write_text((old/'diagnostic.rs').read_text(encoding='utf8').replace((old/'kernel.rs').as_posix(),kp.as_posix()).replace('fn main(){','fn main(){std::panic::set_hook(Box::new(|_|eprintln!("PRESERVED_SCALED_GATE_REJECTION")));',1),encoding='utf8',newline='\n')
    compiler=json.loads((ROOT/'evidence/voice_joint_startup_native01.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');lib='references-local/joint-startup01/librf_d_circuit.rlib';packet='references-local/newton-reuse-inputs01/pairs.bin';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];exe=work/'inspect.exe';q=subprocess.run([compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',str(p),'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120,creationflags=subprocess.CREATE_NO_WINDOW);require(q.returncode==0,'inspection compile');commands=[];saved=None
    for _ in range(2):
        q=subprocess.run([str(exe),str(ROOT/packet)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=600,creationflags=subprocess.CREATE_NO_WINDOW);commands.append(dict(exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr));raw=matrix.read_bytes()
        if saved is not None:require(saved==raw,'same exact failing system')
        saved=raw
    require(commands[0]==commands[1] and commands[0]['exit_code']!=0,'canonical replay preserves rejection');require(saved[:8]==b'RFSCHJ01' and len(saved)==8+8*(458*458+3*458),'matrix format');values=struct.unpack('<'+str(458*458+3*458)+'d',saved[8:]);rows=[]
    with localcontext() as ctx:
        ctx.prec=100;v=[Decimal.from_float(x) for x in values];n=458*458;b=v[n:n+458];tau=[Decimal.from_float(2e-12 if 98<=k%229<133 else 2e-9) for k in range(458)]
        for label,start in [('schur',n+458),('reference',n+916)]:
            d=v[start:start+458];metrics=[]
            for i in range(458):
                coeff=v[458*i:458*(i+1)];products=[a*x for a,x in zip(coeff,d)];error=abs(sum(products,Decimal(0))-b[i]);scale=abs(b[i])+sum(map(abs,products),Decimal(0))+sum((abs(a)*t for a,t in zip(coeff,tau)),Decimal(0));ratio=error/scale if scale else Decimal(0);metrics.append((ratio,i,error,scale))
            ratio,i,error,scale=max(metrics);require(ratio>Decimal('1e-11'),'exact operands still reject')
            rows.append(dict(method=label,worst_row=i,mixed_backward=str(ratio),absolute_residual=str(error),scale=str(scale),failed_rows=sum(x[0]>Decimal('1e-11') for x in metrics)))
    write('evidence/voice_dynamic_schur_scaled_inspection01.json',dict(passed=False,inspection_passed=True,numerical_gates_changed=False,identical_canonical_replay=True,exact_matrix_replay=True,precision=100,decimal_operands='exact binary64 operands',metrics=rows,commands=commands,source_sha256={name:sha(ROOT/name) for name in ['tools/inspect_dynamic_schur_scaled_failure.py','tools/dynamic_schur_fast_solver.rs','evidence/voice_dynamic_schur_diagnostic02.json','docs/SCHUR_DINAMICO_ESCALA_RESIDUAL.md']},private_used_sha256={lib:sha(ROOT/lib),packet:sha(ROOT/packet)},outputs=[dict(path=x.relative_to(ROOT).as_posix(),sha256=sha(x),bytes=x.stat().st_size) for x in work.iterdir() if x.is_file()]))
    print('EXACT_SCALED_REJECTION',json.dumps(rows))

if __name__=='__main__':main()
