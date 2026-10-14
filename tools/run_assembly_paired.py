"""Compare every accepted public advance, observations, proposals and charge integral."""
import base64,json,os,shutil,subprocess,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from promote_assembly_voice import PAIRED
from joint_cycles_analysis import require
def main():
 work=ROOT/'references-local/voice-assembly-paired01';out='evidence/voice_assembly_paired01.json';require(not work.exists() and not (ROOT/out).exists(),'exclusive paired trajectory');pub=json.loads((ROOT/'evidence/voice_assembly_public01.json').read_text(encoding='utf8'));require(pub['passed'] and pub['cost_utility_passed'],'public bank/cost admitted');inp=json.loads((ROOT/'evidence/voice_assembly_promotion01.json').read_text(encoding='utf8'));names=[PAIRED,'tools/run_assembly_paired.py','tools/promote_assembly_voice.py','evidence/voice_assembly_public01.json','evidence/voice_assembly_promotion01.json','docs/VOZ_ENSAMBLADO_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names};lib='references-local/voice-assembly-public01/librf_d_circuit.rlib';private={lib:sha(ROOT/lib),**{s['path']:s['sha256'] for s in inp['seeds']}};require(private[lib]==next(o['sha256'] for o in pub['outputs'] if o['path']==lib),'measured public library');compiler=pub['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'compiler');require(shutil.disk_usage(ROOT).free>=1024**3+96*1024**2,'reserve');work.mkdir();exe=work/'paired.exe';env=os.environ.copy();env['PATH']='C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;'+env['PATH'];commands=[];profiles=[];replays=[];started=time.perf_counter();r=dict(passed=False,source_sha256=before,private_used_sha256=private,compiler=compiler,new_library_compile=False,new_cargo_cache=False,lab_stack_bytes=33554432,output_budget_bytes=96*1024**2)
 def run(cmd,limit):
  t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',timeout=limit,creationflags=subprocess.CREATE_NO_WINDOW);return dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_s=time.perf_counter()-t)
 try:
  cmd=[compiler['path'],'--edition=2021','-C','opt-level=2','-C','strip=symbols','-C','link-arg=-Wl,--stack,33554432',PAIRED,'--extern','rf_d_circuit='+str(ROOT/lib),'-o',str(exe)];q=run(cmd,120);commands.append(q)
  if q['exit_code']:replays.append(run(cmd,120));require(False,'paired compile rejected')
  for s in inp['seeds']:
   maximum=s['maximum_half_ticks'];cmd=[str(exe),str(ROOT/s['path']),str(work/str(maximum))];p=run(cmd,900);profiles.append(dict(maximum_half_ticks=maximum,**p));print('ASSEMBLY_PAIRED_PROFILE',maximum,p['exit_code'],p['stderr'][-300:],flush=True)
   if p['exit_code']:replays.append(run(cmd[:-1]+[str(work/('rejected-replay-'+str(maximum)))],900));require(False,'complete paired history rejected')
  require(time.perf_counter()-started<=1900,'campaign wall budget');r.update(passed=True,every_accepted_bits_identical=True,public_family=True,new_circuit_duration_s=0,new_audio=False,physical_fidelity=False,real_time=False)
 except Exception:r['failure']=traceback.format_exc();r['failed_source_base64']={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names if n.endswith(('.py','.rs'))}
 r.update(commands=commands,profiles=profiles,replays=replays,wall_s=time.perf_counter()-started,source_sha256_after={n:sha(ROOT/n) for n in names},private_used_sha256_after={n:sha(ROOT/n) for n in private},outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.rglob('*')) if p.is_file()]);require(before==r['source_sha256_after'] and private==r['private_used_sha256_after'],'stable paired inputs');write(out,r);print('ASSEMBLY_PAIRED',r['passed'],r.get('failure',''),flush=True);require(r['passed'],'assembly paired public history')
if __name__=='__main__':main()
