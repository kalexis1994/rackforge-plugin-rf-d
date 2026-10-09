"""Release audit: immutable lineage, charge conditioning, errata and scope."""
import base64,hashlib,json,re,subprocess,traceback
from pathlib import Path
from prepare_vco1_portable import ROOT,sha
from build_joint_charge_seed_caller import caller
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
OUT='evidence/voice_joint_charge_seed_tests01.json'

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))

def local_links(names):
    count=0;targets=set()
    for n in names:
        p=ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if link.startswith(('http:','https:','mailto:')):continue
            part,_,anchor=link.strip('<>').partition('#');target=(p.parent/part).resolve() if part else p
            require(target.exists(),'local link '+n+' -> '+link);count+=1;targets.add(str(target))
            if anchor and target.suffix=='.md':
                headings=[];seen={}
                for line in target.read_text(encoding='utf8').splitlines():
                    h=re.match(r'^#{1,6}\s+(.+?)\s*#*$',line)
                    if h:
                        slug=re.sub(r'[^\w\- ]','',h[1].lower()).replace(' ','-');k=seen.get(slug,0);seen[slug]=k+1;headings.append(slug+('-'+str(k) if k else ''))
                require(anchor in headings,'local anchor '+link)
    return dict(documents=names,local_link_count=count,unique_targets=len(targets),passed=True)

