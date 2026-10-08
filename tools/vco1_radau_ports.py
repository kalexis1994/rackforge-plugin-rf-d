"""Full charge equation audit and common-mode reconstruction of both Radau stages."""
import json,time
from decimal import Decimal,localcontext
from fractions import Fraction as F
import vco1_radau_reference as ref
from vco1_newton_reference import ROOT,sha
C=[.5,500.,1e-11,0.,0.,*([-2.1]*6)]
Z=Decimal(0)


def packed(h,l):return [Decimal.from_float(a)+Decimal.from_float(b) for a,b in zip(h,l)]


def check(pair,old,h,inv):
    stages=[list(map(Decimal,pair[part]['independent_decimal'])) for part in ('stage','endpoint')]
    r,j,ground=ref.system(stages,old,h,C)
    correction=ref.circuit.op.dense([row[:] for row in j],[-v for v in r])
    rows=[]
    card={w[0]:w for w in ref.circuit.op.card()}
    l=ref.circuit.op.D(card['L2'][4]);resistance=ref.circuit.op.D(card['R13'][4]);gain=ref.circuit.op.D(card['G4'][7]);offset=ref.circuit.op.D(card['EOS'][6])
    for i,part in enumerate(('stage','endpoint')):
        rr=r[134*i:134*(i+1)];dd=correction[134*i:134*(i+1)]
        n=pair[part]['native'];candidate=packed(n['high'],n['low']);error=[abs(v-w) for v,w in zip(candidate,stages[i])]
        if max(error[:98])>ref.D(2e-7) or max(error[98:])>ref.D(2e-10) or max(map(abs,rr[:98]))>ref.D(2e-14) or max(map(abs,rr[98:]))>ref.D(2e-12) or max(map(abs,dd[:98]))>ref.D(2e-10) or max(map(abs,dd[98:]))>ref.D(2e-13) or abs(sum(rr[:98])+ground[i])>ref.D(1e-11) or n['residual_ratio']>1 or n['correction_ratio']>1:raise ValueError('coupled stage root gate')
        ports=[]
        for amp,m in enumerate(inv['opamp_maps']):
            il=m[35];base=m[ref.circuit.op.NODES.index(7)]
            node=lambda k:Z if k==134 else stages[i][k]
            u=(node(m[0])+node(m[1])-node(m[2])-node(m[3]))/2
            current_error=abs(stages[i][il]+gain*u)
            static=node(m[0])+offset-resistance*stages[i][il]
            dynamic=-l/ref.D(h)*sum(ref.B[i][a]*(stages[a][il]-old[il]) for a in range(2))
            identity=abs(stages[i][base]-static-dynamic)
            if current_error>ref.D(2e-14) or identity>ref.D(1e-11):raise ValueError('common-mode coupled history identity')
            ports.append(dict(amp=amp,base_index=base,static_v=str(static),dynamic_v=str(dynamic),base_v=str(stages[i][base]),identity_error_v=str(identity),inductor_constraint_error_a=str(current_error)))
        rows.append(dict(stage=part,ports=ports,max_node_comparison_v=str(max(error[:98])),max_branch_comparison_a=str(max(error[98:])),max_kcl_a=str(max(map(abs,rr[:98]))),max_constraint_v=str(max(map(abs,rr[98:]))),ground_balance_a=str(abs(sum(rr[:98])+ground[i]))))
    return rows


def main():
    out=ROOT/'evidence/voice_vco1_radau_ports01.json'
    if out.exists():raise ValueError('preserve port audit')
    p=json.loads((ROOT/'evidence/voice_vco1_radau_probe01.json').read_text());q=json.loads((ROOT/'evidence/voice_vco1_radau_continuation01.json').read_text());method=json.loads((ROOT/'evidence/voice_vco1_radau_method01.json').read_text())
    names=set(p['source_sha256'])|set(q['source_sha256'])|{'tools/vco1_radau_ports.py','docs/VCO1_RADAU_PUERTO_PROTOCOLO.md','evidence/voice_vco1_radau_probe01.json','evidence/voice_vco1_radau_continuation01.json','evidence/voice_vco1_radau_method01.json'}
    before={n:sha(ROOT/n) for n in names};pdf=method['primary_pdf'];private={pdf['path']:pdf['sha256']}
    record=dict(schema='rf-d/radau-coupled-stage-and-common-mode-audit/v1',passed=False,source_sha256=before,private_input_sha256=private,pairs=[],decompositions=[],new_audio=False,new_spice_processes=0,production_kernel_changed=False)
    def save():out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    save();start=time.perf_counter()
    inv=ref.circuit.inventory(ref.circuit.scenario(C))
    try:
        with localcontext() as ctx:
            ctx.prec=100
            for case in p['cases']:
                old=packed(case['previous_high'],case['previous_low']);parts={}
                for label,h in [('full',2*case['half_dt_s']),('mid',case['half_dt_s']),('end',case['half_dt_s'])]:
                    history=list(map(Decimal,case['steps']['mid']['roots']['endpoint']['independent_decimal'])) if label=='end' else old
                    roots=case['steps'][label]['roots'];rows=check(roots,history,h,inv);parts[label]=rows[1]['ports'][1]
                    record['pairs'].append(dict(scene=case['scene'],power=case['power'],label=label,dt_s=h,rows=rows))
                static=Decimal(parts['full']['static_v'])-Decimal(parts['end']['static_v']);dynamic=Decimal(parts['full']['dynamic_v'])-Decimal(parts['end']['dynamic_v']);actual=Decimal(parts['full']['base_v'])-Decimal(parts['end']['base_v'])
                if abs(actual-static-dynamic)>ref.D(1e-11):raise ValueError('endpoint decomposition')
                record['decompositions'].append(dict(scene=case['scene'],power=case['power'],static_difference_v=str(static),dynamic_difference_v=str(dynamic),base_difference_v=str(actual)))
            for source,items in [('1us',p['actual_intervals']),*[(str(profile['maximum_accepted_half_ticks']),profile['actual_intervals']) for profile in q['profiles']]]:
                for item in items:
                    rows=check(item['roots'],packed(item['previous_high'],item['previous_low']),item['dt_s'],inv)
                    record['pairs'].append(dict(source=source,row_index=item['row_index'],dt_s=item['dt_s'],rows=rows))
        stability=[]
        for z in (0,-1,-10,-100,-4000,-1000000):
            # Exact rational 2x2 solve for stage derivatives of y'=lambda*y.
            a=1-F(z)*F(5,12);b=F(z)*F(1,12);c=-F(z)*F(3,4);d=1-F(z)*F(1,4)
            k1=(d-b)/(a*d-b*c);k2=(a-c)/(a*d-b*c)
            actual=1+F(z)*(F(3,4)*k1+F(1,4)*k2);expected=(1+F(z,3))/(1-F(2*z,3)+F(z*z,6))
            if actual!=expected:raise ValueError('rational stability identity')
            stability.append(dict(z=z,value=str(actual)))
        record.update(passed=True,stage_roots_checked=2*len(record['pairs']),common_mode_identities_checked=4*len(record['pairs']),rational_stability_checks=stability)
    except Exception as exc:record['error']=repr(exc)
    record.update(source_sha256_after={n:sha(ROOT/n) for n in names},private_input_sha256_after={n:sha(ROOT/n) for n in private},wall_s=time.perf_counter()-start)
    record['passed']=record['passed'] and before==record['source_sha256_after'] and private==record['private_input_sha256_after'];save()
    print('Radau stage/port audit',record['passed'],record.get('stage_roots_checked'),record.get('common_mode_identities_checked'),record.get('error',''),flush=True)


if __name__=='__main__':main()
