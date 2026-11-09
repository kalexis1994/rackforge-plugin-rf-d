"""Build the fixed-bias reduced RF-D voice and compare rates before listening."""
import json
import os
import re
import subprocess
import traceback
import wave
from pathlib import Path

import numpy as np

from affine_evidence import Sources
from check_recovery_cost import digest
from check_vco_family_voice_bus_latch_lu import CPU, TIMING, emit, pin
from check_vco_family_voice_bus_model import AREA, ORACLE, materialize, read_oracle
from check_vco_phase import COMPILER
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once
from prepare_vco_family_voice_bus import prediction
from recovery_cost_exp_model import build, cases, independent_maps
from validate_vco_family_voice_bus import MODEL, read
from vco_family_voice_bus_receipts import receipt_bytes

OWN = "tools/check_rf_d_reduced_voice.py"
VOICE = "tools/rf_d_reduced_voice.rs"
PROBE = "tools/rf_d_reduced_voice_probe.rs"
DOC = "docs/VOZ_REDUCIDA_PILOTO_PROTOCOLO.md"
PLANT = "tools/recovery_cost_exp_kernel.rs"
DATA = "tools/recovery_cost_exp_data.rs"
MAPS = "tools/recovery_cost_exp_model.py"
FIR = "crates/rf-d-circuit/src/j7_antialias_coefficients.rs"
RECEIPT = "evidence/rf_d_reduced_voice_pilot"
GUEST = "tools/rf_d_reduced_voice_guest.rs"
NODE = "tools/rf_d_reduced_voice_wasm.js"
SDK = Path("C:/Users/kalex/.codex/worktrees/rackforge-rf-d-fuel/rackforge/crates/rackforge-plugin-sdk/src/lib.rs")
AUDIO = "artifacts/rf-d-piloto-voz-reducida-escucha.wav"
VOLTS_PER_FULL_SCALE = 0.000125
N = 48_128


def rate_maps():
    names = dict(dc="[f64;68]", iexp="[f64;12]", f="[[f64;18];18]", u0="[f64;18]", u1="[f64;18]",
                 n0="[[f64;12];18]", n1="[[f64;12];18]", xq="[[f64;18];68]", xu="[f64;68]",
                 xd="[[f64;12];68]", zh="[[f64;18];12]", zu="[f64;12]", p="[[f64;12];12]")
    models = [build(case, h=1 / 192_000) for case in cases()]

    def rust(value):
        return "[" + ",".join(map(rust, value)) + "]" if isinstance(value, list) else f"{value:.17e}"

    source = "".join(f"pub const {key.upper()}:[{ty};3]=" + rust([m[key].tolist() for m in models]) + ";\n"
                     for key, ty in names.items())
    return source, [independent_maps(m) for m in models]


