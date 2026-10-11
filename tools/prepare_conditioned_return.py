"""Freeze root/basis, two prefix sensitivities and complete saved calendar."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from check_history_propagation import Reader,bits
from joint_cycles_analysis import trace,require
from prepare_history_propagation import OBS

POINTS=[0,1,2,64,256,1024,4096,8192,12288,16384,20186,20187,20188,20189,24576,32768,40960,42541,42542,42543]
FIXTURES=[0,1,20188,20189,42542,42543]
ATTR=b'\n/tools/conditioned_return_tail.rs text eol=lf\n/tools/joint_conditioned_return_runner.rs text eol=lf\n/tools/joint_conditioned_return_event.rs text eol=lf\n'

def event_adapter():
    return (ROOT/'tools/joint_history_event.rs').read_text().replace('crate::joint_history_propagation','crate::joint_charge_basis_propagation')

def main():
    previous='evidence/voice_charge_basis_tests01.json';qa=json.loads((ROOT/previous).read_text());require(qa['passed'],'previous QA');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='35d7ee6ad97510c32ccbd7756563b56356548c25','base')
    write('evidence/voice_conditioned_return_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    header=(ROOT/'tools/joint_charge_corrected_runner.rs').read_text().split('fn run()->Result<(),String>')[0]
    for name,data in [('tools/joint_conditioned_return_runner.rs',header+(ROOT/'tools/conditioned_return_tail.rs').read_text()),('tools/joint_conditioned_return_event.rs',event_adapter())]:
        p=ROOT/name;require(not p.exists(),'exclusive source');p.write_text(data,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR)
    names=['references-local/charge-basis01/basis.bin','references-local/joint-corrected-cycles01/0-65536/trace.bin','references-local/joint-corrected-cycles01/0-65536/selected.txt'];private={}
    for name in names:require(sha(ROOT/name)==qa['private_input_sha256'][name],'protected input');private[name]=sha(ROOT/name)
    b=Reader(ROOT/names[0]);require(b.bytes(8)==b'RFJCBO01' and b.integer('I')==0,'memory0 basis');root=b.floats(436);metrics=b.floats(5);basis=b.floats(3924);prefix=[]
    for _ in range(2):prefix.append((b.integer('Q'),b.integer('I'),b.floats(2000),b.floats(7200)))
    rows=trace(ROOT/names[1])[:42544];require(len(rows)==42544,'full length');lines=(ROOT/names[2]).read_text().splitlines();raw=[]
    for i,line in enumerate(lines):
        if line.startswith('JOINT_ROOT,'):raw.append([list(map(float,s.split(',')[1:])) for s in lines[i+1:i+6]])
    fixtures=[raw[k] for k in [1,2,4,5,7,8]]
    for i in range(2):require(bits(prefix[i][2],__import__('numpy').array(fixtures[i]).ravel()),'prefix fixture consistency')
    p=ROOT/'references-local/conditioned-return-inputs01.bin';require(not p.exists(),'exclusive input')
    with p.open('xb') as f:
        f.write(b'RFJCRIN1'+struct.pack('<I',len(rows)));f.write(root.tobytes());f.write(basis.tobytes())
        for a in fixtures:f.write(struct.pack('<2000d',*[v for s in a for v in s]))
        for _,_,_,s in prefix:f.write(s.tobytes())
        f.write(struct.pack('<I20I',len(POINTS),*POINTS))
        for row in rows:f.write(struct.pack('<QI7d',int(row['ticks']),int(row['half_ticks']),*[float(row[key]) for key,_ in OBS]))
    write('evidence/voice_conditioned_return_inputs01.json',dict(passed=True,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),private_used_sha256=private,steps=len(rows),end_ticks=int(rows[-1]['ticks']),points=POINTS,fixture_steps=FIXTURES,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_conditioned_return.py','tools/conditioned_return_tail.rs','tools/joint_charge_corrected_runner.rs','tools/joint_history_event.rs','docs/VOZ_RETORNO_CONDICIONADO_PROTOCOLO.md']}));print('CONDITIONED_INPUTS',len(rows),p.stat().st_size,flush=True)
if __name__=='__main__':main()
