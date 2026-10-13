"""Confirm a noisy measurement with the exact executable and packet."""
import json,subprocess,time
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require
def main():
 exe='references-local/lu-extent-bench01/bench.exe';packet='references-local/newton-reuse-inputs01/pairs.bin';names=['tools/repeat_lu_extent_bench.py','docs/LU_EXTENSION_CONFIRMACION.md'];sources={n:sha(ROOT/n) for n in names};private={n:sha(ROOT/n) for n in [exe,packet]};old=json.loads((ROOT/'evidence/voice_lu_extent_bench_native01.json').read_text(encoding='utf8'));require(old['passed'] and any(p['path']==exe and p['sha256']==private[exe] for p in old['outputs']),'same benchmark');commands=[]
 for attempt in range(2):
  t=time.perf_counter();q=subprocess.run([str(ROOT/exe),str(ROOT/packet)],cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=300,creationflags=subprocess.CREATE_NO_WINDOW);r=dict(command=[str(ROOT/exe),str(ROOT/packet)],exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,wall_s=time.perf_counter()-t);commands.append(r);write(f'evidence/voice_lu_extent_confirmation_command01-{attempt+1:02d}.json',r)
  if q.returncode==0:break
 require(sources=={n:sha(ROOT/n) for n in sources} and private=={n:sha(ROOT/n) for n in private},'stable confirmation');write('evidence/voice_lu_extent_confirmation01.json',dict(passed=commands[-1]['exit_code']==0 and len(commands)==1,source_sha256=sources,source_sha256_after=sources,private_used_sha256=private,private_used_sha256_after=private,commands=commands));print('LU_CONFIRMATION',commands[-1]['exit_code'])
if __name__=='__main__':main()
