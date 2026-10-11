"""Derive only the RHS width; freeze corrected roots and first two fixtures."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require,trace

def adapter():
    text=(ROOT/'tools/joint_history_propagation.rs').read_text()
    start=text.index('pub fn units(');end=text.index('pub fn propagate(',start);text=text[:start]+text[end:]
    text=text.replace('pub const R:usize=9;','pub const R:usize=18;').replace('pub const COLS:[usize;R]=[43,5,12,139,199,194,157,117,98];\n','').replace('{old_mass,history}','{old_mass}')
    return text

def main():
    previous='evidence/voice_return_interval_tests01.json';qa=json.loads((ROOT/previous).read_text());require(qa['passed'],'previous QA');head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='d0bd3b2b810e2394a21ca42d200faaf1b87e2c7b','base commit')
    write('evidence/voice_charge_basis_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    header=(ROOT/'tools/joint_charge_corrected_runner.rs').read_text();header=header[:header.index('fn run()->Result<(),String>')];tail=(ROOT/'tools/charge_basis_tail.rs').read_text()
    for name,text in [('tools/joint_charge_basis_runner.rs',header+tail),('tools/joint_charge_basis_propagation.rs',adapter())]:
        p=ROOT/name;require(not p.exists(),'exclusive source');p.write_text(text,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/charge_basis_tail.rs text eol=lf\n/tools/joint_charge_basis_runner.rs text eol=lf\n/tools/joint_charge_basis_propagation.rs text eol=lf\n')
    lines=json.loads((ROOT/'evidence/voice_joint_charge_corrected_native01.json').read_text())['commands'][-1]['stdout'].splitlines();roots={}
    for i,line in enumerate(lines):
        if line.startswith('CHARGE_ROOT,'):
            id,guess=map(int,line.split(',')[1:3])
            if guess==0:roots[id]=[list(map(float,lines[i+j].split(',')[1:])) for j in [1,2]]
    require(set(roots)=={0,1},'two corrected roots');p=ROOT/'references-local/charge-basis-inputs01.bin';require(not p.exists(),'exclusive inputs');private={};profiles=[]
    with p.open('xb') as f:
        f.write(b'RFJCBIN1')
        for id in range(2):
            f.write(struct.pack('<436d',*roots[id][0],*roots[id][1]));directory=ROOT/f'references-local/joint-corrected-cycles01/{id}-65536'
            for file in ['trace.bin','selected.txt']:
                name=(directory/file).relative_to(ROOT).as_posix();require(sha(ROOT/name)==qa['private_input_sha256'][name],'protected fixture');private[name]=sha(ROOT/name)
            rows=trace(directory/'trace.bin')[:2];lines=(directory/'selected.txt').read_text().splitlines();cases=[]
            for i,line in enumerate(lines):
                if line.startswith('JOINT_ROOT,'):cases.append([list(map(float,a.split(',')[1:])) for a in lines[i+1:i+6]])
            clocks=[]
            for row,states in zip(rows,cases[1:3]):
                ticks=int(row['ticks']);half=int(row['half_ticks']);f.write(struct.pack('<QI2000d',ticks,half,*[v for state in states for v in state]));clocks.append([ticks,half])
            profiles.append(dict(id=id,clocks=clocks))
    write('evidence/voice_charge_basis_inputs01.json',dict(passed=True,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),profiles=profiles,private_used_sha256=private,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_charge_basis.py','tools/charge_basis_tail.rs','tools/joint_charge_corrected_runner.rs','evidence/voice_joint_charge_corrected_native01.json','evidence/voice_joint_charge_response_targets01.txt','docs/VOZ_BASE_CARGAS_CORREGIDAS_PROTOCOLO.md']}));print('CHARGE_BASIS_INPUTS',p.stat().st_size)
if __name__=='__main__':main()
