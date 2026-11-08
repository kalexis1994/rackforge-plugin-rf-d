"""Contrast the first staged pilot return ports and benchmark the same scene."""
import math
import os
import re
import subprocess
import traceback
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_cost import digest
from check_rf_d_reduced_voice import (
    AREA, DATA, FIR, PLANT, PROBE as PILOT_PROBE, TIMING, VOICE, emit, pin, score,
)
from check_vco_family_voice_bus_model import materialize, read_oracle
from check_vco_phase import COMPILER, LIB
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_rf_d_pilot_returns import LAWS, OWN as MAP_TOOL, emit_data
from prepare_vco_family_voice_bus import prediction
from recovery_port_input_model import cases
from validate_vco_family_voice_bus import MODEL, read

OWN = "tools/check_rf_d_pilot_returns.py"
DOC = "docs/VOZ_PILOTO_RETORNOS_PROTOCOLO.md"
PORT_PLANT = "tools/rf_d_pilot_return_plant.rs"
SCENE = "tools/rf_d_pilot_returns_scene.rs"
PROBE = "tools/rf_d_pilot_returns_probe.rs"
ORACLE = "tools/rf_d_pilot_returns_oracle.rs"
SOURCES = (OWN, DOC, PORT_PLANT, SCENE, PROBE, ORACLE, MAP_TOOL, VOICE, DATA, FIR, PLANT, PILOT_PROBE,
           TIMING, "tools/vco_cv_load_linear.rs", "crates/rf-d-circuit/src/chain_charge.rs",
           "crates/rf-d-circuit/src/circuit66.rs", "crates/rf-d-circuit/src/cutoff.rs",
           "crates/rf-d-circuit/tests/support/mixer_chain_lab.rs", "tools/recovery_port_input_model.py",
           "tools/prepare_charge_reduced.py", "tools/check_rf_d_reduced_voice.py")
LENGTH = 48_128
RATE = 192_000


