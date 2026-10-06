"""Postprocess captured roots: one binary64 publication and cross-iteration identity."""
import json
from decimal import Decimal, localcontext
from pathlib import Path
import voice_matrix_build_retry as build
import voice_matrix_trace as trace
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def rounded(s,analysis):
    with localcontext() as ctx:
        ctx.prec=120
        x=[trace.exact(float(Decimal(row['precise']))) for row in analysis['rows']]
        residual=[-trace.exact(s['nodes'][i]['b']) for i in range(s['n'])]
        for (i,j),v in s['entries'].items():residual[i]+=trace.exact(v)*x[j]
        rows=[]
        for i,row in enumerate(analysis['rows']):
            rows.append(dict(index=i,node=row['node'],unknown_unit=row['unknown_unit'],row_unit=row['row_unit'],
                rounded_solution=float(x[i]),rounding_error=str(x[i]-Decimal(row['precise'])),
                residual=str(residual[i]),observed_residual=row['observed_residual']))
        maxima={}
        for unit in ('V','A'):
            r=max((r for r in rows if r['row_unit']==unit),key=lambda r:abs(Decimal(r['residual'])))
            u=max((r for r in rows if r['unknown_unit']==unit),key=lambda r:abs(Decimal(r['rounding_error'])))
            maxima[unit]=dict(max_rounded_residual=r['residual'],at_row=r['node'],max_rounding_error=u['rounding_error'],at_unknown=u['node'])
        return dict(iteration=s['iteration'],time_s=s['time_s'],h_s=s['h_s'],rows=rows,maxima=maxima)

def decompose(first,last,name):
    a=next(r for r in first['rows'] if r['node']==name);b=next(r for r in last['rows'] if r['node']==name)
    with localcontext() as ctx:
        ctx.prec=120
        observed=trace.exact(b['observed'])-trace.exact(a['observed'])
        precise=Decimal(b['precise'])-Decimal(a['precise'])
        errors=Decimal(b['observed_minus_precise'])-Decimal(a['observed_minus_precise'])
        defect=observed-precise-errors
        if abs(defect)>Decimal('1e-110'):raise ValueError('cross-iteration decomposition failed')
        return dict(node=name,unknown_unit=a['unknown_unit'],observed_change=str(observed),precise_roots_change=str(precise),
            linear_error_change=str(errors),identity_residual=str(defect),
            scope='two different captured systems; precise roots already contain rounded device stamps; not a nonlinear trajectory')

def main():
    output=ROOT/'evidence/voice_matrix_rounding01.json'
    if output.exists():raise ValueError('preserve postprocessing')
    audit_path=ROOT/'evidence/voice_matrix_observation01.json';audit=vco.read(audit_path)
    if not audit['passed'] or len(audit['analyses'])!=2:raise ValueError('this bank requires the two selected roots')
    record=audit['records']['matrix-on-returned'];log=build.WORK/'runs/matrix-on-returned.log'
    if vco.sha(log)!=record['log_sha256']:raise ValueError('captured matrix identity')
    snapshots=trace.parse(log.read_text(encoding='utf-8'));analyses=audit['analyses']
    for s,a in zip(snapshots,analyses):
        if (s['iteration'],s['h_s'],s['time_s'])!=(a['iteration'],a['h_s'],a['time_s']):raise ValueError('snapshot order')
    roots=[rounded(s,a) for s,a in zip(snapshots,analyses)]
    if [a['iteration'] for a in analyses]!=[100,101] or analyses[0]['time_s']!=analyses[1]['time_s'] or analyses[0]['h_s']!=analyses[1]['h_s']:raise ValueError('shared attempt')
    decomposition=[decompose(*analyses,name) for name in ('xic3.16','xic3.17','xic3.3','xic3.7','l.xic3.l2#branch')]
    helpers=[Path(__file__),Path(trace.__file__)];before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/newton-matrix-rounding/v1',passed=True,audit_sha256=vco.sha(audit_path),log_sha256=vco.sha(log),
        rounded_roots=roots,decomposition=decomposition,source_sha256=before,
        source_sha256_after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers},
        new_solves=0,root_solves_inherited=4,new_spice_solves=0,
        publication='round each 120-digit root once to nearest binary64 via Python float; analyze exact resulting floats',
        component_evaluation_changed=False,independent_nonlinear_root=False,
        coupling_admitted=False,physical_fidelity=False,real_time=False,new_audio=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    for root in roots:print(root['iteration'],root['maxima'],flush=True)
    for r in decomposition:print(r['node'],float(Decimal(r['observed_change'])),float(Decimal(r['precise_roots_change'])),float(Decimal(r['linear_error_change'])),flush=True)

if __name__=='__main__':main()
