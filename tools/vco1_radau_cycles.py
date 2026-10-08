"""Own-started 30ms nominal Radau bank; immutable serial compressed traces."""
import gzip,hashlib,json,os,shutil,subprocess,threading,time
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_radau_trace as trace
import vco1_radau_ports as ports
from vco1_circuit_probes import GATES,comparison
ROOT=ports.ROOT;sha=ports.sha;TICK=125e-9/65536
OUT='evidence/voice_vco1_radau_cycles02.json'

def terminal_currents(stages,old,h):
    from vco1_increment_devices import bjt_reference,jfet_reference
    z=Decimal(0);values=[]
    for indexes,polarity,terminal in (([43,33,18,134],1,0),([43,21,134,134],-1,0),([5,43,4],None,1)):
        at=lambda state:[z if i==134 else state[i] for i in indexes]
        parts=[]
        for x in stages:
            v=bjt_reference(polarity,at(x),at(old),h) if polarity else jfet_reference(at(x),at(old),h)
            n=len(indexes);parts.append((v[terminal],v[n+terminal]-v[terminal]))
        values.append(parts[1][0]+ports.ref.B[1][0]*parts[0][1]+ports.ref.B[1][1]*parts[1][1])
    return values

def audit_intervals(selected):
    inv=ports.ref.circuit.inventory(ports.ref.circuit.scenario(ports.C));items=[]
    with localcontext() as ctx:
        ctx.prec=100
        for k,(previous,now) in sorted(selected.items()):
            old=ports.packed(previous[6:140],previous[140:274]);h=float(now[1]*TICK);sol=ports.ref.solve(old,h,ports.C);pair={}
            for part,col in (('stage',274),('endpoint',6)):
                pair[part]=dict(native=dict(high=now[col:col+134].tolist(),low=now[col+134:col+268].tolist(),residual_ratio=float(now[2]),correction_ratio=float(now[3])),independent_decimal=list(map(str,sol[part])))
            checked=ports.check(pair,old,h,inv);cur=terminal_currents([sol['stage'],sol['endpoint']],old,h)
            errors=[abs(v-Decimal.from_float(float(w))) for v,w in zip(cur,now[542:545])]
            if max(errors)>Decimal.from_float(2e-10):raise ValueError('Radau terminal current comparison')
            panel=(sol['endpoint'][46]-sol['endpoint'][39])/Decimal.from_float(12500.)
            if abs(panel-Decimal.from_float(float(now[545])))>Decimal.from_float(2e-10):raise ValueError('panel current')
            items.append(dict(row_index=int(k),dt_s=h,previous_high=previous[6:140].tolist(),previous_low=previous[140:274].tolist(),roots=pair,ports=checked,independent_currents_a=list(map(str,cur)),native_currents_a=now[542:546].tolist(),max_current_error_a=str(max(errors)),panel_error_a=str(abs(panel-Decimal.from_float(float(now[545]))))))
            print('Radau cycle interval',k,'dt',h,'current error',float(max(errors)),flush=True)
    return items

