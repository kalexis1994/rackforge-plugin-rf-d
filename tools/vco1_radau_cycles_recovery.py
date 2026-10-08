"""Own-started 30ms nominal Radau bank; immutable serial compressed traces."""
import gzip,hashlib,json,os,shutil,subprocess,threading,time
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_radau_trace as trace
import vco1_radau_joined_trace as joined
import vco1_radau_ports as ports
from vco1_circuit_probes import GATES,comparison
ROOT=ports.ROOT;sha=ports.sha;TICK=125e-9/65536
OUT='evidence/voice_vco1_radau_cycles04.json'

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
    out=ROOT/OUT;work=ROOT/'references-local/vco1-radau-cycles04'
    if out.exists() or work.exists():raise ValueError('preserve cycle campaign')
    parent=json.loads((ROOT/'evidence/voice_vco1_radau_tests01.json').read_text());pre=json.loads((ROOT/'evidence/voice_vco1_radau_probe01.json').read_text())
    names=set(parent['source_sha256'])|{'evidence/voice_vco1_radau_tests01.json','tools/vco1_radau_cycles.py','tools/vco1_radau_trace.py','tools/vco1_radau_cycles_runner.rs','tools/vco1_radau_cycles_resume.py','tools/vco1_radau_cycles_resume_runner.rs','tools/vco1_radau_joined_trace.py','docs/VCO1_RADAU_CICLOS_PROTOCOLO.md','docs/VCO1_RADAU_CICLOS_EXTENSION_PROTOCOLO.md','evidence/voice_vco1_radau_cycles01.json','evidence/voice_vco1_radau_cycles02.json','evidence/voice_vco1_radau_cycles_resource01.json','evidence/voice_vco1_radau_cycles_repair01.json','evidence/voice_vco1_radau_cycles_extension01.json','evidence/voice_vco1_radau_cycles03.json','evidence/voice_vco1_radau_newton01.json','tools/vco1_radau_newton_probe.py','tools/vco1_radau_failure_runner.rs','tools/vco1_radau_residual_kernel.rs','tools/vco1_radau_cycles_recovery.py','docs/VCO1_RADAU_NEWTON_PROTOCOLO.md','docs/VCO1_RADAU_RECUPERACION_PROTOCOLO.md'}
    sources={n:sha(ROOT/n) for n in names};compiler=pre['compiler'];library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib';reserve=1024**3
    record=dict(schema='rf-d/radau-own-started-cycles/v1',passed=False,source_sha256=sources,compiler=compiler,lab_stack_bytes=8388608,process_budget_s=2400,reserve_bytes=reserve,available_free_bytes=shutil.disk_usage(ROOT).free,resource_passed=shutil.disk_usage(ROOT).free>reserve+128*1024**2,gates=GATES,profiles=[],commands=[],unchanged_replays=[],production_kernel_changed=False,new_audio=False,new_spice_processes=0,physical_fidelity=False,real_time=False,own_started_radau_admitted=False,native_full_period_admitted=False,native_frequency_refinement_admitted=False)
    def save():out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    save()
    if not record['resource_passed']:return
    work.mkdir();oldwork=ROOT/'references-local/vco1-radau-probe01'
    for n in ('fine.rs','linear.rs','vco1_stamp_data.rs','radau.rs'):shutil.copy2(oldwork/n,work/n)
    shutil.copy2(ROOT/'tools/vco1_radau_cycles_resume_runner.rs',work/'runner.rs');shutil.copy2(ROOT/'tools/vco1_radau_residual_kernel.rs',work/'radau.rs');private={p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()}
    private[library.relative_to(ROOT).as_posix()]=sha(library);prior=json.loads((ROOT/'evidence/voice_vco1_radau_cycles03.json').read_text());requirement=prior['profiles'][0]
    if not requirement['complete'] or prior['source_sha256']!=prior['source_sha256_after']:raise ValueError('protected completed250 prerequisite')
    record['profiles'].append(requirement);record['inherited_250_profile']=True;record['inherited_250_receipt_sha256']=sha(ROOT/'evidence/voice_vco1_radau_cycles03.json')
    for e in requirement['segments']:private[e['path']]=sha(ROOT/e['path'])
    private['references-local/vco1-radau-cycles03/walk-65536.xor.gz']=sha(ROOT/'references-local/vco1-radau-cycles03/walk-65536.xor.gz');record['private_input_sha256']=private;save()
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];exe=work/'cycles.exe';start=time.perf_counter()
    def execute(cmd,tag,path=None):
        began=time.monotonic();stop=threading.Event();rejection=[];digest=hashlib.sha256();size=0
        with (work/(tag+'.stderr')).open('wb') as se,(work/(tag+'.stdout')).open('wb') as so:
            process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=subprocess.PIPE if path else so,stderr=se)
            def guard():
                while not stop.wait(.25):
                    why='disk reserve' if shutil.disk_usage(ROOT).free<reserve else 'process budget' if time.monotonic()-began>2400 else None
                    if why and process.poll() is None:rejection.append(why);process.terminate();return
            thread=threading.Thread(target=guard);thread.start()
            try:
                if path:
                    with path.open('wb') as disk,gzip.GzipFile(filename='',fileobj=disk,mode='wb',compresslevel=6,mtime=0) as zipped:
                        while chunk:=process.stdout.read(trace.BLOCK*trace.COLS*8):
                            digest.update(chunk);size+=len(chunk);whole=len(chunk)//(trace.COLS*8)*(trace.COLS*8)
                            if whole:zipped.write(trace.encode_block(chunk[:whole]))
                            if whole<len(chunk):(work/(tag+'.partial-native-tail')).write_bytes(chunk[whole:])
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
        for maximum in (65536,):
            path=work/f'walk-{maximum}.xor.gz';cmd=[str(exe),str(maximum)];prefix=None;extra=None
            if maximum==65536:
                source=ROOT/'references-local/vco1-radau-cycles03/walk-65536.xor.gz';count=0;tail=[]
                for block in trace.blocks(source):count+=len(block);tail.extend(block[-2:].copy());tail=tail[-2:]
                take=count if count%2 else count-1;old=tail[-1] if take==count else tail[-2];extra=tail[-1] if take<count else None
                half=int(old[1]);proposal=min(4*half,2*maximum) if old[4]<=.25 else 2*half
                checkpoint=work/'checkpoint.txt';checkpoint.write_text(' '.join(format(v,'.17e') for v in old[6:274])+'\n',encoding='utf8',newline='\n')
                private[checkpoint.relative_to(ROOT).as_posix()]=sha(checkpoint)
                prefix=dict(path=source.relative_to(ROOT).as_posix(),sha256=sha(source),skip_rows=0,take_rows=take,original_rows=count,last_clock_ticks=int(old[0]),proposal_ticks=proposal,checkpoint_path=checkpoint.relative_to(ROOT).as_posix(),checkpoint_sha256=sha(checkpoint),last_endpoint_high=old[6:140].tolist(),last_endpoint_low=old[140:274].tolist())
                record['preserved_prefix']=prefix;save();cmd.extend([str(checkpoint),str(int(old[0])),str(proposal)])
            result=execute(cmd,str(maximum),path);record['commands'].append(result);save()
            profile=dict(maximum_accepted_half_ticks=maximum,complete=False,actual_intervals=[]);record['profiles'].append(profile)
            profile['export']=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size);save()
            if result['exit_code']:
                save();raise ValueError('native segment rejected; original retained; diagnose resource or exact rejected interval before rerun')
            digest=hashlib.sha256();size=0;rows=0;echo=None;first_new=None
            for block in trace.blocks(path):
                digest.update(block.tobytes());size+=block.nbytes
                if echo is None:echo=block[0].copy();first_new=block[1].copy() if len(block)>1 else None
                rows+=len(block)
            if digest.hexdigest()!=result['native_stream_sha256'] or size!=result['native_stream_bytes']:raise ValueError('lossless new native export identity')
            entries=[]
            if prefix:
                if not np.array_equal(echo[6:140],prefix['last_endpoint_high']) or not np.array_equal(echo[140:274],prefix['last_endpoint_low']) or echo[0]!=prefix['last_clock_ticks']:raise ValueError('checkpoint echo identity')
                entries.append(dict(path=ROOT/prefix['path'],skip_rows=0,take_rows=prefix['take_rows']))
                profile['checkpoint_echo_verified']=True
                profile['overlap_additional_row_byte_equal']=extra is None or first_new is not None and extra.tobytes()==first_new.tobytes()
                if not profile['overlap_additional_row_byte_equal']:raise ValueError('additional surviving mid-step differs after continuation')
            entries.append(dict(path=path,skip_rows=1 if prefix else 0,take_rows=rows))
            profile['segments']=[dict(path=e['path'].relative_to(ROOT).as_posix(),skip_rows=e['skip_rows'],take_rows=e['take_rows']) for e in entries]
            profile['new_native_stream']=dict(uncompressed_sha256=digest.hexdigest(),uncompressed_bytes=size,rows=rows)
            coverage,first,selected,m=joined.summary(entries,maximum);profile.update(coverage=coverage,measurements=m)
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
