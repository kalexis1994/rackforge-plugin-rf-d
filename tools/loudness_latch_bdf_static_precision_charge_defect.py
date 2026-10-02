"""Declared exact temporal charge witnesses and nonlinear Peano quadrature."""
import json
from fractions import Fraction as F
from pathlib import Path
from bjt_charge_ngspice_probes import model_parameters
import loudness_latch_bdf_charge_defect as law
from loudness_latch_bdf_static_precision_forced_clock import PATHS as OLD_PATHS
from loudness_latch_bdf_doubling_survey import store
from loudness_latch_increment_probes import hashes
from loudness_lab_metadata import environment

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_defect.json.gz'
SUMMARY=ROOT/'evidence/loudness_latch_bdf_static_precision_charge_defect_summary.json'
PROTOCOL=ROOT/'docs/BIESTABLE_DEFECTO_CARGA_PROTOCOLO.md'
PATHS=tuple(dict.fromkeys((*OLD_PATHS,Path(__file__).resolve(),PROTOCOL,ROOT/'tools/loudness_latch_bdf_charge_defect.py')))
RATIOS=(F(1,4),F(1,2),F(1),F(2))
COUNTS=(32,64,128,256)
PATTERN=(F(1,2),F(3,4),F(1),F(3,2),F(1),F(1,2),F(1,4),F(1,2))


def polynomial_cases():
    rows=[]
    for h in (F(1),F(1,1000)):
        for ratio in RATIOS:
            k=h/ratio;w=law.weights(h,k)
            for degree in range(9):
                q=[F(0)]*degree+[F(1)];qp=law.derivative(q,1)
                discrete=sum((a*law.polynomial(t,q) for a,t in zip(w,(F(0),-h,-h-k))),F(0))
                direct=discrete-law.polynomial(F(0),qp);integral=law.peano_polynomial(h,k,q)
                bound=F(0) if degree<3 else h*(h+k)/6*degree*(degree-1)*(degree-2)*(h+k)**(degree-3)
                rows.append(dict(h_s=law.rational(h),k_s=law.rational(k),degree=degree,
                    direct=law.rational(direct),integral=law.rational(integral),bound=law.rational(bound),
                    exact_identity=direct==integral,bound_passed=abs(direct)<=bound))
    be=[]
    for h in (F(1),F(1,1000)):
        for degree in range(9):
            q=[F(0)]*degree+[F(1)]
            direct=(law.polynomial(F(0),q)-law.polynomial(-h,q))/h-law.polynomial(F(0),law.derivative(q,1))
            integral=law.integrate_product(-h,F(0),{0:F(-1),1:-1/h},law.derivative(q,2))
            be.append(dict(h_s=law.rational(h),degree=degree,direct=law.rational(direct),
                           integral=law.rational(integral),exact_identity=direct==integral))
    return rows,be


def rc_case(variable,startup,resistance):
    c=F(1,100000);r=F(resistance);unit=F(1,100000);poly=[F(1,5),F(1),F(100),F(100000)]
    derivative=law.derivative(poly,1);old=poly[0];older=law.polynomial(-unit,poly)
    old_error=F(0);older_error=F(0);time=F(0);previous_h=unit;rows=[]
    for index in range(64):
        h=unit*(PATTERN[index%len(PATTERN)] if variable else 1);destination=time+h
        is_be=startup and index==0
        if is_be:w=(1/h,-1/h);gamma=F(0);past=(time,)
        else:w=law.weights(h,previous_h);gamma=w[2]/w[0];past=(time,time-previous_h)
        exact=law.polynomial(destination,poly);velocity=law.polynomial(destination,derivative)
        charge=[c*law.polynomial(t,poly) for t in (destination,*past)]
        tau=sum((a*q for a,q in zip(w,charge)),F(0))-c*velocity
        dt=1/w[0];beta,rforce,zforce=law.series_terms(tau,dt,c,r)
        source=exact+r*c*velocity;virtual=old+gamma*(old-older)
        published=beta*source+(1-beta)*virtual
        predicted=(1-beta)*(old_error+gamma*(old_error-older_error))+zforce
        actual=exact-published
        rows.append(dict(index=index,method='BE' if is_be else 'BDF2',time_s=law.rational(destination),
            h_s=law.rational(h),previous_h_s=law.rational(previous_h),gamma=law.rational(gamma),
            exact_v=law.rational(exact),source_v=law.rational(source),published_v=law.rational(published),
            tau_a=law.rational(tau),beta=law.rational(beta),residual_forcing_a=law.rational(rforce),
            publication_forcing_v=law.rational(zforce),actual_error_v=law.rational(actual),
            predicted_error_v=law.rational(predicted),error_without_forcing_v=law.rational(F(0)),exact_error_identity=actual==predicted))
        time=destination;older,old=old,published;older_error,old_error=old_error,predicted;previous_h=h
    return dict(variable_clock=variable,be_startup=startup,capacitance_f=law.rational(c),resistance_ohm=law.rational(r),
                voltage_polynomial=[law.rational(v) for v in poly],rows=rows,exact_identities=all(row['exact_error_identity'] for row in rows))


