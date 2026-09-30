"""Reproduce the first unresolved latch fold, with an independent FD Jacobian."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from loudness_contour_reference import GRAPH, Controls, Semiconductors, Network

OUTPUT = Path(__file__).resolve().parents[1]/"evidence/loudness_contour_fold.json"


def generate():
    network = Network()
    analytical, da = network.initial_state()
    independent, df = network.initial_state(use_fd=True)
    worst = max(abs(analytical.node_v[n]-independent.node_v[n]) for n in network.nodes)
    rows = []
    for sample in range(12):
        source = 10.0 if sample >= 10 else 0.0
        analytical, da = network.step(analytical, source, .001)
        independent, df = network.step(independent, source, .001, use_fd=True)
        worst = max(worst, max(abs(analytical.node_v[n]-independent.node_v[n])
                               for n in network.nodes))
        rows.append(dict(sample=sample, keyboard_v=source, dt_s=.001,
                         independent_state=asdict(independent),
                         analytic_diagnostics=da, fd_diagnostics=df))
    roots = network.probe_step_roots(analytical, 10.0, .001)
    fd_roots = network.probe_step_roots(independent, 10.0, .001, use_fd=True)
    if len(roots["roots"]) != 2 or len(fd_roots["roots"]) != 2:
        raise ValueError("documented fold no longer has two independently reproduced roots")
    for a in roots["roots"]:
        error = min(max(abs(a["state"].node_v[n]-f["state"].node_v[n])
                        for n in network.nodes) for f in fd_roots["roots"])
        worst = max(worst, error)
    separation = max(abs(roots["roots"][0]["state"].node_v[n]
                         -roots["roots"][1]["state"].node_v[n]) for n in network.nodes)
    if worst >= 1e-6 or separation <= 1.0:
        raise ValueError("root-reproduction or ambiguity gate failed")
    return dict(schema=1, reference_kind="isolated conditioned circuit; unresolved latch switching",
                graph_sha256=hashlib.sha256(GRAPH.read_bytes()).hexdigest(),
                controls=asdict(Controls()), semiconductors=asdict(Semiconductors()),
                node_order=network.nodes, prefix=rows,
                fold=dict(sample=12, keyboard_v=10.0, dt_s=.001,
                          analytic=asdict_roots(roots), independent_fd=asdict_roots(fd_roots)),
                max_analytic_vs_fd_node_error_v=worst,
                max_root_separation_v=separation,
                numerical_reproduction_passed=True, physical_switching_admitted=False,
                audio_admitted=False)


def asdict_roots(probe):
    return dict(selected=None, rejected=probe["rejected"], roots=[
        dict(state=asdict(r["state"]), diagnostics=r["diagnostics"], seed_policy=r["seed_policy"])
        for r in probe["roots"]])


if __name__ == "__main__":
    result = generate()
    OUTPUT.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k.endswith("_v") or k.endswith("passed")
                      or k.endswith("admitted")}))
