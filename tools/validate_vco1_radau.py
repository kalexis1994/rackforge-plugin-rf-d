"""Freeze Radau roots, complete conditional profiles, ports and private lineage."""
import base64,hashlib,json,re,subprocess,sys
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import vco1_radau_ports as ports
from validate_mixer_on_native import native_source_identity
ROOT=ports.ROOT;sha=ports.sha
PREVIOUS='evidence/voice_vco1_741_condensation_tests01.json'
OUT='evidence/voice_vco1_radau_tests01.json'
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','.gitattributes')
ATTRS=''.join('/tools/'+n+' text eol=lf\n' for n in ('vco1_radau_kernel.rs','vco1_radau_runner.rs','vco1_radau_continuation_runner.rs')).encode()


def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,msg):
    if not ok:raise ValueError(msg)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))


def audit():
    q=read(PREVIOUS);snapshot=read('evidence/voice_vco1_radau_documentation01.json');p=read('evidence/voice_vco1_radau_probe01.json');c=read('evidence/voice_vco1_radau_continuation01.json');a=read('evidence/voice_vco1_radau_ports01.json');m=read('evidence/voice_vco1_radau_method01.json')
    require(q['passed'] and q['covered_test_count']==235 and sha(ROOT/PREVIOUS)==snapshot['previous_qa_sha256'],'previous QA')
    previous={n:base64.b64decode(v) for n,v in snapshot['previous_bytes_base64'].items()}
    old_probe=base64.b64decode(snapshot['measured_probe_bytes_base64'])
    require(hashlib.sha256(old_probe).hexdigest()==snapshot['measured_probe_sha256'],'measured helper snapshot')
    require((ROOT/'tools/vco1_radau_probe.py').read_bytes()==old_probe.replace(b"schema='rf-d/charge-sdirk-local-probe/v1'",b"schema='rf-d/charge-radau-local-probe/v1'").replace(b'np.min(trace[1:,1])<8',b'np.min(trace[1:,1])<4'),'only two adapter metadata/guard replacements')
    require((ROOT/'.gitattributes').read_bytes()==previous['.gitattributes']+ATTRS,'only explicit LF policy append')
    for n,h in q['source_sha256'].items():
        b=previous[n] if n in previous else (ROOT/n).read_bytes()
        require(hashlib.sha256(b).hexdigest()==h,'protected inherited source '+n)
    private=dict(q['private_input_sha256'])
    for record in (p,c,a):
        require(record['passed'] and record['source_sha256']==record['source_sha256_after'] and record['private_input_sha256']==record['private_input_sha256_after'],'measured receipt identity')
        require(not record['production_kernel_changed'] and record['new_spice_processes']==0 and not record['new_audio'],'scope')
        private.update(record['private_input_sha256'])
        for n,h in record['source_sha256'].items():
            b=previous[n] if n in previous else old_probe if n=='tools/vco1_radau_probe.py' else (ROOT/n).read_bytes()
            require(hashlib.sha256(b).hexdigest()==h,'recoverable measured bytes '+n)
        for output in record.get('outputs',[]):
            require(sha(ROOT/output['path'])==output['sha256'] and (ROOT/output['path']).stat().st_size==output['bytes'],'retained output')
            private[output['path']]=output['sha256']
    private[m['primary_pdf']['path']]=m['primary_pdf']['sha256']
    require(m['passed'] and m['stage_order_two_verified_rationally'] and m['order_three_conditions_verified_rationally'],'rational method derivation')
    require(p['native_roots_admitted'] and p['conditional_continuation_admitted'] and p['walk_dispatched'] and len(p['cases'])==8 and all(x['roots_passed'] and x['local_error_admitted'] for x in p['cases']),'eight trios and 1us admission')
    require(c['resource_passed'] and len(c['profiles'])==2 and all(x['complete'] for x in c['profiles']),'complete 3ms profiles')
    for record in (p,c):
        require(not record['unchanged_replays'] and all(x['exit_code']==0 for x in record['commands']),'all physical commands pass original')
        compiler=record['compiler'];require(sha(Path(compiler['path']))==compiler['sha256'],'pinned compiler')
        builds=[x for x in record['commands'] if Path(x['command'][0])==Path(compiler['path'])]
        require(builds and all('opt-level=2' in x['command'] and 'link-arg=-Wl,--stack,8388608' in x['command'] for x in builds) and record['lab_stack_bytes']==8388608,'actual build flags')
    for folder in ('vco1-radau-probe01','vco1-radau-continuation01'):
        for n in ('fine.rs','linear.rs','vco1_stamp_data.rs'):require(sha(ROOT/'references-local'/folder/n)==sha(ROOT/'references-local/vco1-reset-grid02'/n),'unchanged fine/data/linear')
        require(sha(ROOT/'references-local'/folder/'radau.rs')==sha(ROOT/'tools/vco1_radau_kernel.rs'),'same measured kernel')
    expected=(ROOT/'tools/vco1_radau_runner.rs').read_text().replace('(1e-6/TICK)','(3e-3/TICK)').replace('let maximum=262144;','let maximum:u32=args[3].parse()?;if ![131072,262144].contains(&maximum) {return Err("maximum".into());}')
    require(expected==(ROOT/'tools/vco1_radau_continuation_runner.rs').read_text(),'only duration and explicit maximum changed in runner')
    traces=[]
    for coverage,target,maximum,count in [(p['coverage'],1e-6,262144,1831),*[(x['coverage'],.003,x['maximum_accepted_half_ticks'],n) for x,n in zip(c['profiles'],(9079,15007))]]:
        raw=np.memmap(ROOT/coverage['path'],dtype='<f8').reshape(-1,542);traces.append(raw)
        require(len(raw)==count and np.isfinite(raw).all() and np.array_equal(np.diff(raw[:,0]),raw[1:,1]) and np.max(raw[:,2:5])<=1 and np.min(raw[1:,1])>=4 and np.max(raw[1:,1])<=maximum and abs(float(raw[-1,0]*(125e-9/65536))-target)<1e-17,'whole actual clock/gates/coverage')
        require(sha(ROOT/coverage['path'])==coverage['sha256'],'trace digest')
        for column in (6,274):
            hi=raw[:,column:column+134];lo=raw[:,column+134:column+268]
            require(np.array_equal(hi+lo,hi) and np.all(np.abs(lo)<=np.abs(np.spacing(hi))/2) and np.max(np.abs(hi[:,:98]))<=40 and np.max(np.abs(hi[:,98:]))<=1,'all normalized stage/endpoint states')
    require(np.array_equal(traces[0][-1,6:274],traces[1][0,6:274]) and np.array_equal(traces[1][0,6:274],traces[2][0,6:274]),'continuation memory identical')
    for raw,profile in zip(traces[1:],c['profiles']):
        ramp=raw[:,49];cross=np.flatnonzero((ramp[:-1]<-2)&(ramp[1:]>=-2))
        edges=[float((raw[k,0]+(-2-ramp[k])/(ramp[k+1]-ramp[k])*(raw[k+1,0]-raw[k,0]))*(125e-9/65536)) for k in cross]
        coverage=profile['coverage']
        require(edges==coverage['ramp_minus2_rising_crossings_s'] and len(edges)==1 and float(ramp.min())==coverage['ramp_min_v'] and float(ramp.max())==coverage['ramp_max_v'],'next reset and extrema from full export')
    actual=[p['actual_intervals'],*[x['actual_intervals'] for x in c['profiles']]]
    for raw,items in zip(traces,actual):
        changes=np.max(np.abs(np.diff(raw[:,6:104],axis=0)),axis=1)
        chosen=sorted(set([1,len(raw)-1,*list(np.argsort(changes)[-2:]+1)]))
        require([x['row_index'] for x in items]==chosen,'four actual selected intervals')
        for item in items:
            k=item['row_index'];require(item['previous_high']==raw[k-1,6:140].tolist() and item['previous_low']==raw[k-1,140:274].tolist() and item['dt_s']==raw[k,1]*(125e-9/65536),'actual history/time')
            for part,column in (('stage',274),('endpoint',6)):
                n=item['roots'][part]['native'];require(n['high']==raw[k,column:column+134].tolist() and n['low']==raw[k,column+134:column+268].tolist(),'actual roots tied to trace')
    inv=ports.ref.circuit.inventory(ports.ref.circuit.scenario(ports.C));rechecked=[]
    with localcontext() as ctx:
        ctx.prec=100
        for case in p['cases']:
            old=ports.packed(case['previous_high'],case['previous_low'])
            for label,h in [('full',2*case['half_dt_s']),('mid',case['half_dt_s']),('end',case['half_dt_s'])]:
                history=list(map(Decimal,case['steps']['mid']['roots']['endpoint']['independent_decimal'])) if label=='end' else old
                rows=ports.check(case['steps'][label]['roots'],history,h,inv)
                rechecked.append(dict(scene=case['scene'],power=case['power'],label=label,dt_s=h,rows=rows))
            full=list(map(Decimal,case['steps']['full']['roots']['endpoint']['independent_decimal']));end=list(map(Decimal,case['steps']['end']['roots']['endpoint']['independent_decimal']))
            ratios=[abs(v-w)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(v,w) in enumerate(zip(full,end))]
            require(max(ratios)<=1 and float(max(ratios))==case['error_ratio'],'all 134 local error gates')
        for source,items in [('1us',p['actual_intervals']),*[(str(x['maximum_accepted_half_ticks']),x['actual_intervals']) for x in c['profiles']]]:
            for item in items:rechecked.append(dict(source=source,row_index=item['row_index'],dt_s=item['dt_s'],rows=ports.check(item['roots'],ports.packed(item['previous_high'],item['previous_low']),item['dt_s'],inv)))
    require(canonical(rechecked)==canonical(a['pairs']) and a['stage_roots_checked']==72 and a['common_mode_identities_checked']==144,'exact retained roots/port audit reconstruction')
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private evidence '+n)
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(q['source_sha256'])|{PREVIOUS}|{n for n in staged if n and n!=OUT});sources={n:sha(ROOT/n) for n in names}
    for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    for n in (*DOCS[:3],'docs/VCO1_RADAU_RESULTADOS.md','docs/VCO1_RADAU_PROTOCOLO.md','docs/VCO1_RADAU_CONTINUACION_PROTOCOLO.md','docs/VCO1_RADAU_PUERTO_PROTOCOLO.md'):
        path=ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf8')):
            if link.startswith(('http:','https:','#')):continue
            target=(path.parent/link.split('#')[0]).resolve();require(target==ROOT/OUT or target.exists(),'local document link '+link)
    return dict(schema='rf-d/radau-charge-stages-and-conditional-reset-release/v1',passed=True,base_commit='99dd80ae8a523c091478fef891c03794d991b829',previous_qa_sha256=sha(ROOT/PREVIOUS),
                source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,covered_test_count=235,inherited_test_count=235,native_test_count=0,inherited_tests_reexecuted=False,
                independent_stage_root_comparisons=72,publication_stage_roots_reevaluated=72,common_mode_identities=144,local_raw_error_gates_unchanged=True,
                conditional_1us_admitted=True,conditional_3ms_profiles_admitted=2,next_reset_crossing_observed=True,original_euler_sdirk_rejections_unchanged=True,
                production_kernel_changed=False,new_spice_processes=0,new_audio=False,own_started_radau_admitted=False,native_full_period_admitted=False,native_frequency_refinement_admitted=False,
                calibrated_transient_admitted=False,physical_fidelity=False,real_time=False,new_method_heap_measured=False,lab_stack_bytes=8388608,c4_pf=10,
                previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],long_note_admitted_locally=False)


def main():
    out=ROOT/OUT;require(not out.exists(),'preserve publication attempt');report=dict(schema='rf-d/radau-charge-stages-and-conditional-reset-release/v1',passed=False)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    try:report=audit()
    except Exception as exc:report['error']=repr(exc)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    if not report['passed']:print('Radau release rejected',report.get('error'));sys.exit(1)
    print('Radau release:235 inherited tests;72 stage roots;144 port identities;',len(report['source_sha256']),'public;',len(report['private_input_sha256']),'private',flush=True)


if __name__=='__main__':main()
