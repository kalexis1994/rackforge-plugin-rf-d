"""Local ladder admission; preserve the active direct voice and its lineage."""
import base64,hashlib,json,subprocess
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from prepare_ladder_algebraic import derive
from check_hybrid_voice import packed,unpack,parse
from check_ladder_algebraic import KEYS
from validate_joint_charge_seed import local_links
OUT='evidence/ladder_algebraic_tests01.json'
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def main():
    before=read('evidence/ladder_algebraic_before01.json');old=read(before['previous_qa'])
    assert old['passed'] and sha(ROOT/before['previous_qa'])==before['previous_qa_sha256']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==before['base_commit']
    saved={n:base64.b64decode(v) for n,v in before['mutable_original_b64'].items()}
    for n,h in old['source_sha256'].items():assert hashlib.sha256(saved[n] if n in saved else (ROOT/n).read_bytes()).hexdigest()==h,n
    for n,data in saved.items():assert (ROOT/n).read_bytes().startswith(data),n
    private=old['private_input_sha256'];assert len(private)==8769 and all((ROOT/n).is_file() for n in private)
    names=[f'evidence/ladder_algebraic_native{k:02d}.json' for k in [1,2,3]];attempts=[read(n) for n in names]
    extension=read('evidence/ladder_algebraic_extensions_before01.json')
    images=[json.loads(unpack(attempts[0]['failed_sources'])),json.loads(unpack(extension['retired_sources']))]
    for n,h in extension['source_sha256'].items():assert hashlib.sha256(base64.b64decode(images[1][n])).hexdigest()==h,n
    native=read('evidence/hybrid_direct_native03.json');rows=[]
    for p in native['profiles']:
        if p['mode']=='direct':
            _,roots,_=parse(unpack(p['stdout']));rows.extend(','.join(map(str,row)) for row in roots)
    expected=('\n'.join(rows)+'\n').encode();assert len(rows)==24
    for r in attempts:
        assert unpack(r['local_input'])==expected
        for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h or any(n in a and hashlib.sha256(base64.b64decode(a[n])).hexdigest()==h for a in images),n
        assert r['temporary_area_empty'] and not any(r[k] for k in ['new_audio','new_private_sound_inputs','real_time','physical_fidelity','global_ladder_reduction_admitted'])
        assert sha(Path(old['compiler']['path']))==old['compiler']['sha256']==r['compiler_sha256']
        assert sha(ROOT/old['public_assembly_library_path'])==old['public_assembly_library_sha256']==r['library_sha256']
    failure=attempts[0];assert not failure['passed'] and failure['failed_phase']=='compile'
    a=failure['failed_process'];b=failure['unchanged_replay'];assert a['exit_code']==b['exit_code']!=0
    assert unpack(a['stdout'])==unpack(b['stdout']) and a['stderr']==b['stderr']
    assert 'E0284' in a['stderr']
    for r in attempts[1:]:
        assert r['passed'] and r['compile_exit_code']==0
        values=list(map(float,unpack(r['local_stdout']).decode().strip().split(',')[1:]))
        assert len(values)==len(r['local']) and all(r['local'][k]==v for k,v in zip(KEYS,values))
        x=r['local'];assert x['stages']==48 and x['solves']==384 and x['fd_columns']==72 and x['maximum_iterations']<=80
        assert x['invalid_cases']==148 and x['invalid_parameters']==30 and x['heap_allocations']==0
        assert x['dc_fraction']==x['jacobian_fraction']==x['charge_error_a']==x['mass_error_s']==0
        assert max(x[k] for k in ['reaction_fd_fraction','source_fd_fraction','reconstruction_fd_fraction'])<=1
        assert x['coordinate_error_v']<=2e-9 and x['reconstructed_error_v']<=2e-9 and x['reaction_error_a']<=20e-12
        assert x['source_conservation_a']<=20e-12 and x['source_conservation_s']<=2e-9
        assert x['maximum_residual_a']<=1e-12 and x['maximum_correction_v']<=2e-9
    x=attempts[2]['local'];assert x['parent_charge_checks']==48 and x['direct_fd_columns']==128 and x['direct_fd_fraction']<=1
    assert x['parent_charge_error_a']<=20e-12 and x['parent_mass_error_s']<=2e-9
    assert x['low_cancellation_probes']==1 and x['factor_rhs_fixtures']==8 and x['h_endpoint_checks']==2
    for n,s in derive().items():assert (ROOT/n).read_bytes()==s.encode(),n
    assert not list((ROOT/'tmp/lab-current').iterdir())
    receipts=[p for p in (ROOT/'evidence').glob('ladder_algebraic*.json') if p!=ROOT/OUT]
    receipt_bytes=sum(p.stat().st_size for p in receipts);assert receipt_bytes<=4*1024*1024
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines();assert OUT in staged
    sources={n:sha(ROOT/n) for n in sorted(set(old['source_sha256'])|{before['previous_qa']}|(set(staged)-{OUT}))}
    for r in attempts:assert set(r['source_sha256'])<=set(sources)
    for n in set(staged)-{OUT}:assert hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=ROOT)).hexdigest()==sources[n],n
    result={k:v for k,v in old.items() if k not in ['schema','source_sha256','local_markdown_links']}
    result.update(schema='rf-d/nominal-local-ladder-algebraic-reconstruction/v1',passed=True,base_commit=before['base_commit'],previous_qa_sha256=before['previous_qa_sha256'],source_sha256=sources,protected_public_sources=len(old['source_sha256']),protected_private_inputs=len(private),local_ladder_reconstruction_admitted=True,global_ladder_reduction_admitted=False,ladder_cost_measured=False,local_ladder=x,local_ladder_reference={n:sha(ROOT/n) for n in names},ladder_owned_capacitors=5,ladder_internal_memories=4,ladder_algebraic_unknowns=7,ladder_retained_coordinates=9,ladder_physical_ports=5,ladder_admitted_parameter_scope='nominal CA3046; existing direct 40-100 ms ROOT states only',inherited_global_trajectories_reexecuted=False,inherited_private_hashes_recomputed=False,inherited_private_paths_present=True,inherited_tests_reexecuted=False,new_unit_test_definitions=0,new_audio=False,new_private_sound_inputs=0,new_library_compile=False,new_cargo_cache=False,real_time=False,physical_fidelity=False,ladder_receipt_bytes_before_qa=receipt_bytes,ladder_receipt_budget_bytes=4*1024*1024,local_markdown_links=local_links([n for n in staged if n.endswith('.md')]))
    for k in ['active_solver','active_voice','cost_ratio','inherited_test_count','private_input_sha256']:assert result[k]==old[k],k
    write(ROOT/OUT,result);print('LADDER_ALGEBRAIC_QA',len(sources),len(private),'local admitted; active=direct; global pending',receipt_bytes)
if __name__=='__main__':main()