def generate():
    table, logs, models, *_ = materialize(read_oracle())
    assert digest(table) == read(MODEL)["table_sha256"]
    z = prediction(logs, models, -1.6, 0.)["c"][0].copy()
    z[1:] *= 2.
    cycle = np.fft.ifft(z, n=4096).real * 4096
    wave = emit("pilot-wave.rs", "pub const SAW:[f64;4096]=[" +
                ",".join(f"{v:.17e}" for v in cycle / max(abs(cycle))) + "];\n")
    bank = AREA / "pilot-return-maps.rs"
    checks = emit_data(bank, 1. / RATE)
    old = (ROOT / PLANT).read_text(encoding="utf8")
    start, end = old.index("pub fn law("), old.index("// The physical state")
    law = once(old[start:end], "index:usize,", "")
    law = law.replace("data::IEXP[index]", "crate::return_maps::IEXP")
    law = re.sub(r"\b12\b", str(LAWS), law)
    solve = law.index("fn solve(")
    law = law[:solve] + "pub " + re.sub(r"\b6\b", str(LAWS // 2), law[solve:])
    error = next(line for line in old.splitlines() if "pub enum Error" in line)
    law = emit("pilot-law.rs", error + "\n" + law)
    events = []
    for at, status, note in score():
        message = {0x90: f"NoteOn({note})", 0x80: f"NoteOff({note})", 0xb0: "AllNotesOff"}[status]
        events.append(f"Event {{ offset: {at}, message: {message} }}")
    compiled_score = emit("pilot-score.rs", "use crate::voice::{Event, Message::*};\n"
                          "pub const SCENE:[Event;8]=[" + ",".join(events) + "];\n")
    parts = dict(wave=wave, return_maps=bank, pilot_law=law, score=compiled_score, voice=ROOT / VOICE,
                 coefficients=ROOT / FIR, scene=ROOT / SCENE, plant=ROOT / PORT_PLANT)
    code = "".join(f'#[path = "{path.as_posix()}"] mod {name};\n' for name, path in parts.items())
    return code, dict(map_checks=checks, maps_sha256=sha(bank), wave_sha256=sha(wave), h128_sha256=digest(table))


def drives(t, kind):
    w = 2. * math.pi * t
    audio = .055 * np.sin(211 * w) + .015 * np.sin(817 * w)
    volume = .009 * np.sin(331 * w) + .004 * np.sin(719 * w)
    cutoff = .00065 * np.sin(407 * w) - .00022 * np.sin(967 * w)
    if kind == "volume":
        cutoff *= 0.
    if kind == "filter":
        volume *= 0.
    return np.column_stack((audio, volume, cutoff))


def compare(candidate, reference):
    error = candidate - reference
    maximum = np.max(abs(error), axis=0)
    limits = np.array([0., 20e-6, 20e-6, 2e-9, 2e-9, 2e-9])
    limits[1:4] += .01 * np.ptp(reference[:, 1:4], axis=0)
    rms = float(np.linalg.norm(error[:, 0]) / np.linalg.norm(reference[:, 0]))
    peak = float(maximum[0] / max(abs(reference[:, 0])))
    mean = float(abs(np.mean(error[:, 0])))
    passed = bool(np.all(maximum[1:] <= limits[1:]) and rms <= .003 and peak <= .01 and mean <= 1e-6)
    return dict(passed=passed, maximum=maximum.tolist(), limits=limits.tolist(),
                j7_rms_relative=rms, j7_peak_relative=peak, j7_mean_v=mean)


def main():
    assert not list(AREA.iterdir())
    seq = 1
    while (output := ROOT / f"evidence/rf_d_pilot_returns{seq:02}.json").exists():
        seq += 1
    sources = Sources(SOURCES)
    report = dict(passed=False, full_contours_integrated=False, physical_measured=False, **sources.fields(),
                  compiler_sha256=sha(Path(COMPILER)), library_sha256=sha(LIB), builds={}, scenes={}, native={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    last = None

    def run(args, payload=None):
        nonlocal last
        command = list(map(str, args))
        proc = subprocess.run(command, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=120)
        last = command, payload, proc
        receipt = dict(command=command, exit_code=proc.returncode, stderr=packed(proc.stderr),
                       stdout_sha256=digest(proc.stdout), stdout_bytes=len(proc.stdout))
        assert proc.returncode == 0, proc.stderr.decode(errors="replace")
        return proc.stdout, proc.stderr, receipt

    try:
        code, report["maps"] = generate()
        flags = [COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                 "-A", "dead_code", "-C", "link-arg=-Wl,--stack,33554432"]
        report["affinity"] = pin()
        candidate = AREA / "pilot-returns.exe"
        root = emit("returns-probe.rs", code + f'\n#[path = "{(ROOT / PROBE).as_posix()}"] mod probe;\n'
                    "fn main() -> Result<(), Box<dyn std::error::Error>> { probe::main() }\n")
        *_, report["builds"]["candidate"] = run([*flags, "--cfg", "pilot_returns", root, "-o", candidate])
        oracle = AREA / "pilot-returns-oracle.exe"
        *_, report["builds"]["oracle"] = run([*flags, ROOT / ORACLE, "--extern", f"rf_d_circuit={LIB}", "-o", oracle])
        dc = np.asarray(cases()[1]["DC"], dtype="<f8")
        samples = 128 * 4
        for kind in ("volume", "filter", "both"):
            sampled = drives(np.arange(1, samples + 1) / RATE, kind)
            data, _, run_record = run([candidate, "electrical"], sampled.astype("<f8").tobytes())
            trial = np.frombuffer(data, "<f8").reshape(samples, 6)
            entry = dict(candidate=run_record, reference={})
            report["scenes"][kind] = entry
            fine = {}
            for factor in (2, 4):
                ticks = np.arange(samples * factor)
                stage = drives((ticks + 1. / 3.) / (RATE * factor), kind)
                end = drives((ticks + 1.) / (RATE * factor), kind)
                payload = dc.tobytes() + np.column_stack((stage, end)).astype("<f8").tobytes()
                data, _, record = run([oracle, RATE * factor], payload)
                fine[factor] = np.frombuffer(data, "<f8").reshape(samples * factor, 6)[factor - 1::factor]
                entry["reference"][str(factor)] = record
            entry["refinement"] = compare(fine[2], fine[4])
            entry["comparison"] = compare(trial, fine[4])
            print("PILOT_RETURNS_ELECTRICAL", kind, entry["refinement"], entry["comparison"], flush=True)
        # Preserve the previous published pilot as a separate build and control.
        from check_rf_d_reduced_voice import rate_maps
        base_maps = emit("pilot-baseline-maps.rs", rate_maps()[0])
        base_plant = emit("pilot-baseline-plant.rs", once((ROOT / PLANT).read_text(encoding="utf8"),
                          '"recovery_cost_exp_data.rs"', f'"{base_maps.as_posix()}"'))
        baseline_src = (ROOT / PILOT_PROBE).read_text(encoding="utf8")
        for token, path in (("PLANT_PATH", base_plant), ("WAVE_PATH", AREA / "pilot-wave.rs"),
                            ("VOICE_PATH", ROOT / VOICE), ("FIR_PATH", ROOT / FIR), ("TIMING_PATH", ROOT / TIMING)):
            baseline_src = once(baseline_src, token, path.as_posix())
        base = AREA / "pilot-baseline.exe"
        *_, report["builds"]["baseline"] = run([*flags, emit("baseline.rs", once(baseline_src, "run::<FACTOR>", "run::<4>")), "-o", base])
        raw, _, report["native"]["baseline"] = run([base, 128])
        target = np.frombuffer(raw, "<f8").reshape(LENGTH, 4)
        wave = {}
        for name, size in (("zero", 128), ("driven", 128), ("driven", 64)):
            data, stderr, record = run([candidate, name, size])
            tag, actual, maximum, allocs, over = stderr.decode().strip().split(",")
            assert tag == "PILOT_PORTS" and int(actual) == size and int(allocs) == 0
            wave[name, size] = np.frombuffer(data, "<f8").reshape(LENGTH, 6)
            assert np.isfinite(wave[name, size]).all()
            report["native"][f"{name}_{size}"] = dict(run=record, max_ns=int(maximum), over_margin=int(over),
                                                      allocations=int(allocs))
        zero = wave["zero", 128]
        pilot_error = float(np.max(abs(target - zero[:, :4])))
        assert pilot_error <= 1e-8
        assert wave["driven", 128].tobytes() == wave["driven", 64].tobytes()
        report["pilot_zero_drive_max_error"] = pilot_error
        report["split_bit_exact"] = True
        report["native"]["host_expected_j7_f32_sha256"] = digest(wave["driven", 128][:, 0].astype("<f4").tobytes())
        report["passed"] = all(item["comparison"]["passed"] and item["refinement"]["passed"]
                               for item in report["scenes"].values())
        sources.unchanged()
    except Exception:
        report["failure"] = traceback.format_exc()
        if last is not None and last[2].returncode != 0:
            command, payload, prior = last
            replay = subprocess.run(command, input=payload, cwd=ROOT, env=env, capture_output=True, timeout=120)
            report["unchanged_replay"] = dict(exit_code=replay.returncode, stdout_sha256=digest(replay.stdout),
                                              stderr=packed(replay.stderr), same_exit=replay.returncode == prior.returncode)
        raise
    finally:
        write(output, report)
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
    print("PILOT_RETURNS", report["passed"], report["native"], flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
