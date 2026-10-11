"""One real complete clock interval and four exact bracket fixtures."""
import base64,json,struct,subprocess
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_joint_cycles import bank
from joint_cycles_analysis import trace,require
from prepare_history_propagation import OBS
def main():
    previous='evidence/voice_history_event_tests01.json';qa=json.loads((ROOT/previous).read_text());require(qa['passed'],'previous admission');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='44fd35a5ff72873a8ab8cb30a28ff7a5bbd2c2e4','base')
    mutable=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'];write('evidence/voice_return_interval_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
    directory=ROOT/'references-local/joint-corrected-cycles01/0-65536';private={}
    for file in ['selected.txt','trace.bin']:
        p=directory/file;name=p.relative_to(ROOT).as_posix();require(sha(p)==qa['private_input_sha256'][name],'frozen input');private[name]=sha(p)
    cases=bank(directory/'selected.txt');rows=trace(directory/'trace.bin');indices=[]
    for index in [4,7]:
        endpoint=cases[index][1];found=np.ones(len(rows),dtype=bool)
        for name,k in OBS:found&=rows[name]==endpoint[k]+endpoint[200+k]
        match=np.flatnonzero(found);require(len(match)==1,'unique bracket');indices.append(int(match[0]))
    begin,end=indices[0],indices[1]+2;schedule=rows[begin:end];require(len(schedule)==22356,'declared full interval');start=int(schedule[0]['ticks'])-int(schedule[0]['half_ticks']);lines=(directory/'selected.txt').read_text().splitlines();raw=[]
    for i,line in enumerate(lines):
        if line.startswith('JOINT_ROOT,'):raw.append([list(map(float,s.split(',')[1:])) for s in lines[i+1:i+6]])
    n=len(schedule);points=[0,1,2,64,256,1024,4096,8192,12288,16384,20480,n-4,n-3,n-2,n-1];target=ROOT/'references-local/return-interval-inputs01.bin';require(not target.exists(),'exclusive interval input')
    with target.open('xb') as f:
        f.write(b'RFJFINT1'+struct.pack('<IQ',n,start));f.write(struct.pack('<400d',*raw[3][0]));
        for index in [4,5,7,8]:f.write(struct.pack('<2000d',*[v for state in raw[index] for v in state]))
        f.write(struct.pack('<I15I',len(points),*points))
        for row in schedule:f.write(struct.pack('<QI7d',int(row['ticks']),int(row['half_ticks']),*[float(row[name]) for name,_ in OBS]))
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_return_interval_runner.rs text eol=lf\n')
    write('evidence/voice_return_interval_inputs01.json',dict(passed=True,path=target.relative_to(ROOT).as_posix(),sha256=sha(target),private_used_sha256=private,steps=n,start_ticks=start,end_ticks=int(schedule[-1]['ticks']),trace_begin_row=begin,trace_end_row=end,points=points,source_sha256={name:sha(ROOT/name) for name in ['tools/prepare_return_interval.py','docs/VOZ_INTERVALO_RETORNO_PROTOCOLO.md']}));print('RETURN_INPUTS',n,target.stat().st_size)
if __name__=='__main__':main()
