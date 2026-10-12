"""Reuse the admitted reset auditor; add exact seams and the joined cycle."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
EXTRA='''def joined(p,parent,native_parent):
 old=next(q for q in parent['profiles'] if q['final_decay']==p['final_decay'] and q['maximum_half_ticks']==p['maximum_half_ticks']);native=next(q for q in native_parent['profiles'] if q['final_decay']==p['final_decay'] and q['maximum_half_ticks']==p['maximum_half_ticks'])
 previous_dir=Path(native['command'][2]);old_raw=(previous_dir/'final.ckp').read_bytes();old_cp=old_checkpoint(old_raw);new_path=next(k for k in p['input_sha256'] if k.endswith('/selected.txt'));new_dir=(ROOT/new_path).parent;new_cp=checkpoint((new_dir/'checkpoints.bin').read_bytes()[:3720]);require(old_cp['ticks']==new_cp['ticks']==START and packed(old_cp['values'])==packed(new_cp['values']) and all(old_cp[k]==new_cp[k] for k in ['maximum','limit','next_full','model','key','short','on']),'typed seam with proposal/sources')
 def rows(path):
  out=[]
  for line in path.read_text(encoding='utf8').splitlines():
   if line.startswith('OBS,'):
    x=list(map(float,line.split(',')[1:]));require(len(x)==24,'joined OBS codec');out.append(x)
  return out
 before=rows(previous_dir/'selected.txt');after=rows(new_dir/'selected.txt');require(before[-1][0]==START and after[0][0]>START and len(before)==old['fine_steps'] and len(after)==p['fine_steps'],'joined endpoint counts');all_rows=before+after;require(all(a[0]<b[0] for a,b in zip(all_rows,all_rows[1:])),'joined monotonic clock without duplicate seam')
 initial=lift(old['grids'][0]['values']);final=lift(p['grids'][-1]['values']);old_sums=[sum(D(q['native_integrals_c'][k]) for q in old['phases']) for k in range(9)];new_sums=[sum(D(q['native_integrals_c'][k]) for q in p['phases']) for k in range(9)];combined=ledger(initial,final,[float(a+b) for a,b in zip(old_sums,new_sums)],(START-old['grids'][0]['ticks'])+BOUNDARIES[-1])
 a,b=old['resets'][-1],p['resets'][0];begin,end=map(Decimal,[a['interpolated_time_s'],b['interpolated_time_s']]);require(begin<D(START)*D(TICK)<end and end>begin,'cycle straddles exact seam');period=end-begin;require(period>0,'positive cycle period');lo,hi=a['bracket_ticks'][0],b['bracket_ticks'][1];window=[x for x in all_rows if lo<=int(x[0])<=hi];require(window and int(window[0][0])==lo and int(window[-1][0])==hi,'observed cycle bracket coverage');extrema={name:dict(min_v=min(x[k] for x in window),max_v=max(x[k] for x in window)) for name,k in [('saw',15),('bus',17),('j7',4),('c2',2),('loudness',3)]}
 return dict(final_decay=p['final_decay'],maximum_half_ticks=p['maximum_half_ticks'],seam_ticks=START,first_reset=a,last_reset=b,period_s=str(period),frequency_hz=str(1/period),observed_bracket_window_ticks=[lo,hi],observed_endpoints=len(window),finite_sample_extrema_v=extrema,combined_ledger=combined,input_sha256={q.relative_to(ROOT).as_posix():sha(q) for q in [previous_dir/'selected.txt',previous_dir/'final.ckp',new_dir/'selected.txt',new_dir/'checkpoints.bin']},full_cycle_between_resets_admitted=True,steady_periodicity_admitted=False)

'''
def source():
 s=(ROOT/'tools/check_contour_reset.py').read_text(encoding='utf8').replace('from prepare_contour_reset import','from prepare_contour_cycle import').replace('from check_contour_engine import checkpoint as old_checkpoint','from check_contour_reset import checkpoint as old_checkpoint');s=s.replace("magic==b'RFMCTR01'","magic==b'RFCYCT01'")
 s=s.replace('from decimal import localcontext','from decimal import Decimal,localcontext')
 s=s.replace('voice_contour_reset_','voice_contour_cycle_').replace('tools/check_contour_reset.py','tools/check_contour_cycle.py').replace('VOZ_CONTORNO_RESET_PROTOCOLO','VOZ_CONTORNO_CICLO_PROTOCOLO');s=s.replace('def audit():',EXTRA+'def audit():')
 needle=" return dict(profiles=profiles,same_clock_refinement=compares,"
 addition=" parent=json.loads((ROOT/'evidence/voice_contour_reset_reference01.json').read_text(encoding='utf8'));native_parent=json.loads((ROOT/'evidence/voice_contour_reset_native01.json').read_text(encoding='utf8'));require(parent['passed'] and native_parent['passed'],'admitted parent');cycles=[joined(p,parent,native_parent) for p in profiles]\n for on in [True,False]:\n  a,b=[c for c in cycles if c['final_decay']==on];require(abs(D(a['period_s'])-D(b['period_s']))<=D(1e-8),'cycle period refinement')\n"
 require(needle in s,'cycle insertion');s=s.replace(needle,addition+needle.replace('profiles=profiles,','profiles=profiles,joined_cycles=cycles,'));s=s.replace('adaptive229_reset_window_admitted=True','adaptive229_cycle_window_admitted=True,steady_periodicity_admitted=False')
 s=s.replace("names={'tools/check_contour_cycle.py',", "names={'evidence/voice_contour_reset_reference01.json','evidence/voice_contour_reset_native01.json','tools/check_contour_cycle.py',")
 return s.replace('voice_contour_cycle_native01','voice_contour_cycle_native02').replace('voice_contour_cycle_inputs01','voice_contour_cycle_inputs02')
def main():
 p=ROOT/'tools/check_contour_cycle.py';require(not p.exists(),'exclusive auditor');p.write_text(source(),encoding='utf8',newline='\n')
if __name__=='__main__':main()
