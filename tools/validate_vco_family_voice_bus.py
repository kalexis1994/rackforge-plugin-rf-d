"""Bind the prepared H128 port to two loaded voice histories and check their reserves."""
import argparse
import json
import os
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest
from check_vco_phase import COMPILER, LIB
from check_vco_family_voice_bus import PREFIX, PROTOCOL, RESERVED
from check_vco_family_voice_bus_model import AREA, ORACLE, materialize, read_oracle
from prepare_dual_chain import ROOT, sha, write
from prepare_vco_family_voice_bus import TABLE, prediction
from vco_family import ports
from vco_family_voice_bus_receipts import archive_members, read_receipt, receipt_bytes

OWN = "tools/validate_vco_family_voice_bus.py"
PROBE = "tools/vco_family_voice_bus_probe.rs"
KERNEL = "tools/vco_family_voice_bus_kernel.rs"
COUPLED = "tools/vco_family_voice_bus_coupled.rs"
MODEL = PREFIX + "_model01.json"
CRATE = "crates/rf-d-circuit/src/"
VOICE_REF = "evidence/recovery_engine128_mono02.json"
DUAL_REF = "evidence/dual_voice_native02.json"
PATHS = {
    "COUPLED_PATH": COUPLED,
    "GRAPH_PATH": CRATE + "incidence_voice_chain.rs",
    "DENSE_PATH": CRATE + "dual_voice_chain.rs",
    "SOLVER_PATH": CRATE + "incidence_hybrid_solver.rs",
    "INCIDENCE_PATH": CRATE + "incidence_matrix.rs",
    "PATCH_PATH": "crates/rf-d-circuit/tests/support/mixer_chain_lab.rs",
}
PANEL = CRATE + "vco_panel_port.rs"
N = 118
C2, C5, BUS, J7 = 5, 38, 116, 115


def read(name):
    return json.loads((ROOT / name).read_bytes())


def histories():
    report = read(VOICE_REF)
    data = unpack(report["node"]["rows"])
    negative = data[:2 * N * 8]
    dual = read(DUAL_REF)
    source = dual["output_directory"] + "/profile-524288.stdout"
    raw = (ROOT / source).read_bytes()
    assert digest(raw) == dual["private_sha256"][source] == dual["profiles"][1]["stdout_sha256"]
    line, = [line for line in raw.splitlines() if line.startswith(b"GRID,3145728000,")]
    rows = np.asarray(line.split(b",")[2:502], dtype="f8").reshape(2, 250)
    mapping = [12 if k == 116 else 133 + k if k < 116 else 249 for k in range(N)]
    positive = np.asarray(rows[:, mapping], "<f8").tobytes()
    for raw, sign in ((negative, -1.), (positive, 1.)):
        data = np.frombuffer(raw, "<f8").reshape(2, N)
        assert .89 < sign * float(data[0, BUS] + data[1, BUS]) < 1.
    return dict(negative=negative, positive=positive), {source: sha(ROOT / source)}


def port_input():
    phases = np.r_[0., 1., (np.arange(0, 4096, 32) + .5) / 4096.]
    data = [(cv, bus, float(phase)) for cv, bus in (*RESERVED, (-3.1, -1.), (-.1, 1.),
                                                  (-1.6, -.125), (-1.6, .125))
            for phase in phases]
    bad = [(float("nan"), 0., 0.), (-3.2, 0., 0.), (0., 0., 0.), (-2.1, -1.001, 0.),
           (-2.1, 1.001, 0.), (-2.1, 0., -1e-5), (-2.1, 0., 1.01), (-2.1, float("inf"), 0.)]
    return data, bad


def check_ports(result, data, bad, frequency, model):
    lines = result.decode().splitlines()
    assert len(lines) == len(data) + len(bad) and lines[len(data):] == ["REJECT"] * len(bad)
    max_error = np.zeros(6)
    cache = {}
    for (cv, bus, phase), line in zip(data, lines):
        tag, *fields = line.split(",")
        assert tag == "PORT" and len(fields) == 10
        n = np.array(fields, dtype="f8")
        assert np.isfinite(n).all()
        key = (cv, bus)
        if key not in cache:
            cache[key] = prediction(frequency, model, cv, bus)
        fit = cache[key]
        harmonics = np.arange(129)
        basis = np.exp(2j * np.pi * harmonics * phase)
        basis[1:] *= 2.
        saw = float(np.real(fit["c"][0] @ basis))
        saw_phase = float(np.real(fit["c"][0] @ (basis * 2j * np.pi * harmonics)))
        saw_bus = float(np.real(fit["dbus"][0] @ basis))
        _, terminal, _, power = ports(saw, 0., cv, bus)
        frequency_error = abs(n[0] - fit["frequency_hz"])
        # Rebuild the panel from the reported saw to check KCL and energy separately.
        _, measured_terminal, _, measured_power = ports(n[2], 0., cv, bus)
        assert abs(sum(n[4:7])) <= 1e-18
        assert max(abs(n[4:7] - measured_terminal)) <= 1e-18
        assert abs(n[9] - measured_power) <= 1e-18
        derivative = 1. / 39250. - .5 * saw_bus / 39250.
        max_error = np.maximum(max_error, [
            frequency_error, abs(n[2] - saw), max(abs(n[4:7] - terminal)),
            abs(n[3] - saw_phase), abs(n[7] - derivative), abs(n[9] - power),
        ])
    assert np.all(max_error[:5] <= [1e-8, 2e-6, 2e-9, .1, 1e-10]), max_error
    return dict(valid=len(data), rejected=len(bad), maximum_error=max_error.tolist())


