"""Run the frozen scenarios with the separately identified KCL observer."""
import json
from pathlib import Path
import voice_newton_probe as runner
import voice_kcl_instrument as instrument
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=instrument.WORK


def main():
    output=ROOT/'evidence/voice_kcl_runs01.json'
    if output.exists():raise ValueError('preserve previous experiment')
    runner.WORK=WORK
    helpers=(Path(__file__),Path(instrument.__file__))
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers};records={}
    for kind in ('constant','returned'):
        for enabled in (False,True):
            label=('kcl-on-' if enabled else 'kcl-off-')+kind
            records[label]=runner.run(WORK/'bin/observer.exe',kind,label,enabled)
    after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    output.write_text(json.dumps(dict(schema='rf-d/kcl-probe-runs/v1',records=records,wrapper_sha256=before,
        wrapper_sha256_after=after,frozen_runner_sha256=vco.sha(Path(runner.__file__)),new_solves=4,
        coupling_admitted=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
