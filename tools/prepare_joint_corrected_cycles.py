"""Derive an identical caller and new orchestration for corrected histories."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require,checkpoint

def caller():return (ROOT/'tools/joint_seed_cycles_runner.rs').read_text(encoding='utf8')

def substitute(text,changes):
    for a,b in changes:require(a in text,'declared substitution '+a);text=text.replace(a,b)
    return text

def runner():
    return substitute((ROOT/'tools/run_joint_seed_cycles.py').read_text(encoding='utf8'),[
      ('voice_joint_charge_seed_native02.json','voice_joint_charge_corrected_native01.json'),('voice_joint_charge_seed_tests01.json','voice_joint_charge_response_tests01.json'),('voice_joint_seed_cycles_inputs01.json','voice_joint_corrected_cycles_inputs01.json'),('voice_joint_seed_cycles_native','voice_joint_corrected_cycles_native'),('joint-seed-cycles','joint-corrected-cycles'),('tools/run_joint_seed_cycles.py','tools/run_joint_corrected_cycles.py'),('tools/prepare_joint_seed_cycles.py','tools/prepare_joint_corrected_cycles.py'),('tools/joint_seed_cycles_runner.rs','tools/joint_corrected_cycles_runner.rs'),('docs/VOZ_CICLOS_SEMILLAS_PROTOCOLO.md','docs/VOZ_CICLOS_CORREGIDOS_PROTOCOLO.md')])

def checker():
    return substitute((ROOT/'tools/check_joint_seed_cycles.py').read_text(encoding='utf8'),[
      ('voice_joint_charge_seed_native02.json','voice_joint_charge_corrected_native01.json'),('voice_joint_seed_cycles_inputs01.json','voice_joint_corrected_cycles_inputs01.json'),('voice_joint_seed_cycles_native01.json','voice_joint_corrected_cycles_native01.json'),('voice_joint_seed_cycles_reference{a.attempt:02d}.json','voice_joint_corrected_cycles_reference{a.attempt:02d}.json'),('tools/check_joint_seed_cycles.py','tools/check_joint_corrected_cycles.py'),('docs/VOZ_CICLOS_SEMILLAS_PROTOCOLO.md','docs/VOZ_CICLOS_CORREGIDOS_PROTOCOLO.md')])

def validator():
    text=(ROOT/'tools/validate_joint_seed_cycles.py').read_text(encoding='utf8');start=text.index('    rail_before=');end=text.index('    for n,h in old[',start);text=text[:start]+text[end:]
    start=text.index('    require((ROOT/\'.gitattributes\')');end=text.index('    inputs=read(',start)
    text=text[:start]+"    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\\n/tools/joint_corrected_cycles_runner.rs text eol=lf\\n','only lab caller attribute');require((ROOT/'tools/joint_corrected_cycles_runner.rs').read_bytes()==caller().encode(),'byte-identical lab caller')\n    from prepare_joint_corrected_cycles import runner,checker\n    require((ROOT/'tools/run_joint_corrected_cycles.py').read_bytes()==runner().encode() and (ROOT/'tools/check_joint_corrected_cycles.py').read_bytes()==checker().encode(),'declared wrappers')\n"+text[end:]
    return substitute(text,[('from prepare_joint_seed_cycles import caller','from prepare_joint_corrected_cycles import caller'),('voice_joint_charge_seed_tests01.json','voice_joint_charge_response_tests01.json'),('voice_joint_seed_cycles_before01.json','voice_joint_corrected_cycles_before01.json'),('voice_joint_seed_cycles_inputs01.json','voice_joint_corrected_cycles_inputs01.json'),('voice_joint_seed_cycles_native01.json','voice_joint_corrected_cycles_native01.json'),('voice_joint_seed_cycles_reference01.json','voice_joint_corrected_cycles_reference01.json'),('voice_joint_seed_cycles_tests01.json','voice_joint_corrected_cycles_tests01.json'),('voice_joint_seed_cycles_qa_failure','voice_joint_corrected_cycles_qa_failure'),('tools/validate_joint_seed_cycles.py','tools/validate_joint_corrected_cycles.py'),('cache_allocation_reclaimed_bytes=sum(r[\'allocation_reclaimed_bytes\'] for r in compression)','cache_allocation_reclaimed_bytes=0')])

def main():
    previous='evidence/voice_joint_charge_response_tests01.json';q=json.loads((ROOT/previous).read_text());require(q['passed'],'previous release')
    for key in ['source_sha256','private_input_sha256']:
        for n,h in q[key].items():require(sha(ROOT/n)==h,'protected '+n)
    names=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','.gitattributes'];payload=dict(schema='rf-d/joint-corrected-cycles-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names})
    before='evidence/voice_joint_corrected_cycles_before01.json'
    if (ROOT/before).exists():require(json.dumps(json.loads((ROOT/before).read_text()),sort_keys=True)==json.dumps(payload,sort_keys=True),'exact preserved preflight')
    else:write(before,payload)
    for n,text in [('tools/joint_corrected_cycles_runner.rs',caller()),('tools/run_joint_corrected_cycles.py',runner()),('tools/check_joint_corrected_cycles.py',checker()),('tools/validate_joint_corrected_cycles.py',validator())]:
        p=ROOT/n;require(not p.exists(),'exclusive source');p.write_text(text,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_corrected_cycles_runner.rs text eol=lf\n')
    native='evidence/voice_joint_charge_corrected_native01.json';data=json.loads((ROOT/native).read_text());require(data['passed'],'passed corrected roots');lines=data['commands'][-1]['stdout'].splitlines();rows={}
    for i,line in enumerate(lines):
        if line.startswith('CHARGE_ROOT,'):
            id,guess=map(int,line.split(',')[1:3])
            if guess==0:rows[id]=list(map(float,lines[i+1].split(',')[1:]))
    require(set(rows)=={0,1} and all(len(r)==400 for r in rows.values()),'complete exact roots');directory=ROOT/'references-local/joint-corrected-cycle-inputs01';require(not directory.exists(),'exclusive inputs');directory.mkdir();outputs=[]
    for id,raw in rows.items():
        for maximum in [65536,32768]:
            p=directory/f'{id}-{maximum}.ckp';blob=struct.pack('<QIIII400d',0,2*maximum,maximum,20,0,*raw);p.write_bytes(blob);cp=checkpoint(blob);require(list(cp['high'])+list(cp['low'])==raw,'root restoration');outputs.append(dict(id=id,maximum_half_ticks=maximum,path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=len(blob)))
    write('evidence/voice_joint_corrected_cycles_inputs01.json',dict(schema='rf-d/joint-corrected-cycle-inputs/v1',passed=True,native_seed_source=native,native_seed_sha256=sha(ROOT/native),source_sha256={'tools/prepare_joint_corrected_cycles.py':sha(ROOT/'tools/prepare_joint_corrected_cycles.py')},outputs=outputs,start_ticks=0,proposal_rule='from_conditioned:2*maximum_half_ticks',targets_are_distinct_histories=True));print('CORRECTED_CYCLES_PREPARED',flush=True)

if __name__=='__main__':main()
