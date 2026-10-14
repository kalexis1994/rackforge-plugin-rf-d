"""Admit the preserved input catalog, explicit cleanup, and exact panel port."""
import base64,gzip,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from validate_joint_charge_seed import local_links
OUT='evidence/lab_retention_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def main():
    before=read('evidence/lab_retention_before01.json');old=read(before['previous_qa'])
    assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,original in saved.items():assert (ROOT/n).read_bytes().startswith(original),n
    cleanup=read('evidence/lab_cleanup01.json');ledger=read('evidence/lab_retention_ledger01.json');port=read('evidence/vco_panel_port01.json')
    assert cleanup['passed'] and cleanup['retired_files']==cleanup['planned_files']==110705 and cleanup['retired_bytes']==cleanup['planned_bytes']==22338992032
    assert cleanup['admitted_inputs_retired']==0 and cleanup['protected_inputs']==len(old['private_input_sha256'])
    assert cleanup['removed_empty_directories']==10325 and ledger['passed'] and not ledger['retired_samples_archived']
    packed=next(iter(ledger['private_sha256']));data=gzip.decompress((ROOT/packed).read_bytes())
    assert hashlib.sha256(data).hexdigest()==cleanup['plan_sha256']==ledger['restored_plan_sha256']
    plan=json.loads(data);protected=set(old['private_input_sha256'])
    assert protected.isdisjoint(x['path'] for x in plan['files'])
    assert not any((ROOT/x['path']).exists() for x in plan['files'])
    assert all((ROOT/n).is_file() for n in protected)
    assert port['passed'] and port['star_cases']==70 and port['full_voice_observations']==1602 and port['fd_columns']==210 and port['invalid_rejections']==7
    assert max(port['gate_fractions'].values())<=1 and port['temporary_area_empty']
    assert not list((ROOT/'tmp/lab-current').iterdir())
    for name in ['evidence/lab_cleanup01.json','evidence/lab_retention_ledger01.json','evidence/vco_panel_port01.json']:
        for n,h in read(name)['source_sha256'].items():assert sha(ROOT/n)==h,(name,n)
    for n,h in {**ledger['private_sha256'],**port['private_used_sha256']}.items():assert sha(ROOT/n)==h,n
    assert sha(Path(old['compiler']['path']))==old['compiler']['sha256']
    assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r=dict(old)
    r.update(schema='rf-d/lab-retention-and-panel-port/admission-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,private_input_sha256=old['private_input_sha256'],protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(protected),logical_retired_bytes=cleanup['retired_bytes'],retired_files=cleanup['retired_files'],removed_empty_directories=cleanup['removed_empty_directories'],admitted_inputs_retired=0,private_ledger=ledger['private_sha256'],new_private_sound_inputs=0,new_audio=False,new_library_compile=False,new_cargo_cache=False,spatial_reduction=True,panel_cursor_eliminated=True,panel_full_voice_observations=1602,panel_star_cases=70,panel_fd_columns=210,panel_invalid_rejections=7,oscillator_waveform_changed=False,physical_memory_removed=False,new_unit_test_definitions=0,inherited_tests_reexecuted=False,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    # Previous rows/trajectories stay explicitly inherited, not rerun here.
    r['previous_note_campaign_inherited']=True;r['new_original_nonlinear_rows']=0
    r['new_panel_port_reference']={'path':'evidence/vco_panel_port01.json','sha256':sha(ROOT/'evidence/vco_panel_port01.json')}
    write(ROOT/OUT,r);print('LAB_RETENTION_QA',len(sources),len(protected),r['retired_files'],r['logical_retired_bytes'])
if __name__=='__main__':main()
