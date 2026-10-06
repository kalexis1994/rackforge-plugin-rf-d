"""Use the frozen runner with a separately identified working directory."""
import json
from pathlib import Path
import voice_newton_probe as runner
import voice_inductor_instrument as instrument
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=instrument.WORK


def main():
    output=ROOT/'evidence/voice_inductor_runs01.json'
    if output.exists():raise ValueError('preserve previous experiment')
    # Only output/runtime locations change. The frozen original() and run() generate all decks.
    runner.WORK=WORK
    helpers=(Path(__file__),Path(instrument.__file__))
    before={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers};records={}
    for kind in ('constant','returned'):
        for enabled in (False,True):
            label=('inductor-on-' if enabled else 'inductor-off-')+kind
            records[label]=runner.run(WORK/'bin/observer.exe',kind,label,enabled)
    after={p.relative_to(ROOT).as_posix():vco.sha(p) for p in helpers}
    report=dict(schema='rf-d/inductor-probe-runs/v1',records=records,wrapper_sha256=before,wrapper_sha256_after=after,
                frozen_runner_sha256=vco.sha(Path(runner.__file__)),new_solves=4,
                coupling_admitted=False,physical_fidelity=False,real_time=False)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
