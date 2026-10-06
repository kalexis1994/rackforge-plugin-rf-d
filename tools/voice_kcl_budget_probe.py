"""Repeat only the wall-limited positive control, with the same observer binary."""
import json
from pathlib import Path
import voice_kcl_budget_runner as runner
import voice_kcl_alias_instrument as instrument
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=instrument.WORK


def main():
    output=ROOT/'evidence/voice_kcl_runs03.json'
    if output.exists():raise ValueError('preserve previous experiment')
    old=ROOT/'tools/voice_newton_probe.py';new=Path(runner.__file__)
    if new.read_bytes()!=old.read_bytes().replace(b'timeout=120',b'timeout=240',1):raise ValueError('wall budget is the only runner edit')
    bank=vco.read(ROOT/'evidence/voice_kcl_runs02.json')
    rejected=bank['records']['kcl-alias-on-constant']
    if not rejected.get('timeout') or rejected['trajectory_complete']:raise ValueError('preserved wall rejection')
    runner.WORK=WORK
    helpers=(Path(__file__),new,old)
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    r=runner.run(WORK/'bin/observer.exe','constant','kcl-budget-on-constant',True)
    if r['exe_sha256']!=rejected['exe_sha256']:raise ValueError('same executable required')
    records=dict(bank['records']);records['kcl-alias-on-constant']=r
    after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/kcl-budget-probe-runs/v1',records=records,wrapper_sha256=before,wrapper_sha256_after=after,
        inherited_bank_sha256=vco.sha(ROOT/'evidence/voice_kcl_runs02.json'),wall_rejection_sha256=vco.sha(ROOT/'evidence/voice_kcl_budget_rejection01.json'),
        new_solves=1,inherited_solves=3,wall_limit_s=240,circuit_equations_changed=False,solver_tolerances_changed=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