def main():
    out=ROOT/OUT;work=ROOT/'references-local/vco1-radau-cycles02'
    if out.exists() or work.exists():raise ValueError('preserve cycle campaign')
    parent=json.loads((ROOT/'evidence/voice_vco1_radau_tests01.json').read_text());pre=json.loads((ROOT/'evidence/voice_vco1_radau_probe01.json').read_text())
    names=set(parent['source_sha256'])|{'evidence/voice_vco1_radau_tests01.json','tools/vco1_radau_cycles.py','tools/vco1_radau_trace.py','tools/vco1_radau_cycles_runner.rs','docs/VCO1_RADAU_CICLOS_PROTOCOLO.md'}
    sources={n:sha(ROOT/n) for n in names};compiler=pre['compiler'];library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib';reserve=2*1024**3
    record=dict(schema='rf-d/radau-own-started-cycles/v1',passed=False,source_sha256=sources,compiler=compiler,lab_stack_bytes=8388608,process_budget_s=1200,reserve_bytes=reserve,available_free_bytes=shutil.disk_usage(ROOT).free,resource_passed=shutil.disk_usage(ROOT).free>reserve+128*1024**2,gates=GATES,profiles=[],commands=[],unchanged_replays=[],production_kernel_changed=False,new_audio=False,new_spice_processes=0,physical_fidelity=False,real_time=False,own_started_radau_admitted=False,native_full_period_admitted=False,native_frequency_refinement_admitted=False)
    def save():out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    save()
    if not record['resource_passed']:return
    work.mkdir();oldwork=ROOT/'references-local/vco1-radau-probe01'
    for n in ('fine.rs','linear.rs','vco1_stamp_data.rs','radau.rs'):shutil.copy2(oldwork/n,work/n)
    shutil.copy2(ROOT/'tools/vco1_radau_cycles_runner.rs',work/'runner.rs');private={p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()}
    private[library.relative_to(ROOT).as_posix()]=sha(library);record['private_input_sha256']=private;save()
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];exe=work/'cycles.exe';start=time.perf_counter()
    def execute(cmd,tag,path=None):
        began=time.monotonic();stop=threading.Event();rejection=[];digest=hashlib.sha256();size=0
        with (work/(tag+'.stderr')).open('wb') as se,(work/(tag+'.stdout')).open('wb') as so:
            process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=subprocess.PIPE if path else so,stderr=se)
            def guard():
                while not stop.wait(.25):
                    why='disk reserve' if shutil.disk_usage(ROOT).free<reserve else 'process budget' if time.monotonic()-began>1200 else None
                    if why and process.poll() is None:rejection.append(why);process.terminate();return
            thread=threading.Thread(target=guard);thread.start()
            try:
                if path:
                    with path.open('wb') as disk,gzip.GzipFile(filename='',fileobj=disk,mode='wb',compresslevel=6,mtime=0) as zipped:
                        while chunk:=process.stdout.read(trace.BLOCK*trace.COLS*8):
                            digest.update(chunk);size+=len(chunk);zipped.write(trace.encode_block(chunk))
                    process.stdout.close()
                process.wait()
            finally:
                if process.poll() is None:process.terminate();process.wait()
                stop.set();thread.join()
        return dict(command=cmd,exit_code=process.returncode,stderr=(work/(tag+'.stderr')).read_text(errors='replace'),stdout=(work/(tag+'.stdout')).read_text(errors='replace'),resource_rejection=rejection,wall_s=time.monotonic()-began,native_stream_sha256=digest.hexdigest() if path else None,native_stream_bytes=size)
    try:
        build=execute([compiler['path'],'-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608','--edition=2021',str(work/'runner.rs'),'--extern','rf_d_circuit='+str(library),'-o',str(exe)],'compile');record['commands'].append(build);save()
        if build['exit_code']:
            record['unchanged_replays'].append(execute(build['command'],'compile-replay'));save();raise ValueError('build rejected')
        for maximum in (131072,65536):
            path=work/f'walk-{maximum}.xor.gz';cmd=[str(exe),str(maximum)];result=execute(cmd,str(maximum),path);record['commands'].append(result);save()
            profile=dict(maximum_accepted_half_ticks=maximum,complete=False,actual_intervals=[]);record['profiles'].append(profile)
            profile['export']=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size);save()
            if result['exit_code']:
                replaypath=work/f'walk-{maximum}-replay.xor.gz';record['unchanged_replays'].append(execute(cmd,str(maximum)+'-replay',replaypath));save();raise ValueError('native trajectory rejected; original and replay retained')
            coverage,first,selected,m=trace.summary(path,maximum);profile.update(coverage=coverage,measurements=m)
            if coverage['uncompressed_sha256']!=result['native_stream_sha256'] or coverage['uncompressed_bytes']!=result['native_stream_bytes']:raise ValueError('lossless export identity')
            if abs(coverage['elapsed_s']-.03)>1e-17:raise ValueError('duration')
            startup=json.loads((ROOT/'evidence/voice_vco1_startup_reference01.json').read_text());nominal=next(x for x in startup['cases'] if x['profile']==0 and x['scene']==0)
            if not startup['passed'] or not np.array_equal(first[6:140],nominal['native_root']):raise ValueError('own startup exact inherited root')
            profile['startup_identity']=dict(path='evidence/voice_vco1_startup_reference01.json',sha256=sha(ROOT/'evidence/voice_vco1_startup_reference01.json'),profile=0,scene=0,exact_root=True,initial_high=first[6:140].tolist(),initial_low=first[140:274].tolist());save()
            print('Radau complete',maximum,'frequency',m['frequency_hz'],'spread',m['period_spread_relative'],'charge',m['cycle_charge_check']['relative_imbalance'],'compressed',profile['export']['bytes'],flush=True)
            profile['actual_intervals']=audit_intervals(selected);profile['complete']=True;save()
        record['comparison']=comparison(*[p['measurements'] for p in record['profiles']]);cmp=record['comparison']
        gate=all(p['complete'] and p['measurements']['period_spread_relative']<=GATES['period_spread_relative'] and p['measurements']['cycle_charge_check']['relative_imbalance']<=GATES['cycle_charge_relative'] for p in record['profiles']) and cmp['frequency_error_cents']<=GATES['frequency_refinement_cents'] and max(cmp['output_extrema_error_v'].values())<=GATES['output_extrema_refinement_v']
        record.update(passed=gate,own_started_radau_admitted=gate,native_full_period_admitted=gate,native_frequency_refinement_admitted=gate)
        if not gate:record['error']='frozen full cycle gates failed'
    except Exception as exc:record['error']=repr(exc)
    record.update(source_sha256_after={n:sha(ROOT/n) for n in sources},private_input_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()],wall_s=time.perf_counter()-start)
    record['passed']=record['passed'] and sources==record['source_sha256_after'] and private==record['private_input_sha256_after'];save()
    print('Radau full cycle bank',record['passed'],record.get('error',''),flush=True)

if __name__=='__main__':main()
