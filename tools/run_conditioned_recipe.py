"""Run the standalone public recipe example and compare every exported bit."""
import argparse,base64,json,os,shutil,struct,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def compare(directory,old):
    lines=(old/'selected.txt').read_text(encoding='utf8').splitlines()
    initial=list(map(float,lines[1].split(',')[1:]))
    expected=bytearray(b'RFJ7TR01')
    expected.extend(struct.pack('<Q5d',4423942144,*[initial[i]+initial[229+i] for i in [194,46,43,12,39]]))
    steps=bytearray(b'RFSTPS01');grids=bytearray(b'RFGRID01')
    grids.extend(struct.pack('<Q458d',4423942144,*initial))
    count=0
    for i,line in enumerate(lines):
        v=line.split(',')
        if v[0]=='OBS':
            floats=list(map(float,v[1:]));expected.extend(struct.pack('<Q5d',int(v[1]),*[floats[j] for j in [4,15,16,17,18]]));count+=1
        elif v[0]=='STEP':steps.extend(struct.pack('<QQIIdI',int(v[2]),int(v[3]),int(v[4]),int(v[6]),float(v[5]),int(v[7])))
        elif v[0]=='GRID':grids.extend(struct.pack('<Q458d',int(v[2]),*map(float,lines[i+1].split(',')[1:])))
    for name,raw in [('j7.bin',expected),('steps.bin',steps),('grids.bin',grids)]:
        require((directory/name).read_bytes()==raw,'full exported bits '+name)
    events='EVENT,0,4423942144,0,false\nEVENT,1,4426039296,10,true\nEVENT,2,5212471296,0,false\n'
    require((directory/'events.txt').read_text(encoding='utf8')==events,'event clocks/values')
    return dict(fine_endpoints=count,accepted_steps=count//2,complete_grid_states=12,
        observable_bit_fields=5*(count+1),state_bit_fields=12*458,
        expected_source_sha256=sha(old/'selected.txt'),all_exported_bits_identical=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args()
    tag=f'{args.attempt:02d}';work=ROOT/f'references-local/conditioned-recipe-render{tag}'
    out=f'evidence/voice_conditioned_recipe_native{tag}.json'
    require(not work.exists() and not (ROOT/out).exists(),'exclusive campaign')
    require(shutil.disk_usage(ROOT).free>=1024**3+32*1024**2,'reserve')
    library='evidence/voice_conditioned_recipe_library02.json';build=json.loads((ROOT/library).read_text(encoding='utf8'))
    require(build['passed'],'library')
    tests=['evidence/voice_conditioned_recipe_'+n+'tests04.json' for n in ['conditioned_recipe','conditioned_portable']]
    require(all(json.loads((ROOT/n).read_text(encoding='utf8'))['passed'] for n in tests),'native tests')
    source='crates/rf-d-circuit/examples/conditioned_render.rs'
    names=[source,'tools/run_conditioned_recipe.py','docs/RECETA_CONDICIONADA_PROTOCOLO.md',library]+tests
    names+=['crates/rf-d-circuit/src/'+n+'.rs' for n in ['conditioned_recipe','conditioned_recipe_seed']]
    before={n:sha(ROOT/n) for n in names}
    lib='references-local/conditioned-recipe-library02/librf_d_circuit.rlib'
    originals={f'{on}-{maximum}':ROOT/f'references-local/conditioned-portable-cycle01/{on}-{maximum}' for on in [1,0] for maximum in [1048576,524288]}
    private={lib:sha(ROOT/lib),**{(p/'selected.txt').relative_to(ROOT).as_posix():sha(p/'selected.txt') for p in originals.values()}}
    require(private[lib]==next(q['sha256'] for q in build['outputs'] if q['path']==lib),'library identity')
    compiler=build['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler')
    env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH']
    work.mkdir();exe=work/'render.exe';commands=[];profiles=[];replays=[];started=time.perf_counter()
    r=dict(passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,
        reserve_bytes=1024**3,output_budget_bytes=32*1024**2,lab_stack_bytes=33554432,
        own_synthetic_history=True,simulated_window_s=.003004,new_extended_duration_s=0,
        independent_graph_reexecuted=False,real_time=False,physical_fidelity=False)
    def run(cmd,limit):
        t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW)
        return dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
    try:
        cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',source,'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)]
        c=run(cmd,120);commands.append(c)
        if c['exit_code']:replays.append(run(cmd,120));require(False,'compile rejection')
        for tag,original in originals.items():
            on,maximum=map(int,tag.split('-'));directory=work/tag
            cmd=[str(exe),'on' if on else 'off','1' if maximum==524288 else '2',str(directory)]
            q=run(cmd,990);profiles.append(dict(tag=tag,**q));print('RECIPE_PROFILE',tag,q['exit_code'],q['stdout'].strip(),flush=True)
            if q['exit_code']:replays.append(run(cmd[:-1]+[str(work/('failed-replay-'+tag))],990));require(False,'render rejection')
            profiles[-1].update(compare(directory,original))
        tag='1-524288';cmd=[str(exe),'on','1',str(work/'replay-1-524288')];q=run(cmd,990);replays.append(q)
        require(q['exit_code']==0,'native replay')
        for name in ['j7.bin','steps.bin','grids.bin','events.txt']:require((work/tag/name).read_bytes()==(work/'replay-1-524288'/name).read_bytes(),'identical replay '+name)
        require(time.perf_counter()-started<=4000,'campaign wall');r.update(passed=True,identical_replay=True)
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
        # If an adapter failed after a native success, preserve data and rerun
        # the unchanged adapter once before any source repair.
        if profiles and profiles[-1]['exit_code']==0:
            tag=profiles[-1]['tag']
            try:compare(work/tag,originals[tag]);r['adapter_replay']='passed'
            except Exception:r['adapter_replay']=traceback.format_exc()
    r.update(commands=commands,profiles=profiles,replays=replays,wall_s=time.perf_counter()-started,
        source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},
        outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()])
    require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable inputs')
    write(out,r);print('RECIPE_NATIVE',r['passed'],r['wall_s'],r.get('failure',''),flush=True)
    require(r['passed'],'native campaign')
if __name__=='__main__':main()
