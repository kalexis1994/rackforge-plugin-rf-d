"""Adapt the original graph auditor to the longer calendar and bounded replay."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require

def replace(s,a,b):require(s.count(a)==1,'one auditor declaration '+a[:70]);return s.replace(a,b)

def source():
    s=(ROOT/'tools/check_contour_cycle.py').read_text(encoding='utf8')
    s=s[:s.index('def joined(')]
    s=s.replace('from prepare_contour_cycle import START,BOUNDARIES,KEY,SHORT,CUT','from prepare_sustained_voice import START,BOUNDARIES,KEY,SHORT,CUT,cuts').replace("b'RFCYCT01'","b'RFHLD001'")
    a="seed=next(s for s in inp['seeds'] if s['final_decay']==on and s['maximum_half_ticks']==maximum);cp=checkpoint((ROOT/seed['path']).read_bytes());old=old_checkpoint((ROOT/seed['origin_path']).read_bytes());require(cp['ticks']==START and packed(iv)==packed(cp['values'])==packed(old['values']),'own458 history by bits');"
    b="published=json.loads((ROOT/'evidence/voice_schur_chain_trajectory01.json').read_text(encoding='utf8'));own=next(q for q in published['profiles'] if q['final_decay'] and q['maximum_half_ticks']==maximum);require(on and packed(iv)==packed(own['grids'][0]['values']),'own458 public history by bits');"
    s=replace(s,a,b)
    s=replace(s,"require(len(raw)==15*3720,'all grid/boundary checkpoints')","require(len(raw)==46*3720,'all grid/boundary checkpoints')")
    s=replace(s,"require(points[0]['sha256']==seed['sha256'],'seed identity')","require(points[0]['ticks']==START and points[0]['maximum']==maximum and points[0]['next_full']==1024 and points[0]['limit']==20 and points[0]['key']==0. and not points[0]['short'] and packed(points[0]['values'])==packed(iv),'own seed metadata/bits')")
    s=replace(s,"targets=[START+BOUNDARIES[phase+1]] if phase==0 else [START+BOUNDARIES[phase]+k*CUT for k in range(1,6)]","targets=cuts(phase)")
    s=replace(s,'selection_indices=[]','selection_indices=[];golden_index=None')
    s=replace(s,"require(2*half==ticks//(2**(attempts-1))", "if phase==1 and t1==START+788529152:golden_index=count\n   require(2*half==ticks//(2**(attempts-1))")
    s=s.replace('set([0,count-1,*reset_indices])','set([0,count-1,*reset_indices]+([golden_index] if golden_index is not None else []))')
    s=replace(s,'pc==15','pc==46')
    tail="require(len(resets)>=1,'VCO reset present');return dict("
    replacement="""require(len(resets)>=3 and sum(r['phase']==1 for r in resets)>=3,'three resets/two held cycles');
 replay_lines=(directory/'replays.txt').read_text(encoding='utf8').splitlines();actual=[]
 for line in replay_lines:
  marker,phase,name,tick,count=line.split(',');require(marker=='REPLAY','replay codec');actual.append((int(phase),name,int(tick),int(count)))
 expected=[]
 for point in replay_points:
  q=checkpoint((directory/point['path']).read_bytes());expected.append((point['phase'],point['path'],q['ticks'],point['accepted_replayed']))
 require(sorted(actual)==sorted(expected),'all local replay counts/checkpoints')
 maximum_probes=int(re.search(r'max_probes=(\\d+)',p['stderr']).group(1));require(1<=maximum_probes<=3,'bounded replay slots')
 return dict(maximum_active_replay_probes=maximum_probes,"""
    s=replace(s,tail,replacement)
    s=s.replace('from check_contour_reset import checkpoint as old_checkpoint\n','')
    return s+'\nimport numpy as np\n'+(ROOT/'tools/sustained_audit_body.py').read_text(encoding='utf8')

def main():
    p=ROOT/'tools/check_sustained_voice.py';require(not p.exists(),'exclusive graph auditor');p.write_text(source(),encoding='utf8',newline='\n');print('SUSTAINED_AUDITOR_PREPARED')
if __name__=='__main__':main()
