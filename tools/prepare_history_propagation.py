"""Freeze twelve contiguous calendars and exact HIGH/LOW selected seams."""
import base64,json,struct,subprocess
import numpy as np
from prepare_vco1_portable import ROOT,sha,write
from check_joint_cycles import bank
from joint_cycles_analysis import trace,require,TICK
OBS=[('ramp',43),('saw',46),('tri',54),('pulse',44),('bus',12),('cursor',39),('j7',194)]
def main():
    previous='evidence/voice_history_tangent_tests01.json';old=json.loads((ROOT/previous).read_text());require(old['passed'],'previous QA')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(head=='89085fb5f6999606ade53ba080e97d29daca6029','base commit')
    names=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']
    write('evidence/voice_history_propagation_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    inputs=json.loads((ROOT/'evidence/voice_history_tangent_inputs01.json').read_text());private={};windows=[]
    target=ROOT/'references-local/history-propagation-inputs01.bin';require(not target.exists(),'exclusive input')
    with target.open('xb') as f:
        f.write(b'RFJHPIN1'+struct.pack('<II',12,64))
        for profile,name in enumerate(inputs['selected_sha256']):
            p=ROOT/name;require(sha(p)==old['private_input_sha256'][name],'selected input');private[name]=sha(p)
            tp=p.parent/'trace.bin';tn=tp.relative_to(ROOT).as_posix();require(sha(tp)==old['private_input_sha256'][tn],'trace input');private[tn]=sha(tp);rows=trace(tp);cases=bank(p)
            lines=p.read_text().splitlines();raw=[]
            for i,line in enumerate(lines):
                if line.startswith('JOINT_ROOT,'):raw.append([list(map(float,s.split(',')[1:])) for s in lines[i+1:i+6]])
            for location,index in enumerate([0,3,6]):
                endpoint=cases[index+1][1];found=np.ones(len(rows),dtype=bool)
                for field,k in OBS:found&=rows[field]==endpoint[k]+endpoint[200+k]
                ix=np.flatnonzero(found);require(len(ix)==1,'unique calendar anchor');start=int(ix[0]);schedule=rows[start:start+64];require(len(schedule)==64,'64 steps')
                ticks=int(schedule[0]['ticks'])-int(schedule[0]['half_ticks']);wid=len(windows)
                require(cases[index+1][0][1]==int(schedule[0]['half_ticks'])*TICK and cases[index+2][0][1]==int(schedule[1]['half_ticks'])*TICK,'selected clocks')
                f.write(struct.pack('<IIIQ',wid,profile,location,ticks));f.write(struct.pack('<400d',*raw[index][0]))
                for fixture in [raw[index+1],raw[index+2]]:f.write(struct.pack('<2000d',*[v for s in fixture for v in s]))
                for row in schedule:f.write(struct.pack('<QI7d',int(row['ticks']),int(row['half_ticks']),*[float(row[n]) for n,_ in OBS]))
                windows.append(dict(id=wid,profile=profile,location=['first','reset1','reset2'][location],trace=tn,start_row=start,start_ticks=ticks,end_ticks=int(schedule[-1]['ticks']),half_ticks=list(map(int,schedule['half_ticks'])),duration_s=(int(schedule[-1]['ticks'])-ticks)*TICK))
    attr=ROOT/'.gitattributes';attr.write_bytes(attr.read_bytes()+b'\n/tools/joint_history_propagation.rs text eol=lf\n/tools/joint_history_propagation_runner.rs text eol=lf\n')
    write('evidence/voice_history_propagation_inputs01.json',dict(passed=True,path=target.relative_to(ROOT).as_posix(),sha256=sha(target),private_used_sha256=private,windows=windows,source_sha256={'tools/prepare_history_propagation.py':sha(ROOT/'tools/prepare_history_propagation.py'),'docs/VOZ_PROPAGACION_HISTORIA_PROTOCOLO.md':sha(ROOT/'docs/VOZ_PROPAGACION_HISTORIA_PROTOCOLO.md')}))
    print('PROPAGATION_INPUTS',len(windows),target.stat().st_size)
if __name__=='__main__':main()
