"""Bounded every-Accepted identity campaign, with frozen baseline library."""
import argparse,base64,json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from prepare_voice_paired import paired,engine
from prepare_voice_block import block_kernel
from joint_cycles_analysis import require

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--public',action='store_true');parser.add_argument('--attempt',type=int,default=1);args=parser.parse_args();kind='portable' if args.public else 'paired';work=ROOT/f'references-local/voice-block-{kind}{args.attempt:02d}';out=f'evidence/voice_block_{kind}{args.attempt:02d}.json';require(not work.exists() and not (ROOT/out).exists(),'exclusive paired campaign')
 if args.public:src='crates/rf-d-circuit/examples/block_decay_verify.rs';lib='references-local/voice-block-library01/librf_d_circuit.rlib'
 else:src='tools/voice_pivot_paired.rs';lib='references-local/decay-voice02/librf_d_circuit.rlib'
 require((ROOT/src).read_text(encoding='utf8')==paired(args.public),'declared paired caller');require((ROOT/'tools/voice_block_engine.rs').read_text(encoding='utf8')==engine() and (ROOT/'tools/voice_block_kernel.rs').read_text(encoding='utf8')==block_kernel(),'declared candidate')
 bench=json.loads((ROOT/'evidence/voice_block_bench01.json').read_text(encoding='utf8'));require(bench['passed'] and bench['cost_utility_passed'],'bank/utility admission');old=json.loads((ROOT/'evidence/voice_decay_tests01.json').read_text(encoding='utf8'));require(old['passed'],'admitted baseline')
 names=[src,'tools/run_voice_paired.py','tools/prepare_voice_paired.py','tools/prepare_voice_block.py','tools/voice_block_kernel.rs','tools/voice_block_engine.rs','docs/VOZ_COSTO_PIVOTE_PROTOCOLO.md','docs/VOZ_COSTO_BLOQUES_PROTOCOLO.md','evidence/voice_block_bench01.json'];sources={n:sha(ROOT/n) for n in names};private={lib:sha(ROOT/lib)}
 for maximum in [1048576,524288]:
  n=f'references-local/decay-voice02/{maximum}/phase0-start.ckp';require(sha(ROOT/n)==old['private_input_sha256'][n],'own control history');private[n]=sha(ROOT/n)
 compiler=json.loads((ROOT/'evidence/voice_decay_native02.json').read_text(encoding='utf8'))['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');require(shutil.disk_usage(ROOT).free>=1024**3+96*1024**2,'budget/reserve');work.mkdir();exe=work/'paired.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];profiles=[];replays=[];started=time.perf_counter();r=dict(passed=False,source_sha256=sources,private_used_sha256=private,compiler=compiler,new_library_compile=False,new_cargo_cache=False,lab_stack_bytes=33554432,public=args.public)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);return dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
 try:
  cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',src,'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)];c=run(cmd,120);commands.append(c)
  if c['exit_code']:replays.append(run(cmd,120));require(False,'paired compile rejected')
  for maximum in [1048576,524288]:
   cmd=[str(exe),str(ROOT/f'references-local/decay-voice02/{maximum}/phase0-start.ckp'),str(work/str(maximum))];p=run(cmd,900);profiles.append(dict(maximum_half_ticks=maximum,**p));print('PAIRED_PROFILE',kind,maximum,p['exit_code'],p['stderr'][-220:],flush=True)
   if p['exit_code']:replays.append(run(cmd[:-1]+[str(work/('rejected-replay-'+str(maximum)))],900));require(False,'paired trajectory rejected')
   require((work/str(maximum)/'baseline.txt').read_bytes()==(work/str(maximum)/'candidate.txt').read_bytes(),'all exported bits')
  require(time.perf_counter()-started<=1900,'paired wall budget');r['passed']=True
 except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith(('.py','.rs'))}
 r.update(commands=commands,profiles=profiles,replays=replays,wall_s=time.perf_counter()-started,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()]);require(sources==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable paired campaign');write(out,r);print('PAIRED_NATIVE',kind,r['passed'],r['wall_s'],r.get('failure',''));require(r['passed'],'every-Accepted paired campaign')
if __name__=='__main__':main()
