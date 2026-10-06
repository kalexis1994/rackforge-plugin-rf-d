"""Compile the exact C arithmetic and compare against Decimal binary64 inputs."""
import json,subprocess,os
from decimal import Decimal,localcontext
from pathlib import Path
import voice_refine_build as build
import voice_matrix_build_retry as prior
import voice_matrix_trace as trace
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=build.WORK

def cases():
    d=Decimal.from_float;out=[]
    with localcontext() as ctx:
        ctx.prec=160
        for a,b in ((.1,.1),(-1.0610000000000002e17,1.2124845799186281e-7),(2.**-60,2.**40),(2.**-400,2.**-400),(-2.**400,2.**400)):
            out.append(dict(input=f'P {a:.17g} {b:.17g}',exact=str(d(a)*d(b)),scale=str(abs(d(a)*d(b))),kind='exact-product'))
        for a,b,c,e in ((1e16,0.,-1e16,1.),(1.,0.,2.**-60,0.),(-1.,-2.**-60,1.,0.),(1.,2.**-60,2.**-60,0.)):
            out.append(dict(input=f'S {a:.17g} {b:.17g} {c:.17g} {e:.17g}',exact=str(d(a)+d(b)+d(c)+d(e)),scale='1',kind='exact-sum'))
        for a,b in ((1e308,2.),(float('inf'),1.),(float('nan'),1.),(2.**-500,1.),(2.**-1074,1.)):
            out.append(dict(input=f'P {a:.17g} {b:.17g}',kind='domain-rejection',rejected=True))
        original_log=prior.WORK/'runs/matrix-on-returned.log'
        record=vco.read(ROOT/'evidence/voice_matrix_observation01.json')['records']['matrix-on-returned']
        if vco.sha(original_log)!=record['log_sha256']:raise ValueError('frozen matrix log identity')
        for s in trace.parse(original_log.read_text(encoding='utf-8')):
            for i in range(s['n']):
                entries=[(a,s['x'][j]) for (row,j),a in s['entries'].items() if row==i];b=s['nodes'][i]['b']
                exact=d(b)-sum((d(a)*d(x) for a,x in entries),Decimal(0))
                scale=abs(d(b))+sum((abs(d(a)*d(x)) for a,x in entries),Decimal(0))
                text=f'R {b:.17g} {len(entries)} '+ ' '.join(f'{a:.17g} {x:.17g} 0' for a,x in entries)
                out.append(dict(input=text,exact=str(exact),scale=str(scale),kind='captured-row',iteration=s['iteration'],node=s['nodes'][i]['name']))
    return out

def check(inputs,stdout):
    lines=stdout.splitlines()
    if len(lines)!=len(inputs):raise ValueError('complete C outputs required')
    results=[]
    with localcontext() as ctx:
        ctx.prec=160
        for case,line in zip(inputs,lines):
            parts=line.split()
            if case.get('rejected'):
                passed=parts==['0'];result=dict(kind=case['kind'],passed=passed)
            else:
                if len(parts)!=3 or parts[0]!='1':raise ValueError('arithmetic unexpectedly rejected')
                hi=trace.number(parts[1]);lo=trace.number(parts[2]);actual=Decimal.from_float(hi)+Decimal.from_float(lo)
                error=actual-Decimal(case['exact']);bound=Decimal('1e-30')*max(Decimal(1),Decimal(case['scale']))
                passed=(error==0) if case['kind'].startswith('exact-') else abs(error)<=bound
                result=dict(kind=case['kind'],passed=passed,error=str(error),bound=str(bound),hi=hi,lo=lo)
                if 'node' in case:result.update(node=case['node'],iteration=case['iteration'])
            results.append(result)
    return results

def main():
    output=ROOT/'evidence/voice_refine_arithmetic02.json'
    if output.exists():raise ValueError('preserve arithmetic experiment')
    folder=WORK/'arithmetic02';folder.mkdir(exist_ok=False);exe=folder/'bench.exe'
    helpers=[Path(__file__),ROOT/'tools/voice_refine_dd.h',ROOT/'tools/voice_refine_bench.c',ROOT/'tools/voice_matrix_trace.py']
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    compiler=Path('C:/msys64/ucrt64/bin/gcc.exe')
    cmd=[str(compiler),'-O2','-g','-m64',str(ROOT/'tools/voice_refine_bench.c'),'-o',str(exe),'-lm']
    env=os.environ.copy();env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True)
    (folder/'build.log').write_text(r.stdout+r.stderr,encoding='utf-8',newline='\n')
    if r.returncode:raise ValueError('arithmetic compilation failed')
    inputs=cases();input_path=folder/'input.txt';input_path.write_text('\n'.join(c['input'] for c in inputs)+'\n',encoding='utf-8',newline='\n')
    r=subprocess.run([str(exe)],cwd=ROOT,env=env,input=input_path.read_text(),capture_output=True,text=True)
    (folder/'output.txt').write_text(r.stdout,encoding='utf-8',newline='\n')
    results=check(inputs,r.stdout) if r.returncode==0 else []
    after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/linear-refine-arithmetic/v1',passed=r.returncode==0 and len(results)==len(inputs) and all(r['passed'] for r in results) and before==after,
        cases_count=len(inputs),captured_rows=sum(c['kind']=='captured-row' for c in inputs),results=results,
        source_sha256=before,source_sha256_after=after,compiler_path=compiler.as_posix(),compiler_sha256=vco.sha(compiler),
        compile_command=cmd,compile_exit_code=0,run_exit_code=r.returncode,stderr=r.stderr,exe_sha256=vco.sha(exe),
        input_sha256=vco.sha(input_path),output_sha256=vco.sha(folder/'output.txt'),build_log_sha256=vco.sha(folder/'build.log'),
        matrix_audit_sha256=vco.sha(ROOT/'evidence/voice_matrix_observation01.json'),
        product_domain='zero or 2^-400<=abs(operand)<=2^400; no fast-math; checked finite intermediates',
        row_accuracy_gate='abs(pair-exact)<=1e-30*max(1,sum(abs(terms)))',new_spice_solves=0)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('compiled arithmetic:',report['passed'],len(inputs),'cases,',report['captured_rows'],'captured rows',flush=True)

if __name__=='__main__':main()