def parse_branch(raw):
    grid = []
    for line in raw.decode().splitlines():
        kind, *items = line.split(",")
        if kind == "GRID":
            frame, phase, r59, r60, *volts = items
            assert int(frame) == len(grid)
            state = np.asarray([int(item, 16) for item in volts], "<u8").view("<f8").reshape(2, N)
            grid.append((float(phase), float(r59), float(r60), state))
        else:
            assert kind == "END" and len(grid) == 129
            subdivisions, iterations = map(int, items[:2])
            duration, residual, correction, low, high, j7, current, charge, c27, tangent, panel = map(float, items[2:13])
            retries, deepest = map(int, items[13:])
    assert residual <= 1e-12 and correction <= 2e-9
    assert max(current, charge, c27) <= 2e-11 and tangent <= 1. and panel <= 1e-18, (current, charge, c27, tangent, panel)
    assert -1. <= low <= high <= 1.
    return dict(subdivisions=subdivisions, iterations=iterations, duration_s=duration, residual_a=residual,
                correction_v=correction, bus_v=[low, high], final_j7_v=j7,
                dense_kcl_error_a=current, dense_charge_error_a=charge, c27_error_a=c27,
                bus_tangent_error_gate_fraction=tangent, panel_error_a=panel,
                rejected_substeps=retries, maximum_halvings=deepest), grid


