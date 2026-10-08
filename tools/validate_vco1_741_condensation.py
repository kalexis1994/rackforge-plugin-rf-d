"""Publish exact loaded-port evidence, preserving rejected adapters and scopes."""
import base64,hashlib,json,re,subprocess,sys
from decimal import Decimal,localcontext
from pathlib import Path
import vco1_741_condensation as kernel
import vco1_741_roots as roots
from validate_mixer_on_native import native_source_identity
ROOT=kernel.ROOT
sha=kernel.sha
require=kernel.require
DOCS=('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md')
PREVIOUS='evidence/voice_vco1_sdirk_tests01.json'
OUT='evidence/voice_vco1_741_condensation_tests01.json'


def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))


def audit():
    q=read(PREVIOUS);snapshot=read('evidence/voice_vco1_741_documentation01.json')
    require(q['passed'] and q['covered_test_count']==235 and sha(ROOT/PREVIOUS)==snapshot['previous_qa_sha256'],'previous QA')
    oldbytes={n:base64.b64decode(v) for n,v in snapshot['previous_bytes_base64'].items()}
    for n,h in q['source_sha256'].items():
        if n in oldbytes:require(hashlib.sha256(oldbytes[n]).hexdigest()==h,'document snapshot')
        else:require(sha(ROOT/n)==h,'protected source '+n)
    private=dict(q['private_input_sha256'])
    records=[read(f'evidence/voice_vco1_741_{kind}{k:02d}.json') for kind in ('condensation','roots') for k in (1,2,3)]
    c1,c2,c3,r1,r2,r3=records
    require(not c1['passed'] and not c2['passed'] and c3['passed'] and not r1['passed'] and not r2['passed'] and r3['passed'],'original admission scopes')
    require(c1['source_sha256']==c2['source_sha256'] and c1['error']==c2['error'] and canonical(c1['scenes'])==canonical(c2['scenes']),'linear original/replay')
    require(r1['source_sha256']==r2['source_sha256'] and r1['error']==r2['error'] and canonical(r1['cases'])==canonical(r2['cases'])==canonical(r3['cases']),'nine root pairs identical across repairs')
    archive=ROOT/'references-local/vco1-741-source01';archive.mkdir(exist_ok=True)
    for record in records:
        require(record['source_sha256']==record['source_sha256_after'] and record['private_input_sha256']==record['private_input_sha256_after'],'measured identity')
        require(not record['production_kernel_changed'] and not record['new_audio'] and record['new_spice_processes']==0,'laboratory scope')
        private.update(record['private_input_sha256'])
        for n,h in record['source_sha256'].items():
            b=(ROOT/n).read_bytes()
            if hashlib.sha256(b).hexdigest()!=h:
                if n in oldbytes:b=oldbytes[n]
                elif n in record.get('failed_source_text',{}):b=record['failed_source_text'][n].encode('utf8')
                else:raise ValueError('unrecoverable measured source '+n)
            require(hashlib.sha256(b).hexdigest()==h,'measured bytes '+n)
            if sha(ROOT/n)!=h and n not in oldbytes:
                target=archive/(h+'.blob')
                if not target.exists():target.write_bytes(b)
                require(sha(target)==h,'failed source archive')
                private[target.relative_to(ROOT).as_posix()]=h
    require(len(list(archive.glob('*.blob')))==2,'both failed helper versions recoverable')
    diagnostic=read('references-local/vco1-741-condensation-diagnostic01.json')
    require(diagnostic['original_source_sha256']==c1['source_sha256']['tools/vco1_741_condensation.py'] and Decimal(diagnostic['diagnostic']['maxerr'])<kernel.GATE and Decimal(diagnostic['diagnostic']['mass'])>Decimal('1e-4'),'original return omission diagnosed')
    inv=kernel.circuit.inventory(kernel.circuit.scenario(roots.C))
    descriptor=read('evidence/voice_vco1_reset_modes02.json')
    with localcontext() as ctx:
        ctx.prec=100
        require(len(c3['scenes'])==3 and len(r3['cases'])==9 and len(r3['decompositions'])==2,'complete new banks')
        for index,(scene,measured) in enumerate(zip(descriptor['scenes'],c3['scenes'])):
            require(scene['previous_high']==measured['previous_high'] and scene['previous_low']==measured['previous_low'],'linear history provenance')
            x=[Decimal.from_float(h)+Decimal.from_float(l) for h,l in zip(scene['previous_high'],scene['previous_low'])]
            require([case['dt_s'] for case in measured['cases']]==[0.,125e-9,125e-9/4096,125e-9/16384],'frozen linear intervals')
            for case in measured['cases']:
                result=kernel.coupled(x,case['dt_s'],roots.C,inv)
                require(canonical(result)==canonical(case),'reconstructed linear system and all port columns')
            for dt in (125e-9/16384,125e-9/8192,125e-9/4096):
                candidates=[c for c in r3['cases'] if c['scene']==index and c['dt_s']==dt]
                require(len(candidates)==1,'unique nonlinear root')
                case=candidates[0];candidate=list(map(Decimal,case['condensed_decimal']));full=list(map(Decimal,case['full_decimal']))
                require(kernel.circuit.valid(candidate,roots.C) and kernel.circuit.valid(full,roots.C),'both nonlinear roots in domain')
                error=[a-b for a,b in zip(candidate,full)]
                require(kernel.maximum(error[:98])<=kernel.op.D(2e-7) and kernel.maximum(error[98:])<=kernel.op.D(2e-10),'stored independent root comparison')
                for vector in (candidate,full):
                    residual,j,g=kernel.circuit.reference_decimal(vector,x,dt,roots.C)
                    correction=kernel.op.dense([row[:] for row in j],[-v for v in residual])
                    require(kernel.maximum(residual[:98])<=kernel.op.D(2e-14) and kernel.maximum(residual[98:])<=kernel.op.D(2e-12),'reconstructed nonlinear residual')
                    require(kernel.maximum(correction[:98])<=kernel.op.D(2e-10) and kernel.maximum(correction[98:])<=kernel.op.D(2e-13) and abs(sum(residual[:98])+g)<=kernel.op.D(1e-11),'independent correction and ground')
                require(case['passed'] and case['budget_rejected'] and case['repetition_identical'] and case['history_unchanged'],'transaction and replay')
        for result,ticks in zip(r3['decompositions'],(8,4)):
            floor=read(result['source_receipt']);reconstructed=roots.decomposition(floor,inv,ticks*125e-9/65536);reconstructed['source_receipt']=result['source_receipt']
            require(canonical(reconstructed)==canonical(result),'SDIRK base decomposition')
            actual=Decimal(result['base_difference_v'])
            require(abs(actual)>kernel.op.D(2e-6) and Decimal('0.9998')<Decimal(result['dynamic_fraction_signed'])<1,'both rejected local errors and dynamic contribution')
            require(float(abs(actual)/kernel.op.D(2e-6))==floor['independent_limit']['error_ratio'],'unchanged previous LTE verdict')
    for n,h in private.items():require(sha(ROOT/n)==h,'private evidence '+n)
    require(sha(ROOT/q['previous_audio']['path'])==q['previous_audio']['sha256'],'previous audible source unchanged')
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
    names=sorted(set(q['source_sha256'])|{PREVIOUS}|{n for n in staged if n and n!=OUT})
    sources={n:sha(ROOT/n) for n in names}
    for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    for n in (*DOCS,'docs/VCO1_741_CONDENSACION_RESULTADOS.md','docs/VCO1_741_CONDENSACION_PROTOCOLO.md','docs/VCO1_741_RAICES_PROTOCOLO.md'):
        p=ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if link.startswith(('http:','https:','#')):continue
            target=(p.parent/link.split('#')[0]).resolve();require(target==ROOT/OUT or target.exists(),'local document target '+link)
    return dict(schema='rf-d/loaded-lm741-exact-port-release/v1',passed=True,base_commit=c3['base_commit'],previous_qa_sha256=sha(ROOT/PREVIOUS),
                source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,
                covered_test_count=235,inherited_test_count=235,native_test_count=0,inherited_tests_reexecuted=False,
                unique_loaded_linear_systems=12,publication_linear_systems_reexecuted=12,unique_nonlinear_root_pairs=9,
                nonlinear_root_pairs_executed_including_repeats=27,root_history_and_budget_rejections_checked=True,
                original_adapter_failures_preserved=4,common_mode_endpoint_pairs_decomposed=6,
                exact_port_condensation_admitted_locally=True,conditional_decimal_nonlinear_roots_admitted=True,
                production_kernel_changed=False,dynamic_reduction_admitted=False,previous_temporal_rejections_unchanged=True,
                new_spice_processes=0,new_audio=False,native_full_period_admitted=False,native_frequency_refinement_admitted=False,
                calibrated_transient_admitted=False,free_dc_admitted=False,physical_fidelity=False,real_time=False,
                new_heap_measurement=False,c4_pf=10,previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],long_note_admitted_locally=False)


def main():
    out=ROOT/OUT;require(not out.exists(),'preserve publication attempt')
    report=dict(passed=False,schema='rf-d/loaded-lm741-exact-port-release/v1')
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    try:report=audit()
    except Exception as exc:report['error']=repr(exc)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    if not report['passed']:print('741 release rejected:',report.get('error'));sys.exit(1)
    print('741 release:235 inherited tests;12 linear systems;9 unique nonlinear pairs;',len(report['source_sha256']),'public;',len(report['private_input_sha256']),'private',flush=True)


if __name__=='__main__':main()