def audit():
    previous='evidence/voice_joint_conditioned_cycles_tests01.json';old=read(previous);before=read('evidence/voice_joint_charge_seed_before01.json');require(old['passed'] and before['previous_qa_sha256']==sha(ROOT/previous),'previous release')
    saved={n:base64.b64decode(v) for n,v in before['mutable_before_base64'].items()}
    for n,h in old['source_sha256'].items():require(hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,'protected public '+n)
    private=dict(old['private_input_sha256'])
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private '+n)
    require((ROOT/'.gitattributes').read_bytes()==saved['.gitattributes']+b'\n/tools/joint_charge_seed_runner.rs text eol=lf\n','new lab Rust bytes rule')
    require((ROOT/'tools/joint_charge_seed_runner.rs').read_bytes()==caller().encode(),'generated lab caller exact')
    defect=read('evidence/voice_joint_charge_seed_links_before01.json');name='docs/VOZ_CICLOS_CONDICIONADOS_RESULTADOS.md';original=saved[name].decode('utf8').replace('\r\n','\n')
    require(not defect['passed'] and len(defect['broken_targets'])==4 and defect['broken_targets']==defect['replay_broken_targets'] and defect['source_sha256']==hashlib.sha256(saved[name]).hexdigest(),'preserved documentation defect')
    fixed=original.replace('_native 01.json','_native01.json').replace('_reference 01.json','_reference01.json').replace('_tests 01.json','_tests01.json');fixed=re.sub(r'\b(C|J|R|CA) (?=[0-9])',r'\1',fixed)
    require((ROOT/name).read_bytes()==fixed.encode('utf8'),'only declared result errata')
    failure=read('evidence/voice_joint_charge_seed_native01.json');require(not failure['passed'] and len(failure['replays'])==1 and failure['commands'][0]['exit_code']!=0 and failure['replays'][0]['exit_code']!=0,'preserved compiler failure and replay')
    for n in ['tools/build_joint_charge_seed_caller.py','tools/joint_charge_seed_runner.rs']:
        text=failure['failed_source_text'][n];require(hashlib.sha256(text.encode()).hexdigest()==failure['source_sha256'][n],'failed source text identity')
        require((ROOT/n).read_text(encoding='utf8')==text.replace('system(p,trial)','system(p,trial,target)'),'one missing immutable argument repair')
    targets=read('evidence/voice_joint_charge_seed_targets01.json');require(targets['passed'] and len(targets['targets'])==2 and targets['targets_sha256']==sha(ROOT/'evidence/voice_joint_charge_seed_targets01.txt') and targets['mean_refinement_difference_v']<=1e-6,'declared target derivation/refinement')
    for n,h in targets['source_sha256'].items():require(sha(ROOT/n)==h,'target source '+n)
    for n,h in targets['private_input_sha256'].items():require(private[n]==h,'admitted target input '+n)
    native=read('evidence/voice_joint_charge_seed_native02.json');reference=read('evidence/voice_joint_charge_seed_reference01.json')
    for r in [native,reference]:
        require(r['passed'] and r['source_sha256']==r['source_sha256_after'],'passed unchanged measurement sources')
        for n,h in r['source_sha256'].items():require(sha(ROOT/n)==h,'measured source '+n)
    require(native['private_used_sha256']==native['private_used_sha256_after'],'frozen library')
    for n,h in native['private_used_sha256'].items():require(private[n]==h,'admitted library '+n)
    require(sha(Path(native['compiler']['path']))==native['compiler']['sha256'],'compiler identity')
    require(not native['new_library_compile'] and not native['new_audio'] and native['new_spice_processes']==0 and len(native['commands'])==2 and all(c['exit_code']==0 and c['wall_s']<=180 for c in native['commands']) and not native['replays'],'bounded caller and run')
    require(native['wall_s']<=600 and native['available_free_bytes']>=native['reserve_bytes']+native['estimated_output_bytes'] and native['minimum_free_bytes']>=native['reserve_bytes'],'resource gates')
    for r in [failure,native]:
        for o in r['outputs']:require(sha(ROOT/o['path'])==o['sha256'],'private output '+o['path']);private[o['path']]=o['sha256']
    require(len(reference['augmented_root_checks'])==4 and sum(x['rows'] for x in reference['augmented_root_checks'])==872 and reference['charge_incidence_rank']==18 and reference['physical_capacitors']==18,'218-row charge coverage')
    require(reference['preserved_charges_target0']==18 and reference['preserved_charges_target1']==17 and reference['retargeted_capacitor_index']==5 and len(reference['guess_comparisons'])==2,'explicit charge targets')
    require(len(reference['release_stage_checks'])==24 and sum(x['rows'] for x in reference['release_stage_checks'])==9600 and len(reference['release_lte'])==8 and len(reference['release_profiles'])==4 and len(reference['release_refinement'])==2 and reference['restore_replays']==4,'dynamic coverage')
    for x in [*reference['augmented_root_checks'],*reference['release_stage_checks']]:require(max(float(x['residual_gate_ratio']),float(x['correction_gate_ratio']))<=1,'independent numerical gates')
    require(reference['duration_per_profile_s']==2e-6 and reference['final_ticks']==1048576 and reference['accepted_intervals']==68 and reference['input_rejections']==2,'duration and counts')
    require(not reference['independent_root_search'] and not reference['steady_periodicity_admitted'] and not reference['own_joint_power_on'] and not reference['physical_cards_changed'] and not reference['physical_fidelity'] and not reference['real_time'],'scope')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();require(OUT in staged,'staged QA')
    docs=sorted(n for n in staged if n.endswith('.md'));links=local_links(docs)
    names=set(old['source_sha256'])|{previous}|(set(staged)-{OUT});sources={n:sha(ROOT/n) for n in sorted(names)}
    for n in staged:
        if n!=OUT:native_source_identity(n,sources[n],subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    return dict(schema='rf-d/joint-charge-seed-release/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=sha(ROOT/previous),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,inherited_test_count=248,native_test_count=0,covered_test_count=248,inherited_tests_reexecuted=False,new_independent_initial_rows=872,new_independent_dynamic_rows=9600,new_independent_stage_points=48,independent_roots=0,charge_targets=2,chain_capacitors=18,accepted_intervals=68,published_half_steps=136,duration_per_profile_s=2e-6,final_ticks=1048576,restore_replays=4,charge_conditioning_lab_admitted=True,short_release_admitted=True,production_physics_changed=False,new_library_compile=False,previous_initialized_cycles_admitted_under_their_history=True,steady_periodicity_admitted=False,own_joint_power_on=False,full_voice_radau_admitted=False,physical_fidelity=False,real_time=False,heap_measured_this_block=False,lab_stack_bytes=33554432,new_audio=False,new_spice_processes=0,local_markdown_links=links,documentation_erratum_preserved=True,compiler_failure_preserved=True,previous_audio=old['previous_audio'],native_listening=old['native_listening'],official_executable_sha256=old['official_executable_sha256'])

def main():
    try:r=audit()
    except Exception:
        r=dict(passed=False,failure=traceback.format_exc(),failed_source_text=(ROOT/'tools/validate_joint_charge_seed.py').read_text())
        try:audit();r['replay']='unexpected pass'
        except Exception:r['replay']=traceback.format_exc()
        k=1
        while (ROOT/f'evidence/voice_joint_charge_seed_qa_failure{k:02d}.json').exists():k+=1
        (ROOT/f'evidence/voice_joint_charge_seed_qa_failure{k:02d}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');raise
    (ROOT/OUT).write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n');print('CHARGE_SEED_QA',r['passed'],len(r['source_sha256']),len(r['private_input_sha256']),r['local_markdown_links']['local_link_count'],flush=True)
if __name__=='__main__':main()
