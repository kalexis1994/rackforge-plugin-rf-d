"""Continue an administratively stopped segment with the exact cached caller.
Preserve every receipt/file. Aggregate completed coverage separately; the
original resource stop remains failed. No electrical gate or reserve change.
"""
import argparse,json,os,re,shutil,subprocess,time
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import checkpoint,checkpoints,trace,require,GOAL
from analyze_joint_cycles import summary

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);a=parser.parse_args()
    require(a.attempt>=2,'continuation sequence')
    parents=[f'evidence/voice_joint_cycles_resume{k:02d}.json' for k in range(1,a.attempt)]
    receipts=[json.loads((ROOT/n).read_text()) for n in parents]
    for r in receipts:
        require(r['source_sha256']==r['source_sha256_after'],'unchanged previous segment sources')
        for n,h in r['source_sha256'].items():require(sha(ROOT/n)==h,'previous input '+n)
        for o in r['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'previous output '+o['path'])
    previous=receipts[-1];p=previous['profiles'][0];require(p['exit_code']==1 and p['administrative_stop'] and 'ADMINISTRATIVE_BUDGET' in p['stderr'] and 'ENGINE_REJECT' not in p['stderr'],'only administrative continuation')
    native=json.loads((ROOT/'evidence/voice_joint_cycles_native01.json').read_text())
    completed=int(summary(native['profiles'][1]['stderr'])['intervals'])+sum(int(summary(r['profiles'][0]['stderr'])['intervals']) for r in receipts)
    restore=Path(p['command'][3])/'final.ckp';old=checkpoint(restore.read_bytes());remaining=48000-completed
    exe=Path(receipts[0]['profiles'][0]['command'][0]);require(old['ticks']<GOAL and remaining>0,'remaining coverage')
    out=ROOT/f'evidence/voice_joint_cycles_resume{a.attempt:02d}.json';work=ROOT/f'references-local/joint-cycles-resume{a.attempt:02d}';require(not out.exists() and not work.exists(),'new segment')
    names=['tools/continue_joint_cycles.py','tools/joint_cycles_resume_runner.rs','tools/joint_cycles_analysis.py','tools/analyze_joint_cycles.py','docs/VOZ_PRIMER_CICLO_RECURSOS.md','evidence/voice_joint_cycles_native01.json',*parents,exe.relative_to(ROOT).as_posix(),restore.relative_to(ROOT).as_posix()]
    hashes={n:sha(ROOT/n) for n in names};free=shutil.disk_usage(ROOT).free
    report=dict(schema='rf-d/joint-cycles-continuation/v1',passed=False,source_sha256=hashes,compiler=previous['compiler'],commands=[],replays=[],profiles=[],outputs=[],available_free_bytes=free,reserve_bytes=1024**3,estimated_output_bytes=12*1024**2,process_budget_s=1800,global_budget_s=2100,lab_stack_bytes=33554432,preserved_prefix_ticks=old['ticks'],preserved_prefix_intervals=completed,remaining_interval_budget=remaining,cached_caller_sha256=sha(exe),earlier_segment_receipts=parents)
    def write():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    write();require(free>=report['reserve_bytes']+report['estimated_output_bytes'],'same reserve, remaining writes preflight')
    work.mkdir();directory=work/'32768';directory.mkdir();command=[str(exe),'run','32768',str(directory),str(remaining),str(restore)]
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];env['RUST_MIN_STACK']='33554432'
    started=time.perf_counter();minimum=free;administrative=False
    with (directory/'stdout.txt').open('wb') as stdout,(directory/'stderr.txt').open('wb') as stderr:
        child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
        while child.poll() is None:
            space=shutil.disk_usage(ROOT).free;minimum=min(minimum,space)
            if space<report['reserve_bytes'] or time.perf_counter()-started>1810:(work/'stop.flag').write_text('resource stop\n');administrative=True
            if time.perf_counter()-started>1830:child.terminate();administrative=True
            time.sleep(.25)
    text=(directory/'stderr.txt').read_text();profile=dict(maximum_half_ticks=32768,interval_budget=remaining,command=command,exit_code=child.returncode,wall_s=time.perf_counter()-started,stderr=text,stdout=(directory/'stdout.txt').read_text(),minimum_free_bytes=minimum,administrative_stop=administrative)
    report['profiles'].append(profile)
    if child.returncode:
        report['failed_source_text']={n:(ROOT/n).read_text() for n in names if n.endswith(('.rs','.py'))}
        match=re.search(r'FAILURE,target_ticks=(\d+),reason=ENGINE_REJECT',text)
        if match:
            replay=[str(exe),'replay',str(directory/'final.ckp'),match[1]];r=subprocess.run(replay,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
            report['replays'].append(dict(command=replay,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        else:report['replay_pending']='preserved administrative or observation failure; do not replay an unchanged prefix'
    report['outputs']=[dict(path=f.relative_to(ROOT).as_posix(),sha256=sha(f),bytes=f.stat().st_size) for f in sorted(work.rglob('*')) if f.is_file()]
    report['source_sha256_after']={n:sha(ROOT/n) for n in names};report['wall_s']=time.perf_counter()-started
    report['passed']=child.returncode==0 and not administrative and minimum>=report['reserve_bytes'] and hashes==report['source_sha256_after'] and report['wall_s']<=1800
    write();print(text[-1500:]);print('CYCLES_CONTINUATION',a.attempt,report['passed'],flush=True)
    if report['passed']:
        aggregate=ROOT/f'evidence/voice_joint_cycles_continuations{a.attempt:02d}.json';require(not aggregate.exists(),'new aggregate')
        profiles=[r['profiles'][0] for r in [*receipts,report]];last=checkpoint((ROOT/'references-local/joint-cycles01/32768/final.ckp').read_bytes());inputs={}
        for part in profiles:
            d=Path(part['command'][3]);start=checkpoints(d/'checkpoints.bin')[0];require(start==last,'bit-identical continuation seam')
            rows=trace(d/'trace.bin',start_ticks=start['ticks']);last=checkpoint((d/'final.ckp').read_bytes());require(int(rows[-1]['ticks'])==last['ticks'],'complete segment endpoint')
            for n in ['trace.bin','checkpoints.bin','final.ckp','selected.txt','stderr.txt']:
                name=(d/n).relative_to(ROOT).as_posix();inputs[name]=sha(ROOT/name)
        require(last['ticks']==GOAL,'aggregate full clock');sources={n:sha(ROOT/n) for n in ['tools/continue_joint_cycles.py',*parents,out.relative_to(ROOT).as_posix()]}
        result=dict(schema='rf-d/joint-cycles-continuations/v1',passed=True,source_sha256=sources,source_sha256_after=sources,input_sha256=inputs,profiles=profiles,exact_seams=True,failed_segments_preserved=True,resource_guard_interruptions=sum(r['profiles'][0]['administrative_stop'] for r in receipts),reserve_bytes=1024**3,numerical_gates_changed=False)
        aggregate.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('CYCLES_AGGREGATE',aggregate.name,flush=True)
if __name__=='__main__':main()
