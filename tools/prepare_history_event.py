"""Extract eight two-step crossings without changing the admitted windows."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from check_history_propagation import Reader
from joint_cycles_analysis import require
def main():
    previous='evidence/voice_history_propagation_tests01.json';qa=json.loads((ROOT/previous).read_text());ref=json.loads((ROOT/'evidence/voice_history_propagation_reference01.json').read_text());require(qa['passed'] and ref['passed'],'previous admission')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='ab9cfc71da41f9b3c0cd273903ee918a13a39938','base')
    mutable=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md'];write('evidence/voice_history_event_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
    source='references-local/history-propagation-inputs01.bin';require(sha(ROOT/source)==qa['private_input_sha256'][source],'window input');r=Reader(ROOT/source);require(r.bytes(8)==b'RFJHPIN1' and r.integer('I')==12 and r.integer('I')==64,'codec');target=ROOT/'references-local/history-event-inputs01.bin';require(not target.exists(),'exclusive input');events=[]
    with target.open('xb') as f:
        f.write(b'RFJHEIN1'+struct.pack('<I',8))
        for window in ref['windows']:
            ids=[r.integer('I') for _ in range(3)];start=r.integer('Q');initial=r.floats(400);fixtures=r.floats(4000);schedule=[(r.integer('Q'),r.integer('I'),r.floats(7)) for _ in range(64)]
            if ids[2]==0:continue
            require(schedule[0][2][0]<-2<=schedule[1][2][0],'first two endpoints bracket reset');eid=len(events);eps=window['epsilon']
            f.write(struct.pack('<IIIIQ',eid,*ids,start));f.write(struct.pack('<9d',*eps));f.write(initial.tobytes());f.write(fixtures.tobytes())
            for ticks,half,obs in schedule[:2]:f.write(struct.pack('<QI7d',ticks,half,*obs))
            events.append(dict(id=eid,window=ids[0],profile=ids[1],location=window['location'],start_ticks=start,bracket_ticks=[schedule[0][0],schedule[1][0]],half_ticks=[schedule[0][1],schedule[1][1]],epsilon=eps))
    r.end();require(len(events)==8,'eight events');p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_history_event.rs text eol=lf\n/tools/joint_history_event_runner.rs text eol=lf\n')
    write('evidence/voice_history_event_inputs01.json',dict(passed=True,path=target.relative_to(ROOT).as_posix(),sha256=sha(target),events=events,private_used_sha256={source:sha(ROOT/source)},source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_history_event.py','docs/VOZ_EVENTO_HISTORIA_PROTOCOLO.md','evidence/voice_history_propagation_reference01.json']}));print('EVENT_INPUTS',len(events),target.stat().st_size)
if __name__=='__main__':main()
