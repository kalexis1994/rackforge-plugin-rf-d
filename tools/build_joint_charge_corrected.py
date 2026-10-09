"""Export admitted static predictors and derive an unchanged conditioning caller."""
import json
from decimal import Decimal,localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_joint_reference import D
from joint_cycles_analysis import require

def two_sum(a,b):
    s=a+b;v=s-a
    return s,(a-(s-v))+(b-v)

def caller():
    text=(ROOT/'tools/joint_charge_seed_runner.rs').read_text(encoding='utf8');a='../evidence/voice_joint_charge_seed_targets01.txt';require(text.count(a)==1,'one target substitution');return text.replace(a,'../evidence/voice_joint_charge_response_targets01.txt')

def checker():
    text=(ROOT/'tools/check_joint_charge_seed.py').read_text(encoding='utf8')
    old="require(max(abs(a-b) for a,b in zip(oldvolts,targets[0]))<=Decimal('1e-28'),'all historical charges retained')\n    require(all(targets[0][k]==targets[1][k] for k in range(18) if k!=5),'only C27 retargeted')"
    new="prediction=json.loads((ROOT/'evidence/voice_joint_charge_response_fine_reference01.json').read_text());require(prediction['passed'],'admitted predictor')\n    for id in range(2):require(max(abs(a-Decimal(b)) for a,b in zip(targets[id],prediction['records'][id]['predictor']['target_voltages_decimal']))<=Decimal('1e-28'),'exact predicted targets')"
    changes=[(old,new),('voice_joint_charge_seed_targets01.txt','voice_joint_charge_response_targets01.txt'),('preserved_charges_target0=18,preserved_charges_target1=17,retargeted_capacitor_index=5','jointly_corrected_targets=2,static_predictor_is_not_a_periodic_root=True'),('voice_joint_charge_seed_native02.json','voice_joint_charge_corrected_native01.json'),('voice_joint_charge_seed_reference{a.attempt:02d}.json','voice_joint_charge_corrected_reference{a.attempt:02d}.json'),('tools/check_joint_charge_seed.py','tools/check_joint_charge_corrected.py'),('docs/VOZ_CARGAS_SEMILLA_PROTOCOLO.md','docs/VOZ_CARGAS_CORREGIDAS_PROTOCOLO.md'),("'docs/VOZ_CARGAS_CORREGIDAS_PROTOCOLO.md'}","'docs/VOZ_CARGAS_CORREGIDAS_PROTOCOLO.md','evidence/voice_joint_charge_response_fine_reference01.json'}")]
    for a,b in changes:require(a in text,'checker substitution '+a);text=text.replace(a,b)
    return text

def runner():
    text=(ROOT/'tools/run_joint_charge_seed.py').read_text(encoding='utf8')
    changes=[('voice_joint_charge_seed_native','voice_joint_charge_corrected_native'),('joint-charge-seed','joint-charge-corrected'),('voice_joint_conditioned_cycles_tests01.json','voice_joint_seed_cycles_tests01.json'),('tools/run_joint_charge_seed.py','tools/run_joint_charge_corrected.py'),('tools/joint_charge_seed_runner.rs','tools/joint_charge_corrected_runner.rs'),('tools/build_joint_charge_seed_caller.py','tools/build_joint_charge_corrected.py'),('docs/VOZ_CARGAS_SEMILLA_PROTOCOLO.md','docs/VOZ_CARGAS_CORREGIDAS_PROTOCOLO.md'),('voice_joint_charge_seed_targets01.txt','voice_joint_charge_response_targets01.txt'),('voice_joint_charge_seed_targets01.json','voice_joint_charge_response_targets01.json')]
    for a,b in changes:require(a in text,'runner substitution '+a);text=text.replace(a,b)
    return text

def main():
    n='evidence/voice_joint_charge_response_fine_reference01.json';q=json.loads((ROOT/n).read_text());require(q['passed'],'admitted response');rows=[];records=[]
    with localcontext() as ctx:
        ctx.prec=100
        for r in q['records']:
            p=r['predictor'];require(p['admitted'] and len(p['packed_target_pairs'])==36,'invertible target');raw=p['packed_target_pairs']
            for k in range(18):
                h,l=raw[2*k:2*k+2];require(two_sum(h,l)==(h,l),'normalized target pair');require(abs(D(h)+D(l)-Decimal(p['target_voltages_decimal'][k]))<=Decimal('1e-28'),'target high/low reproduction')
            rows.append(' '.join(format(v,'.17e') for v in raw));records.append(dict(id=r['id'],packed_pairs=raw,alpha=p['alpha'],applied_delta_target_v=p['applied_delta_target_v'],phase_held_predictor_only=True))
    require(len(rows)==2,'two memories');path=ROOT/'evidence/voice_joint_charge_response_targets01.txt';require(not path.exists(),'exclusive targets');path.write_text('\n'.join(rows)+'\n',encoding='utf8',newline='\n')
    write('evidence/voice_joint_charge_response_targets01.json',dict(schema='rf-d/joint-charge-response-targets/v1',passed=True,source_sha256={name:sha(ROOT/name) for name in [n,'tools/build_joint_charge_corrected.py']},target_file_sha256=sha(path),records=records,steady_periodicity_admitted=False))
    for name,text in [('tools/joint_charge_corrected_runner.rs',caller()),('tools/check_joint_charge_corrected.py',checker()),('tools/run_joint_charge_corrected.py',runner())]:
        path=ROOT/name;require(not path.exists(),'exclusive corrected source');path.write_text(text,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_charge_corrected_runner.rs text eol=lf\n');print('CHARGE_CORRECTED_PREPARED',flush=True)

if __name__=='__main__':main()