def refinement(coarse, fine):
    a = np.asarray([row[3] for row in coarse])
    b = np.asarray([row[3] for row in fine])
    diff = (a[:, 0] - b[:, 0]) + (a[:, 1] - b[:, 1])
    ref = b.sum(axis=1)
    state_gate = float(np.max(abs(diff) / (20e-6 + 2e-6 * abs(ref))))
    loads = np.asarray([row[1:3] for row in fine])
    delta = np.asarray([row[1:3] for row in coarse]) - loads
    load_gate = float(np.max(abs(delta) / (2e-9 + 2e-5 * abs(loads))))
    phase_delta = np.asarray([x[0] - y[0] for x, y in zip(coarse, fine)])
    phase_error = float(max(abs((phase_delta + .5) % 1. - .5)))
    return dict(nodal_gate_fraction=state_gate, contour_return_gate_fraction=load_gate,
                phase_error_cycles=phase_error, c2_error_v=float(max(abs(diff[:, C2]))),
                c5_error_v=float(max(abs(diff[:, C5]))), bus_error_v=float(max(abs(diff[:, BUS]))),
                passed=state_gate <= 1. and load_gate <= 1.)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positive-refinement", type=int, choices=(128, 256))
    options = parser.parse_args()
    assert {x.name for x in AREA.iterdir()} <= {TABLE}
    number = 1
    archived = archive_members()
    while (ROOT / f"{PREFIX}_coupled{number:02}.json").exists() or f"{PREFIX}_coupled{number:02}.json" in archived:
        number += 1
    out = ROOT / f"{PREFIX}_coupled{number:02}.json"
    model = read(MODEL)
    sources = Sources([OWN, PROBE, KERNEL, COUPLED, PANEL, PROTOCOL, *PATHS.values()])
    report = dict(passed=False, **sources.fields(), model_sha256=sha(ROOT / MODEL),
                  traces=[], compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB))
    command, last, stdin = [], None, None
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])

    def run(args, input_bytes=None, timeout=150):
        nonlocal command, last, stdin
        command, last, stdin = list(map(str, args)), None, input_bytes
        last = subprocess.run(command, input=stdin, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
        return dict(command=command, exit_code=last.returncode, stdout=packed(last.stdout), stderr=packed(last.stderr))

    try:
        assert model["passed"]
        table, frequency, wave, cases, _, _ = materialize(read_oracle())
        assert cases == model["validation"] and digest(table) == model["table_sha256"]
        table_path = AREA / TABLE
        table_path.write_bytes(table)
        kernel = AREA / "family-kernel.rs"
        kernel.write_text((ROOT / KERNEL).read_text(encoding="utf8").replace(
            "H128_VOICE_TABLE_PATH", table_path.as_posix()).replace("VCO_PANEL_PORT_PATH", (ROOT / PANEL).as_posix()),
            encoding="utf8", newline="\n")
        probe = AREA / "family-probe.rs"
        text = (ROOT / PROBE).read_text(encoding="utf8").replace("FAMILY_KERNEL_PATH", kernel.as_posix())
        for slot, path in PATHS.items():
            text = text.replace(slot, (ROOT / path).as_posix())
        probe.write_text(text, encoding="utf8", newline="\n")
        exe = AREA / "family-voice.exe"
        report["compile"] = run([COMPILER, "--edition=2021", "-C", "opt-level=3",
                                 "-C", "link-arg=-Wl,--stack,33554432", "-A", "dead_code", probe,
                                 "--extern", f"rf_d_circuit={LIB}", "-o", exe])
        assert last.returncode == 0, last.stderr.decode(errors="replace")
        report["table_sha256"] = sha(table_path)
        data, bad = port_input()
        raw_input = "".join(f"{cv} {bus} {phase}\n" for cv, bus, phase in (*data, *bad)).encode()
        report["port_capture"] = run([exe, "ports"], raw_input)
        assert last.returncode == 0, last.stderr.decode(errors="replace")
        report["port_capture"]["metrics"] = check_ports(last.stdout, data, bad, frequency, wave)
        print("H128_VOICE_PORT", report["port_capture"]["metrics"], flush=True)
        states, referenced = histories()
        report["private_input_sha256"] = referenced
        if options.positive_refinement is None:
            pairs = (32, 64)
        else:
            states = {"positive": states["positive"]}
            pairs = (options.positive_refinement, 2 * options.positive_refinement)
        for label, raw in states.items():
            trace = dict(case=label, history=packed(raw), runs=[])
            report["traces"].append(trace)
            history = AREA / "history.bin"
            history.write_bytes(raw)
            grids = []
            if options.positive_refinement == 256:
                prior_path = PREFIX + "_coupled03.json"
                prior = read_receipt(prior_path)
                previous, = prior["traces"]
                assert prior["passed"] and previous["case"] == label
                assert previous["history"] == trace["history"] and not previous["refinement"]["passed"]
                assert prior["table_sha256"] == report["table_sha256"]
                for key in ("compiler_sha256", "library_sha256"):
                    assert prior[key] == report[key]
                for key in (PROBE, KERNEL, COUPLED, PANEL, *PATHS.values()):
                    assert prior["source_sha256"][key] == report["source_sha256"][key]
                fine = previous["runs"][1]
                metrics, coarse_grid = parse_branch(unpack(fine["stdout"]))
                assert metrics["subdivisions"] == 256 and fine["metrics"] == metrics
                grids.append(coarse_grid)
                trace["reused_coarse"] = dict(path=prior_path, sha256=digest(receipt_bytes(prior_path)), run=1)
                pairs = (512,)
            for subdivisions in pairs:
                item = run([exe, "branch", history, label, subdivisions])
                trace["runs"].append(item)
                assert last.returncode == 0, last.stderr.decode(errors="replace")
                item["metrics"], grid = parse_branch(last.stdout)
                assert grid[0][3].tobytes() == raw
                grids.append(grid)
                print("H128_VOICE_BRANCH", label, item["metrics"], flush=True)
            trace["refinement"] = refinement(*grids)
            print("H128_VOICE_REFINE", label, trace["refinement"], flush=True)
        report["passed"] = True
        report["loaded_reserves_passed"] = all(item["refinement"]["passed"] for item in report["traces"])
        report["rt_admitted"] = False
    except Exception:
        report["failure"] = traceback.format_exc()
        if command:
            if last is not None:
                report["failed_process"] = dict(exit_code=last.returncode, stdout=packed(last.stdout), stderr=packed(last.stderr))
            try:
                report["unchanged_replay"] = run(command, stdin)
            except subprocess.TimeoutExpired:
                report["unchanged_replay"] = dict(timeout=True)
    finally:
        write(out, report)
        for path in AREA.iterdir():
            if path.name != TABLE:
                assert path.is_file() and path.resolve().parent == AREA.resolve()
                path.unlink()
        sources.unchanged()
        report["runtime_retired"] = {path.name for path in AREA.iterdir()} <= {TABLE}
        write(out, report)
    print("H128_VOICE_COUPLED", report["passed"], report.get("loaded_reserves_passed"), report.get("failure", ""), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
