"""Resume each own229 checkpoint without restarting adaptive proposal/history."""
import base64,json,struct,subprocess
from decimal import localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_contour_reset import checkpoint
from joint_cycles_analysis import require
START=4423942144;BOUNDARIES=[0,2097152,788529152,1574961152];CUT=157286400
KEY=[0.,10.,0.];SHORT=[False,True,False];MAXIMUM=[1048576,524288]
ATTR=b'\n/tools/joint_contour_cycle_body.rs text eol=lf\n/tools/joint_contour_cycle_runner.rs text eol=lf\n'
def body():return (ROOT/'tools/joint_contour_reset_body.rs').read_text(encoding='utf8').replace('START:u64=2848980992','START:u64=4423942144').replace('RFMCTR01','RFCYCT01')
def caller():return (ROOT/'tools/joint_contour_reset_runner.rs').read_text(encoding='utf8').split('// All IO')[0]+body()
def main():
 previous='evidence/voice_contour_reset_tests01.json';old=json.loads((ROOT/previous).read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='107a9b461d703b917befaf8745329380f0df5d7a','base');write('evidence/voice_contour_cycle_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}));work=ROOT/'references-local/contour-cycle-inputs01';require(not work.exists(),'exclusive inputs');work.mkdir();seeds=[]
 for on in [True,False]:
  for maximum in MAXIMUM:
   origin=f'references-local/contour-reset01/{int(on)}-{maximum}/final.ckp';require(sha(ROOT/origin)==old['private_input_sha256'][origin],'own229 seed')
   with localcontext() as ctx:ctx.prec=100;cp=checkpoint((ROOT/origin).read_bytes())
   require(cp['ticks']==START and cp['key']==0. and not cp['short'] and cp['maximum']==maximum,'calendar/recipe');raw=bytearray((ROOT/origin).read_bytes());raw[:8]=b'RFCYCT01';raw[28:32]=struct.pack('<I',0);p=work/f'{int(on)}-{maximum}.ckp';p.write_bytes(raw);seeds.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),origin_path=origin,origin_sha256=sha(ROOT/origin),final_decay=on,maximum_half_ticks=maximum,inherited_next_full_ticks=cp['next_full']))
 for n,s in [('tools/joint_contour_cycle_body.rs',body()),('tools/joint_contour_cycle_runner.rs',caller())]:
  p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);names=['tools/prepare_contour_cycle.py','tools/joint_contour_cycle_body.rs','tools/joint_contour_cycle_runner.rs','tools/contour_reset_engine.rs','tools/joint_contour_reset_body.rs','tools/joint_latch_kernel.rs','tools/latch_charge_driver.rs','tools/contour_closed_driver.rs','docs/VOZ_CONTORNO_CICLO_PROTOCOLO.md'];write('evidence/voice_contour_cycle_inputs01.json',dict(passed=True,start_ticks=START,boundaries_relative_ticks=BOUNDARIES,keyboard=KEY,short_states=SHORT,seeds=seeds,maximum_half_ticks=MAXIMUM,source_sha256={n:sha(ROOT/n) for n in names}));print('CONTOUR_CYCLE_INPUTS',len(seeds))
if __name__=='__main__':main()
