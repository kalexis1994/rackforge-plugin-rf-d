"""Inherit temporal equations only after identity of every exported data file."""
import json,re,time,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def audit():
    target=read('evidence/voice_radau_inplace_native01.json');original=read('evidence/voice_schur_chain_native01.json');oracle=read('evidence/voice_schur_chain_trajectory01.json');inp=read('evidence/voice_radau_inplace_inputs01.json')
    require(target['passed'] and original['passed'] and oracle['passed'] and oracle['chain_schur_cycle_window_admitted'] and len(target['profiles'])==len(original['profiles'])==4,'admitted native/reference scope')
    require(inp['seeds']==read('evidence/voice_schur_chain_inputs01.json')['seeds'],'same own histories and proposals')
    def files(r,root):
        d={}
        for q in r['outputs']:
            p=ROOT/q['path'];require(sha(p)==q['sha256'] and p.stat().st_size==q['bytes'],'recorded file identity');key=p.relative_to(root).as_posix();require(key not in d,'unique exported file');d[key]=q
        require('run.exe' in d and len(d)==41,'exe plus forty data files');del d['run.exe'];require(all(Path(k).suffix in ['.txt','.ckp','.bin'] for k in d),'declared data types');return d
    a=files(original,ROOT/'references-local/schur-chain01');b=files(target,ROOT/'references-local/radau-inplace01');require(set(a)==set(b),'same complete data inventory');pairs=[]
    for key in sorted(a):
        old,new=a[key],b[key];require(old['sha256']==new['sha256'] and (ROOT/old['path']).read_bytes()==(ROOT/new['path']).read_bytes(),'every exported data byte '+key)
        pairs.append(dict(relative_path=key,original_path=old['path'],target_path=new['path'],sha256=new['sha256'],bytes=new['bytes']))
    profiles=[]
    for p in target['profiles']:
        old=next(x for x in original['profiles'] if x['final_decay']==p['final_decay'] and x['maximum_half_ticks']==p['maximum_half_ticks']);q=next(x for x in oracle['profiles'] if x['final_decay']==p['final_decay'] and x['maximum_half_ticks']==p['maximum_half_ticks'])
        pattern=r'COMPLETED,on=(\d+),max=(\d+),accepted=(\d+),restores=(\d+),replays=(\d+),corruptions=(\d+),rollbacks=(\d+),crossings=(\d+)';x,y=[re.search(pattern,c['stderr']) for c in [p,old]];require(x is not None and y is not None and x.groups()==y.groups(),'same completed native calendar/replay counts')
        require(tuple(map(int,x.groups()))==(int(p['final_decay']),p['maximum_half_ticks'],q['accepted_steps'],q['restores'],q['replayed_accepted_steps'],4,2,len(q['resets'])),'admitted coverage per profile')
        profiles.append(dict(final_decay=p['final_decay'],maximum_half_ticks=p['maximum_half_ticks'],accepted_steps=q['accepted_steps'],fine_steps=q['fine_steps'],restores=q['restores'],replayed_accepted_steps=q['replayed_accepted_steps'],wall_s=p['wall_s']))
    keys=['accepted_steps','fine_steps','restores','replayed_accepted_steps','reset_crossings','rejected_corruptions','atomic_rollbacks','original_lu_same_clock_comparison','admitted_schur_same_clock_comparison','same_clock_refinement','joined_cycles']
    return dict(radau_inplace_cycle_window_admitted=True,all_exported_data_identical=True,identical_data_files=40,identical_data_bytes=sum(p['bytes'] for p in pairs),file_identity_pairs=pairs,profiles=profiles,**{k:oracle[k] for k in keys},independent_nonlinear_rows_reexecuted=0,inherited_independent_nonlinear_rows=oracle['independent_nonlinear_rows'],temporal_graph_reexecuted=False,original_temporal_oracle_sha256=sha(ROOT/'evidence/voice_schur_chain_trajectory01.json'),new_duration_s=0,new_audio=False,full_contour_from_silence_admitted=False,physical_fidelity=False,real_time=False)

def main():
    names=['tools/check_radau_inplace_trajectory.py','evidence/voice_radau_inplace_native01.json','evidence/voice_radau_inplace_inputs01.json','evidence/voice_schur_chain_native01.json','evidence/voice_schur_chain_inputs01.json','evidence/voice_schur_chain_trajectory01.json','docs/RADAU_EN_SITIO_PROTOCOLO.md'];before={n:sha(ROOT/n) for n in names};r=dict(passed=False,source_sha256=before);t=time.perf_counter()
    try:r.update(audit());require(time.perf_counter()-t<=600,'identity audit budget');r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc();r['failed_source_text']=(ROOT/'tools/check_radau_inplace_trajectory.py').read_text(encoding='utf8')
        try:audit();r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
    r.update(source_sha256_after={n:sha(ROOT/n) for n in names},wall_s=time.perf_counter()-t);require(before==r['source_sha256_after'],'stable identity auditor');write('evidence/voice_radau_inplace_trajectory01.json',r);print('RADAU_INPLACE_TRAJECTORY',r['passed'],r.get('identical_data_files'),r.get('failure',''),flush=True)
if __name__=='__main__':main()