def generate():
    before=hashes(PATHS);env=environment();poly,be=polynomial_cases()
    rc=[rc_case(variable,startup,r) for variable in (False,True) for startup in (False,True) for r in (0,25500)]
    params=model_parameters(1,'finite_transit');profiles=[]
    for junction in ('be','bc'):
        for bias in (.12,.55):
            for ratio in RATIOS:
                for h in (F(1,10000),F(1,20000)):
                    k=h/ratio;direct=law.nonlinear_defect(params,junction,bias,h,k,80)
                    direct100=law.nonlinear_defect(params,junction,bias,h,k,100);levels=[]
                    for count in COUNTS:
                        value=law.nonlinear_integral(params,junction,bias,h,k,count,80)
                        level=dict(count=count,integral_a=str(value),comparison=law.precision_metric(direct,value))
                        if count==COUNTS[-1]:
                            high=law.nonlinear_integral(params,junction,bias,h,k,count,100)
                            level.update(integral100_a=str(high),precision=law.precision_metric(value,high))
                        levels.append(level)
                    profiles.append(dict(junction=junction,bias_v=bias,h_s=law.rational(h),k_s=law.rational(k),
                        defect80_a=str(direct),defect100_a=str(direct100),precision=law.precision_metric(direct,direct100),
                        levels=levels,declared_final_quadratures_passed=all(row['comparison']['passed'] for row in levels[-2:])))
            print(json.dumps(dict(junction=junction,bias_v=bias,profiles=len(profiles),
                final_quadratures_passed=sum(p['declared_final_quadratures_passed'] for p in profiles))),flush=True)
    if hashes(PATHS)!=before:raise ValueError('charge-defect witness inputs changed')
    return dict(schema='rf-d/bdf-static-charge-defect/v1',source_sha256=before,environment=env,
        polynomial_cases=poly,be_cases=be,rc_cases=rc,nonlinear_profiles=profiles,
        simpson_counts=COUNTS,absolute_gate_a=1e-30,relative_gate=1e-8,new_nonlinear_solves=0,
        diagnostic_only=True,manufactured_solutions_known=True,parameters_synthetic=True,
        circuit_temporal_defect_known=False,temporal_error_bound_admitted=False,integrator_changed=False,
        physical_switching_admitted=False,audio_admitted=False,deadline_admitted=False,
        limitation='exact scalar charge witnesses and smooth manufactured QBE/QBC profiles; no bound on actual RF-D Q derivatives or switching intervals')


def save(report):
    storage=store(report,OUTPUT)
    summary={k:v for k,v in report.items() if k not in ('polynomial_cases','be_cases','rc_cases','nonlinear_profiles')}
    summary.update(storage=storage,polynomial_count=len(report['polynomial_cases']),
        polynomial_identities=sum(r['exact_identity'] for r in report['polynomial_cases']),
        be_count=len(report['be_cases']),be_identities=sum(r['exact_identity'] for r in report['be_cases']),
        rc_cases=len(report['rc_cases']),rc_steps=sum(len(c['rows']) for c in report['rc_cases']),
        rc_identities=sum(r['exact_error_identity'] for c in report['rc_cases'] for r in c['rows']),
        nonlinear_profiles=[dict(junction=p['junction'],bias_v=p['bias_v'],h_s=p['h_s'],k_s=p['k_s'],
            defect80_a=p['defect80_a'],precision=p['precision'],levels=p['levels'],
            declared_final_quadratures_passed=p['declared_final_quadratures_passed']) for p in report['nonlinear_profiles']])
    SUMMARY.write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    return summary


if __name__=='__main__':save(generate())
