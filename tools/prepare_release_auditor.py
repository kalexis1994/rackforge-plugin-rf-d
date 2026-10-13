"""Adapt original graph checks to a single restored phase and transition probes."""
from prepare_vco1_portable import ROOT
from prepare_release_voice import once
from joint_cycles_analysis import require

def source():
 s=(ROOT/'tools/check_sustained_voice.py').read_text(encoding='utf8').split('import numpy as np')[0]
 s=s.replace('from prepare_sustained_voice import START,BOUNDARIES,KEY,SHORT,CUT,cuts','from prepare_release_voice import START,BOUNDARIES,KEY,SHORT,CUT,cuts').replace("b'RFHLD001'","b'RFREL001'").replace('and phase in range(3) and','and phase==0 and').replace('flags in range(4)','flags==1').replace('for phase in range(3):','for phase in range(1):')
 s=s.replace('evidence/voice_schur_chain_trajectory01.json','evidence/voice_sustained_reference01.json').replace("own['grids'][0]['values']","own['grids'][-1]['values']")
 s=s.replace("len(raw)==46*3720","len(raw)==29*3720").replace('pc==46','pc==29').replace("points[0]['next_full']==1024","points[0]['next_full']==4096")
 s=s.replace('if phase>0 and gi==1:','if gi==1:')
 anchor=' for phase in range(1):'
 extra=" transition_cps=[(p.name,checkpoint(p.read_bytes())) for p in sorted(directory.glob('phase0-transition*.ckp'))];transition_by_tick={q['ticks']:(name,q) for name,q in transition_cps};require(len(transition_by_tick)==len(transition_cps),'unique transition checkpoints')\n"
 s=once(s,anchor,extra+anchor)
 s=s.replace('selection_indices=[];golden_index=None','selection_indices=[];golden_index=None;transition_indices=[];selected_starts={}')
 s=once(s,"if phase==1 and t1==START+788529152:golden_index=count","if t0 in transition_by_tick:transition_indices.append(count)")
 s=once(s,"coarse,mid,end=triples;require", "selected_starts[t0]=triples[0][0];coarse,mid,end=triples;require")
 s=s.replace('*reset_indices]+([golden_index] if golden_index is not None else [])','*reset_indices,*transition_indices]+([golden_index] if golden_index is not None else [])')
 anchor="replay_points.extend(dict(phase=phase,start_index=k,path=n,accepted_replayed=min(16,count-k)) for k,n in starts)"
 addition="starts.extend((k,transition_by_tick[phase_traces[k]['start_ticks']][0]) for k in transition_indices);require(len(transition_indices)==len(transition_cps) and all(lift(q['values'])==selected_starts[q['ticks']] for _,q in transition_cps),'all transitions selected with incoming history');"
 s=once(s,anchor,addition+anchor)
 s=once(s,"(int(on),maximum,total_count,5+len(resets),expected_replays,4,2,len(resets))","(int(on),maximum,total_count,2+len(resets)+len(transition_cps),expected_replays,4,1,len(resets))")
 s=s.replace("5+len(resets),selected_accepted_count", "2+len(resets)+len(transition_cps),selected_accepted_count")
 s=once(s,"require(len(resets)>=3 and sum(r['phase']==1 for r in resets)>=3,'three resets/two held cycles')","require(len(resets)>=2,'continued oscillator resets')")
 return s+'\nimport numpy as np\n'+(ROOT/'tools/release_audit_body.py').read_text(encoding='utf8')

def main():
 p=ROOT/'tools/check_release_voice.py';require(not p.exists(),'exclusive continuation auditor');p.write_text(source(),encoding='utf8',newline='\n');print('RELEASE_AUDITOR_PREPARED')
if __name__=='__main__':main()
