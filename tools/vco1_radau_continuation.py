"""Serial 3 ms conditional Radau profiles; complete traces and protected rejects."""
import json,os,shutil,subprocess,time
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_radau_reference as ref
from vco1_newton_reference import ROOT,sha
TICK=125e-9/65536
C=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]


def main():
    out=ROOT/'evidence/voice_vco1_radau_continuation01.json';work=ROOT/'references-local/vco1-radau-continuation01'
    if out.exists() or work.exists():raise ValueError('preserve continuation')
    parent=json.loads((ROOT/'evidence/voice_vco1_radau_probe01.json').read_text())
    if not parent['passed']:raise ValueError('1 us prerequisite')
    names=set(parent['source_sha256'])|{'evidence/voice_vco1_radau_probe01.json','tools/vco1_radau_continuation.py','tools/vco1_radau_continuation_runner.rs','docs/VCO1_RADAU_CONTINUACION_PROTOCOLO.md','evidence/voice_vco1_radau_method01.json'}
    before={n:sha(ROOT/n) for n in names}
    compiler=parent['compiler'];library=ROOT/'references-local/vco1-increment-cycles02/librf_d_circuit.rlib'
    estimate=4*20001*542*8
    record=dict(schema='rf-d/coupled-radau-conditional-3ms/v1',passed=False,source_sha256=before,compiler=compiler,
                lab_stack_bytes=8388608,commands=[],unchanged_replays=[],profiles=[],new_spice_processes=0,new_audio=False,
                production_kernel_changed=False,native_full_period_admitted=False,native_frequency_refinement_admitted=False,
                physical_fidelity=False,real_time=False,maximum_endpoints=20000,estimated_peak_export_bytes=estimate,
                reserve_bytes=2*1024**3,available_free_bytes=shutil.disk_usage(ROOT).free,
                resource_passed=shutil.disk_usage(ROOT).free>estimate+2*1024**3+128*1024**2)
    def save():out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    save()
    if not record['resource_passed']:return
    work.mkdir();source=ROOT/'references-local/vco1-radau-probe01'
    for n in ('fine.rs','linear.rs','vco1_stamp_data.rs','radau.rs'):shutil.copy2(source/n,work/n)
    shutil.copy2(ROOT/'tools/vco1_radau_continuation_runner.rs',work/'runner.rs')
    raw=np.memmap(ROOT/parent['coverage']['path'],dtype='<f8').reshape(-1,542)
    values=raw[-1,6:274].tolist()
    for i in range(2):(work/f'history{i}.txt').write_text(' '.join(format(v,'.17e') for v in values)+'\n',encoding='utf8',newline='\n')
    private={p.relative_to(ROOT).as_posix():sha(p) for p in work.iterdir()}
    private.update({parent['coverage']['path']:parent['coverage']['sha256'],library.relative_to(ROOT).as_posix():sha(library),ref.circuit.op.MODEL:sha(ROOT/ref.circuit.op.MODEL)})
    record['private_input_sha256']=private;record['previous_high']=values[:134];record['previous_low']=values[134:];save()
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];exe=work/'continue.exe';start=time.perf_counter()
    def execute(cmd,tag):
        with (work/(tag+'.stdout')).open('w',encoding='utf8') as so,(work/(tag+'.stderr')).open('w',encoding='utf8') as se:
            process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=so,stderr=se);began=time.monotonic();reason=None
            while process.poll() is None:
                if shutil.disk_usage(ROOT).free<2*1024**3:reason='disk reserve'
                if time.monotonic()-began>180:reason='process budget'
                if reason:process.terminate();process.wait();break
                time.sleep(.25)
        return dict(command=cmd,exit_code=process.returncode,stdout=(work/(tag+'.stdout')).read_text(),stderr=(work/(tag+'.stderr')).read_text(),resource_rejection=reason)
    try:
        build=execute([compiler['path'],'-C','opt-level=2','-C','link-arg=-Wl,--stack,8388608','--edition=2021',str(work/'runner.rs'),'--extern','rf_d_circuit='+str(library),'-o',str(exe)],'compile')
        record['commands'].append(build);save()
        if build['exit_code']:
            record['unchanged_replays'].append(execute(build['command'],'compile-replay'));save();raise ValueError('continuation build')
        for maximum in (262144,131072):
            path=work/f'walk-{maximum}.bin';cmd=[str(exe),'walk',str(path),str(maximum)]
            result=execute(cmd,str(maximum));record['commands'].append(result);save()
            profile=dict(maximum_accepted_half_ticks=maximum,complete=False,actual_intervals=[])
            record['profiles'].append(profile)
            if result['exit_code']:
                if path.exists():
                    original=path.with_suffix('.failed-original.bin');shutil.copy2(path,original)
                    profile['failed_original']=dict(path=original.relative_to(ROOT).as_posix(),sha256=sha(original),bytes=original.stat().st_size)
                save();replay=execute(cmd,str(maximum)+'-replay')
                replay.update(source_sha256={n:sha(ROOT/n) for n in before},export_sha256=sha(path) if path.exists() else None)
                record['unchanged_replays'].append(replay);save()
            data=np.memmap(path,dtype='<f8').reshape(-1,542)
            if len(data)<2:raise ValueError('no complete accepted interval')
            if not np.isfinite(data).all() or not np.array_equal(np.diff(data[:,0]),data[1:,1]) or np.max(data[:,2:5])>1 or np.min(data[1:,1])<4 or np.max(data[1:,1])>maximum:raise ValueError('whole continuation clock/gates')
            for column in (6,274):
                hi=data[:,column:column+134];lo=data[:,column+134:column+268]
                if not np.array_equal(hi+lo,hi) or np.any(np.abs(lo)>np.abs(np.spacing(hi))/2) or np.max(np.abs(hi[:,:98]))>40 or np.max(np.abs(hi[:,98:]))>1:raise ValueError('whole continuation memory/domain')
            ramp=data[:,49];cross=np.flatnonzero((ramp[:-1]<-2)&(ramp[1:]>=-2));edges=[float((data[k,0]+(-2-ramp[k])/(ramp[k+1]-ramp[k])*(data[k+1,0]-data[k,0]))*TICK) for k in cross]
            profile['coverage']=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),rows=len(data),columns=542,
                     elapsed_s=float(data[-1,0]*TICK),minimum_actual_dt_s=float(data[1:,1].min()*TICK),maximum_actual_dt_s=float(data[1:,1].max()*TICK),
                     max_residual_ratio=float(data[:,2].max()),max_correction_ratio=float(data[:,3].max()),max_error_ratio=float(data[:,4].max()),
                     ramp_min_v=float(ramp.min()),ramp_max_v=float(ramp.max()),ramp_minus2_rising_crossings_s=edges)
            save();print('Radau continuation',maximum,profile['coverage'],flush=True)
            changes=np.max(np.abs(np.diff(data[:,6:104],axis=0)),axis=1)
            indices=sorted(set([1,len(data)-1,*list(np.argsort(changes)[-2:]+1)]))
            with localcontext() as ctx:
                ctx.prec=100
                for k in indices:
                    previous=data[k-1];now=data[k];old=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(previous[6:140],previous[140:274])]
                    h=float(now[1]*TICK);pair=ref.solve(old,h,C);parts={}
                    for i,(part,column) in enumerate((('stage',274),('endpoint',6))):
                        high=now[column:column+134].tolist();low=now[column+134:column+268].tolist()
                        candidate=[Decimal.from_float(v)+Decimal.from_float(w) for v,w in zip(high,low)];error=[abs(v-w) for v,w in zip(candidate,pair[part])]
                        residual=pair['residual'][134*i:134*(i+1)];ground=pair['ground'][i]
                        ok=max(error[:98])<=Decimal.from_float(2e-7) and max(error[98:])<=Decimal.from_float(2e-10) and max(map(abs,residual[:98]))<=Decimal.from_float(2e-14) and max(map(abs,residual[98:]))<=Decimal.from_float(2e-12) and abs(sum(residual[:98])+ground)<=Decimal.from_float(1e-11)
                        parts[part]=dict(native=dict(high=high,low=low,residual_ratio=float(now[2]),correction_ratio=float(now[3])),independent_decimal=list(map(str,pair[part])),max_node_error_v=float(max(error[:98])),max_branch_error_a=float(max(error[98:])),passed=ok)
                    profile['actual_intervals'].append(dict(row_index=int(k),dt_s=h,previous_high=previous[6:140].tolist(),previous_low=previous[140:274].tolist(),roots=parts));save()
                    if not all(p['passed'] for p in parts.values()):raise ValueError('actual continuation interval contrast')
            profile['complete']=result['exit_code']==0 and abs(profile['coverage']['elapsed_s']-.003)<1e-17
            save()
            if not profile['complete']:raise ValueError('conditional continuation rejected; campaign stopped')
        record['passed']=len(record['profiles'])==2 and all(p['complete'] for p in record['profiles'])
    except Exception as exc:record['error']=repr(exc)
    record.update(source_sha256_after={n:sha(ROOT/n) for n in before},private_input_sha256_after={n:sha(ROOT/n) for n in private},
                  outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in work.iterdir() if p.is_file()],wall_s=time.perf_counter()-start)
    record['passed']=record['passed'] and before==record['source_sha256_after'] and private==record['private_input_sha256_after'];save()
    print('Radau 3 ms campaign',record['passed'],record.get('error',''),flush=True)


if __name__=='__main__':main()
