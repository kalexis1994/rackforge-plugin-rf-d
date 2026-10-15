"""Close four rejected electrical-interface experiments; preserve active direct."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_inline import derive as inline
from prepare_hybrid_compact import derive as compact
from check_hybrid_voice import unpack,parse,compare
from check_hybrid_schur import comparison
from validate_joint_charge_seed import local_links
OUT='evidence/hybrid_compact_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def identity(r,archives):
    images=[json.loads(unpack(x['failed_sources'])) for x in [r,*archives] if 'failed_sources' in x]
    for n,h in r['source_sha256'].items():
        assert sha(ROOT/n)==h or any(n in a and hashlib.sha256(base64.b64decode(a[n])).hexdigest()==h for a in images),n
def main():
    before=read('evidence/hybrid_inline_before01.json');old=read(before['previous_qa']);assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    protected=old['private_input_sha256'];assert all((ROOT/n).is_file() for n in protected)
    names=[f'evidence/hybrid_{kind}_native{k:02d}.json' for kind in ['inline','compact'] for k in [1,2]];attempts=[read(n) for n in names]
    previous=read('evidence/hybrid_direct_native03.json');baseline=[p for p in previous['profiles'] if p['mode']=='direct']
    ratios=[]
    for r in attempts:
        assert not r['passed'] and r['failed_phase']=='cost';identity(r,attempts)
        a=r['failed_process'];b=r['unchanged_replay'];assert a['exit_code']==b['exit_code']==0
        assert unpack(a['stdout']).split(b'FINAL,')[0]==unpack(b['stdout']).split(b'FINAL,')[0]
        ratio=r['profiles'][2]['measurement']['solve_s']/r['profiles'][0]['measurement']['solve_s'];assert ratio==r['cost_ratio'] and ratio>.9;ratios.append(ratio)
        grids=[]
        for p in r['profiles']:
            raw=unpack(p['stdout']);g,roots,f=parse(raw);assert f['heap_allocations']==0 and f['exact_replays']==4 and f['atomic_rejections']==5
            q=baseline[0 if p['maximum_full_ticks']==33554432 else 1];control=unpack(q['stdout']);og,_,_=parse(control)
            assert raw.split(b'FINAL,')[0]==control.split(b'FINAL,')[0]
            assert comparison(g,og,raw,control)==p['schur_comparison'];assert p['solver']['max_final_backward']<=1e-11
            y=p['full_voice_comparison'];assert y['j7_rms_relative']<=.03 and y['j7_peak_relative']<=.06 and y['j7_mean_error_v']<=1e-5 and max(y['contour_fraction'],y['bus_fraction'],y['load_fraction'])<=1
            if p['mode']!='baseline':grids.append(g)
        assert json.dumps(compare(grids[0],grids[1],True),sort_keys=True)==json.dumps(r['refinement'],sort_keys=True)
        for n,h in r['private_used_sha256'].items():assert protected[n]==h and sha(ROOT/n)==h,n
        assert r['temporary_area_empty'] and sha(Path(old['compiler']['path']))==old['compiler']['sha256']==r['compiler_sha256']
        assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==r['library_sha256']
    for r in attempts[:2]:
        x=r['local'];assert x['stages']==48 and x['fd_columns']==472 and x['invalid_parameters']==3
        assert x['fd_fraction']<=1 and max(x[k] for k in ['dc_fraction','dq_fraction','jacobian_fraction','mass_fraction','fast_dc_fraction','fast_dq_fraction'])==0
        assert r['guards']['invalid_stage_cases']==r['guards']['exact_retries']==26;unpack(r['guards']['stdout'])
    for r in attempts[2:]:
        x=r['local'];assert x['directions']==192 and x['direction_fraction']<=1 and x['bitwise_matrix_entries']==24*236*236
        assert x['invalid_cases']==x['exact_invalid_retries']==33 and x['new_legal_edge_retries']==24 and x['cancellation_probes']==1
        assert x['fill_swap_rhs_fixtures']==16 and x['factor_overflow_retries']==x['global_capacity_retries']==1
        assert x['maximum_stage_nonzeros']==481 and x['stage_coefficient_snapshots']==48;unpack(r['local_stdout']);unpack(r['local_input'])
    for n,s in (inline()|compact()).items():assert (ROOT/n).read_bytes()==s.encode(),n
    profile=read('evidence/hybrid_electrical_profile01.json');assert profile['passed'] and profile['temporary_area_empty'];identity(profile,attempts)
    assert all(v>0 for v in profile['timed_sections_s'].values());assert all(v==0 for v in profile['comparison'].values() if isinstance(v,float))
    audit=read('evidence/hybrid_compact_audit01.json');assert audit['passed'] and audit['original_rows']==5712;identity(audit,attempts)
    assert all(x['max_residual_a']<=2e-11 and x['max_correction_v']<=2e-9 for x in audit['profiles'])
    assert not list((ROOT/'tmp/lab-current').iterdir())
    receipts=[p for pattern in ['hybrid_electrical*.json','hybrid_inline*.json','hybrid_compact*.json'] for p in (ROOT/'evidence').glob(pattern) if p!=ROOT/OUT]
    receipt_bytes=sum(p.stat().st_size for p in receipts);assert receipt_bytes<=16*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for receipt in [*attempts,profile,audit]:assert set(receipt['source_sha256'])<=set(sources)
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    r={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    r.update(schema='rf-d/nominal-hybrid-electrical-interface-rejections/closure-v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(protected),electrical_interface_optimization_admitted=False,electrical_interface_cost_gate_passed=False,electrical_interface_cost_ratios=ratios,electrical_interface_cost_gate=.9,inline_stage_checks=48,inline_fd_columns=472,inline_invalid_parameters=3,inline_stage_invalid_cases=26,inline_stage_exact_retries=26,compact_stage_snapshots=48,compact_matrix_entries=24*236*236,compact_directions=192,compact_boundary_invalid_cases=35,compact_boundary_exact_retries=35,compact_legal_edge_retries=24,compact_fill_swap_rhs_fixtures=16,compact_stage_capacity=2048,compact_selected_stage_nonzeros=481,compact_global_capacity_retries=1,compact_original_rows=5712,new_private_sound_inputs=0,new_audio=False,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,inherited_tests_reexecuted=False,new_unit_test_definitions=0,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    assert r['active_solver']==old['active_solver'] and r['active_voice']==old['active_voice'] and r['cost_ratio']==old['cost_ratio']
    r['electrical_interface_receipts_bytes_before_qa']=receipt_bytes;r['electrical_interface_receipts_budget_bytes']=16*1024*1024
    r['electrical_interface_reference']={n:sha(ROOT/n) for n in [*names,'evidence/hybrid_electrical_profile01.json','evidence/hybrid_compact_audit01.json']}
    write(ROOT/OUT,r);print('ELECTRICAL_INTERFACE_CLOSURE',len(sources),len(protected),ratios,'active=direct')
if __name__=='__main__':main()