def parse(run, factor, size):
    assert run.returncode == 0, run.stderr.decode(errors="replace")
    fields = run.stderr.decode().strip().split(",")
    assert fields[0] == "PILOT"
    actual, block, count, elapsed, maximum, over, allocs = map(int, fields[1:])
    assert (actual, block, count) == (factor, size, N // size) and allocs == 0
    frames = np.frombuffer(run.stdout, "<f8").reshape(N, 4)
    assert np.isfinite(frames).all() and np.all(frames[:48, 0] == 0.)
    return frames, dict(factor=actual, block=block, count=count, mean_ns=elapsed / count, max_ns=maximum,
                        over_margin=over, allocations=allocs, render_sha256=digest(run.stdout))


def compare(fine, candidate):
    y, b = candidate[:, 0], fine[:, 0]
    error = y - b
    peak = float(max(abs(b)))
    assert peak > 1e-7 and max(abs(y)) > 1e-7
    rms = float(np.linalg.norm(error) / np.linalg.norm(b))
    peak_error = float(max(abs(error)) / peak)
    mean = float(abs(np.mean(error)))
    delta = np.max(abs(candidate[:, 1:] - fine[:, 1:]), axis=0)
    limits = np.array([20e-6, 20e-6, 2e-9]) + .01 * np.ptp(fine[:, 1:], axis=0)
    passed = rms <= .003 and peak_error <= .01 and mean <= 1e-6 and bool(np.all(delta <= limits))
    return dict(passed=passed, j7_rms_relative=rms, j7_peak_relative=peak_error, j7_mean_v=mean,
                port_maximum=delta.tolist(), port_limits=limits.tolist(), j7_peak_v=float(max(abs(y))))


def score():
    section = (ROOT / PROBE).read_text(encoding="utf8").split("const SCENE:", 1)[1].split("fn guards", 1)[0]
    events = []
    for offset, message, note in re.findall(r"offset: (\d+), message: (NoteOn|NoteOff|AllNotesOff)(?:\((\d+)\))?", section):
        events.append([int(offset), {"NoteOn": 0x90, "NoteOff": 0x80, "AllNotesOff": 0xb0}[message],
                       int(note) if note else 123])
    assert len(events) == 8
    return events


def pitch_checks(samples):
    regions = ((61, 6179, 57), (6179, 12298, 45), (12298, 18537, 57),
               (23229, 29383, 52), (29383, 35678, 52), (35678, 42321, 60))
    result = []
    for first, last, note in regions:
        x = samples[first + 800:last - 128]
        amplitude = abs(np.fft.rfft((x - x.mean()) * np.hanning(len(x)), n=65536))
        k = int(amplitude.argmax())
        assert 0 < k < len(amplitude) - 1
        a, b, c = np.log(amplitude[k - 1:k + 2])
        hz = (k + .5 * (a - c) / (a - 2 * b + c)) * 48000. / 65536
        reference = 440. * 2. ** ((note - 69) / 12.)
        assert abs(hz - reference) < 1., (first, note, hz)
        result.append(dict(start=first, end=last, note=note, hz=float(hz)))
    return result


def portable_source(plant, wave_path):
    probe = (ROOT / PROBE).read_text(encoding="utf8")
    modules = probe[:probe.index("mod coefficients;") + len("mod coefficients;")]
    modules = modules.replace("PLANT_PATH", plant.as_posix()).replace("WAVE_PATH", wave_path.as_posix())
    modules = modules.replace("FIR_PATH", (ROOT / FIR).as_posix())
    source = modules + f'\n#[path = "{(ROOT / VOICE).as_posix()}"] mod voice;\n'
    source += (ROOT / GUEST).read_text(encoding="utf8")
    return emit("pilot-guest.rs", source)


def prepare_pilot():
    table, logs, models, _, _, _ = materialize(read_oracle())
    assert digest(table) == read(MODEL)["table_sha256"]
    z = prediction(logs, models, -1.6, 0.)["c"][0].copy()
    z[1:] *= 2.
    cycle = np.fft.ifft(z, n=4096).real * 4096
    scale = float(max(abs(cycle)))
    assert scale > 0.
    wave_path = emit("pilot-wave.rs", "pub const SAW:[f64;4096]=[" +
                     ",".join(f"{v:.17e}" for v in cycle / scale) + "];\n")
    maps, checks = rate_maps()
    candidate = emit("pilot-maps.rs", maps)
    return wave_path, candidate, dict(independent_maps=checks, wave_table_sha256=sha(wave_path),
                                      wave_peak_source_v=scale, candidate_maps_sha256=sha(candidate))


def pilot_plant(data):
    return emit("pilot-plant.rs", once((ROOT / PLANT).read_text(encoding="utf8"),
                '"recovery_cost_exp_data.rs"', f'"{data.as_posix()}"'))


def portable(run, plant, wave_path, native, report):
    guest = portable_source(plant, wave_path)
    sdk = AREA / "librackforge_plugin_sdk.rlib"
    wasm = AREA / "pilot.wasm"
    flags = [COMPILER, "--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128",
             "-C", "opt-level=3", "-A", "dead_code"]
    report["sdk_sha256"] = sha(SDK)
    report["portable_builds"] = []
    for args in (
        [*flags, "--edition=2024", "--crate-type", "rlib", "--crate-name", "rackforge_plugin_sdk", SDK, "-o", sdk],
        [*flags, "--edition=2021", "--crate-type", "cdylib", "-C", "panic=abort", "-C", "lto=fat",
         guest, "--extern", f"rackforge_plugin_sdk={sdk}", "-o", wasm],
    ):
        result = run(args)
        report["portable_builds"].append(dict(command=list(map(str, args)), exit_code=result.returncode,
                                              stderr=result.stderr.decode(errors="replace")))
        assert result.returncode == 0, result.stderr.decode(errors="replace")
    result = run(["node", ROOT / NODE, wasm, json.dumps(score()), N])
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    stereo = np.frombuffer(result.stdout, "<f4").reshape(N, 2)
    assert np.isfinite(stereo).all() and stereo[:, 0].tobytes() == stereo[:, 1].tobytes()
    reference = (native[:, 0] / VOLTS_PER_FULL_SCALE).astype("<f4")
    error = float(np.max(abs(reference.astype("f8") - stereo[:, 0])))
    assert error <= 2e-7 and float(max(abs(stereo[:, 0]))) > .05
    timings = json.loads(result.stderr)
    assert len(timings) == N // 128 and all(t > 0 for t in timings)
    report["portable"] = dict(component_sha256=sha(wasm), output_sha256=digest(result.stdout),
                              latency=48, max_audio_error=error,
                              bit_exact=reference.tobytes() == stereo[:, 0].tobytes(),
                              p50_ns=float(np.median(timings)), max_ns=max(timings),
                              over_margin=sum(3 * t > 4_000_000 for t in timings), timings_ns=timings)


def main():
    assert not list(AREA.iterdir())
    sequence = 1
    while (ROOT / f"{RECEIPT}{sequence:02}.json").exists():
        sequence += 1
    target = ROOT / f"{RECEIPT}{sequence:02}.json"
    sources = Sources([OWN, VOICE, PROBE, DOC, PLANT, DATA, MAPS, FIR, TIMING, GUEST, NODE])
    report = dict(passed=False, **sources.fields(), compiler_sha256=sha(Path(COMPILER)),
                  oracle_sha256=digest(receipt_bytes(ORACLE)),
                  plant_input_sha256=sha(ROOT / "evidence/charge_control_native01.json"),
                  builds={}, runs={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"])
    command = []
    process = None

    def run(args):
        nonlocal command, process
        command = list(map(str, args))
        process = None
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=120)
        return process

    try:
        wave_path, candidate_maps, checks = prepare_pilot()
        report.update(checks)
        report["affinity"] = pin()
        outputs = {}
        for factor, data in ((8, ROOT / DATA), (4, candidate_maps)):
            plant = pilot_plant(data)
            source = (ROOT / PROBE).read_text(encoding="utf8")
            for token, path in (("PLANT_PATH", plant), ("VOICE_PATH", ROOT / VOICE),
                                ("FIR_PATH", ROOT / FIR), ("TIMING_PATH", ROOT / TIMING), ("WAVE_PATH", wave_path)):
                source = once(source, token, path.as_posix())
            source = once(source, "run::<FACTOR>", f"run::<{factor}>")
            probe = emit("pilot-probe.rs", source)
            exe = AREA / f"pilot-{factor}.exe"
            build_run = run([COMPILER, "--edition=2021", "-C", "opt-level=3",
                             "-C", "target-feature=+fma", "-A", "dead_code", probe, "-o", exe])
            report["builds"][str(factor)] = dict(command=command, exit_code=build_run.returncode,
                                                  stderr=build_run.stderr.decode(errors="replace"))
            assert build_run.returncode == 0, build_run.stderr.decode(errors="replace")
            affinity = run([exe, "affinity"])
            assert affinity.returncode == 0 and affinity.stdout.strip() == f"AFFINITY,{1 << CPU},{CPU}".encode()
            outputs[factor], report["runs"][str(factor)] = parse(run([exe, "128"]), factor, 128)
            if factor == 4:
                split, item = parse(run([exe, "64"]), factor, 64)
                assert split.tobytes() == outputs[factor].tobytes()
                report["split"] = item
        report["comparison"] = compare(outputs[8], outputs[4])
        report["pitch_checks"] = pitch_checks(outputs[4][:, 0])
        portable(run, plant, wave_path, outputs[4], report)
        report["native_margin_observed"] = report["runs"]["4"]["over_margin"] == 0
        print("PILOT_RESULT", report["comparison"], report["runs"], flush=True)
        audio = ROOT / AUDIO
        audio.parent.mkdir(exist_ok=True)
        volts_per_full_scale = VOLTS_PER_FULL_SCALE
        mono = outputs[4][:, 0] / volts_per_full_scale
        assert max(abs(mono)) < 1., float(max(abs(mono)))
        with wave.open(str(audio), "wb") as wav:
            wav.setparams((1, 2, 48_000, N, "NONE", "not compressed"))
            wav.writeframes(np.rint(mono * 32767).astype("<i2").tobytes())
        with wave.open(str(audio), "rb") as wav:
            assert wav.getnframes() == N and wav.getframerate() == 48_000
        report["listening"] = dict(path=AUDIO, sha256=sha(audio), frames=N, volts_per_full_scale=volts_per_full_scale)
        report["passed"] = True
    except Exception:
        report["failure"] = traceback.format_exc()
        if process is not None:
            report["failed"] = dict(command=command, exit_code=process.returncode, stdout_sha256=digest(process.stdout),
                                    stderr=process.stderr.decode(errors="replace"))
            try:
                again = run(command)
                report["unchanged_replay"] = dict(exit_code=again.returncode, stdout_sha256=digest(again.stdout),
                                                   stderr=again.stderr.decode(errors="replace"))
            except subprocess.TimeoutExpired:
                report["unchanged_replay"] = dict(timeout=True)
    finally:
        for path in AREA.iterdir():
            assert path.is_file() and path.resolve().parent == AREA.resolve()
            path.unlink()
        sources.unchanged()
        report["temporary_area_empty"] = not list(AREA.iterdir())
        write(target, report)
    print("PILOT", report["passed"], report.get("failure"), flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
