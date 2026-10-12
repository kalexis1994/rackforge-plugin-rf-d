"""Declare the long-window auditor as an explicit extension of the admitted one."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
def source():
 s=(ROOT/'tools/check_contour_engine.py').read_text(encoding='utf8').replace('from prepare_contour_engine import START,BOUNDARIES,KEY,SHORT','from prepare_contour_reset import START,BOUNDARIES,KEY,SHORT,CUT')
 s=s.replace('checkpoint as old_checkpoint','checkpoint as latch_checkpoint').replace('CODEC=struct.Struct', 'from check_contour_engine import checkpoint as old_checkpoint\nCODEC=struct.Struct').replace(';CUT=5242880','')
 s=s.replace("magic==b'RFCTRE01'","magic==b'RFMCTR01'").replace('maximum in [131072,65536]','maximum in [1048576,524288]').replace('for h in [131072,65536]','for h in [1048576,524288]')
 s=s.replace('voice_contour_engine_','voice_contour_reset_').replace('tools/check_contour_engine.py','tools/check_contour_reset.py').replace('VOZ_CONTORNO_ADAPTATIVO_PROTOCOLO','VOZ_CONTORNO_RESET_PROTOCOLO')
 s=s.replace('boundary_states=[]','boundary_states=[];resets=[];last_ramp=float(initial[43]);last_ticks=START;replay_points=[];selected_accepted_count=0')
 s=s.replace('previous_end=None','previous_end=None;reset_indices=[];selection_indices=[]')
 s=s.replace('selected+=1','selected+=1;selection_indices.append(count);selected_accepted_count+=1')
 old="    i+=1\n   phase_traces.append"
 require(old not in s,'endpoint layout checked')
 needle="   phase_traces.append"
 insertion='''    ramp=ob[16];tick=int(ob[0]);crossed=last_ramp< -2. and ramp>= -2.
    if crossed:
     record=lines[i].split(',');require(len(record)==6 and record[0]=='RESET' and int(record[1])==phase and int(record[2])==last_ticks and int(record[3])==tick and float(record[4])==last_ramp and float(record[5])==ramp,'reset endpoints');i+=1
     require(triples is not None,'reset stages selected');name=f'phase{phase}-reset{len(resets)}.ckp';cp_reset=checkpoint((directory/name).read_bytes());require(cp_reset['ticks']==t0 and cp_reset['phase']==phase,'reset incoming clock')
     require(lift(cp_reset['values'])==triples[0][0],'reset incoming history');alpha=(D(-2)-D(last_ramp))/(D(ramp)-D(last_ramp));time_s=(D(last_ticks)+alpha*D(tick-last_ticks))*D(TICK);resets.append(dict(phase=phase,bracket_ticks=[last_ticks,tick],bracket_ramp_v=[last_ramp,ramp],interpolated_time_s=str(time_s),accepted_start_ticks=t0,accepted_end_ticks=t1,half_ticks=half,checkpoint_path=name));reset_indices.append(count)
    else:require(not lines[i].startswith('RESET,'),'no false reset')
    last_ramp=ramp;last_ticks=tick
'''
 s=s.replace(needle,insertion+needle)
 s=s.replace('selected==2','selected==len(set([0,count-1,*reset_indices]))').replace('len(checks)==6','len(checks)==3*selected')
 s=s.replace("expected_replays+=count+(count-inside_count if inside_count is not None else 0);", "require(selection_indices==sorted(set([0,count-1,*reset_indices])),'all reset/edge selections');starts=[(0,f'phase{phase}-start.ckp')]+([(inside_count,f'phase{phase}-inside.ckp')] if inside_count is not None else [])+[(k,r['checkpoint_path']) for k,r in zip(reset_indices,[r for r in resets if r['phase']==phase])];replay_points.extend(dict(phase=phase,start_index=k,path=n,accepted_replayed=min(16,count-k)) for k,n in starts);expected_replays+=sum(min(16,count-k) for k,n in starts);")
 s=s.replace('rollbacks=(\\d+)', 'rollbacks=(\\d+),crossings=(\\d+)').replace('total_count,5,expected_replays,4,2','total_count,5+len(resets),expected_replays,4,2,len(resets)')
 s=s.replace('return dict(final_decay=on,','require(len(resets)>=1,\'VCO reset present\');return dict(final_decay=on,').replace('restores=5,corruptions','restores=5+len(resets),selected_accepted_count=selected_accepted_count,resets=resets,replay_points=replay_points,corruptions')
 s=s.replace(' return dict(profiles=profiles,', '''  require(len(a['resets'])==len(b['resets']),'matched reset count')
  for x,y in zip(a['resets'],b['resets']):require(abs(D(x['interpolated_time_s'])-D(y['interpolated_time_s']))<=D(1e-8),'reset time refinement')
 return dict(profiles=profiles,''')
 s=s.replace('independent_candidates=144,independent_nonlinear_rows=32976,native_current_endpoint_vectors=48,native_current_values=144', "independent_candidates=6*sum(p['selected_accepted_count'] for p in profiles),independent_nonlinear_rows=1374*sum(p['selected_accepted_count'] for p in profiles),native_current_endpoint_vectors=2*sum(p['selected_accepted_count'] for p in profiles),native_current_values=6*sum(p['selected_accepted_count'] for p in profiles)")
 s=s.replace('restores=20,rejected_corruptions','restores=sum(p[\'restores\'] for p in profiles),reset_crossings=sum(len(p[\'resets\']) for p in profiles),rejected_corruptions').replace('adaptive229_window_admitted=True','adaptive229_reset_window_admitted=True')
 return s
def main():
 p=ROOT/'tools/check_contour_reset.py';require(not p.exists(),'exclusive auditor');p.write_text(source(),encoding='utf8',newline='\n')
if __name__=='__main__':main()
