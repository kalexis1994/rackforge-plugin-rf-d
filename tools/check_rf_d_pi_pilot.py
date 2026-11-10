"""Build the 96 kHz RF-D audition profile and contrast it before deployment."""
import argparse
import json
import math
import os
import shutil
import subprocess
import traceback
from zipfile import ZipFile

import numpy as np

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_rf_d_playable_pilot import (
    AREA, COMPILER, GUEST, HOST, N, NODE, PACKAGE, ROOT, SDK_PATH, SOURCES, WASM_OPT,
    digest, emit, sha, write,
)
from check_rf_d_pilot_returns import LIB, ORACLE, PROBE, compare, drives, generate
from prepare_long_note_aa import taps
from recovery_port_input_model import cases

RATE = 96_000
BASELINE = ROOT / "artifacts/rf-d-pilot-0.3.0.rfplugin"
BASELINE_RECEIPT = ROOT / "evidence/rf_d_playable_pilot12.json"
ARTIFACT = ROOT / "artifacts/rf-d-pilot-0.3.1.rfplugin"
PROFILE = ("--cfg", "pilot_returns", "--cfg", "pilot_block_roots", "--cfg", "pilot_pi")


def antialias():
    h = taps(RATE)
    middle = len(h) // 2
    index = np.arange(len(h)) - middle
    size = 2**20
    frequency = np.fft.rfftfreq(size, 1 / RATE)
    response = abs(np.fft.rfft(h, size))
    curvature = (2 * np.pi / RATE)**2 * np.sum(index**2 * abs(h))
    allowance = curvature * (RATE / size)**2 / 8 + 2e-12
    edge = lambda f: abs(h @ np.cos(2 * np.pi * f * index / RATE))
    band = np.r_[response[frequency <= 20_000], edge(20_000)]
    stop = np.r_[response[frequency >= 24_000], edge(24_000)]
    low = 20 * math.log10(min(band) - allowance)
    high = 20 * math.log10(max(band) + allowance)
    rejection = 20 * math.log10(max(stop) + allowance)
    assert middle / RATE == .001 and max(abs(h - h[::-1])) <= 1e-15
    assert abs(sum(h) - 1.) <= 1e-12 and max(abs(low), abs(high)) <= .001 and rejection <= -90.
    return dict(taps=len(h), delay_frames=48, passband_db=[low, high], stopband_db=rejection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desktop-blocks", action="store_true", help="build 0.3.2 with callbacks up to 4096 frames")
    wide = parser.parse_args().desktop_blocks
    artifact = ARTIFACT.with_name("rf-d-pilot-0.3.2.rfplugin") if wide else ARTIFACT
    version = "0.3.2" if wide else "0.3.1"
    profile = (*PROFILE, "--cfg", "pilot_host_blocks") if wide else PROFILE
    assert not list(AREA.iterdir())
    sources = Sources((*SOURCES, "tools/check_rf_d_pi_pilot.py", "tools/prepare_long_note_aa.py"))
    sequence = 1
    prefix = "rf_d_host_blocks" if wide else "rf_d_pi_pilot"
    while (out := ROOT / f"evidence/{prefix}{sequence:02}.json").exists():
        sequence += 1
    report = dict(passed=False, internal_rate_hz=RATE, package_version=version,
                  **sources.fields(), builds={}, electrical={})
    env = dict(os.environ, PATH="C:/msys64/mingw64/bin;C:/msys64/ucrt64/bin;" + os.environ["PATH"],
               RACKFORGE_OPTIMIZE_PLUGINS="0")
    last = None

    def execute(label, args, payload=None):
        nonlocal last
        command = list(map(str, args))
        run = subprocess.run(command, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=120)
        last = command, payload, run
        report["builds"][label] = dict(command=command, exit_code=run.returncode,
                                       stdout_sha256=digest(run.stdout), stderr=packed(run.stderr))
        assert run.returncode == 0, run.stderr.decode(errors="replace")
        return run.stdout

    try:
        report["fir"] = antialias()
        report["baseline_receipt_sha256"] = sha(BASELINE_RECEIPT)
        reference = json.loads(BASELINE_RECEIPT.read_bytes())
        assert sha(BASELINE) == reference["archive_sha256"]
        with ZipFile(BASELINE) as archive:
            old = AREA / "old.wasm"
            old.write_bytes(archive.read("component.wasm"))
        code, report["maps"] = generate(rate=RATE)
        probe = emit("pi-electrical.rs", code + f'#[path = "{(ROOT / PROBE).as_posix()}"] mod probe;\n'
                     "fn main() -> Result<(), Box<dyn std::error::Error>> { probe::main() }\n")
        candidate, oracle = AREA / "candidate.exe", AREA / "oracle.exe"
        native_flags = [COMPILER, "--edition=2021", "-C", "opt-level=3", "-C", "target-feature=+fma",
                        "-A", "dead_code", "-C", "link-arg=-Wl,--stack,33554432"]
        execute("candidate", [*native_flags, *PROFILE, probe, "-o", candidate])
        execute("oracle", [*native_flags, ROOT / ORACLE, "--extern", f"rf_d_circuit={LIB}", "-o", oracle])
        dc = np.asarray(cases()[1]["DC"], dtype="<f8")

        def readout(label, command, payload):
            raw = execute(label, command, payload.astype("<f8").tobytes())
            return np.frombuffer(raw, "<f8").reshape(-1, 6)

        for scene in ("volume", "filter", "both"):
            count = 256
            reduced = readout(f"{scene}_96", [candidate, "electrical"],
                              drives(np.arange(1, count + 1) / RATE, scene))
            fine = {}
            for factor in (4, 8):
                tick = np.arange(count * factor)
                rate = RATE * factor
                ports = np.column_stack((drives((tick + 1 / 3) / rate, scene), drives((tick + 1) / rate, scene)))
                fine[factor] = readout(f"{scene}_{rate}", [oracle, rate], np.r_[dc, ports.ravel()])[factor - 1::factor]
            entry = dict(comparison=compare(reduced, fine[8]), refinement=compare(fine[4], fine[8]))
            report["electrical"][scene] = entry
            assert all(check["passed"] for check in entry.values()), entry

        guest = emit("pilot-return-guest.rs", code + (ROOT / GUEST).read_text(encoding="utf8"))
        sdk = AREA / "librackforge_plugin_sdk.rlib"
        flags = [COMPILER, "--target", "wasm32-unknown-unknown", "-C", "target-feature=+simd128",
                 "-C", "opt-level=3", "-A", "dead_code"]
        report["sdk_sha256"] = sha(HOST / SDK_PATH)
        execute("sdk", [*flags, "--edition=2024", "--crate-type", "rlib", "--crate-name",
                        "rackforge_plugin_sdk", HOST / SDK_PATH, "-o", sdk])
        guest_flags = [*flags, "--edition=2021", "--crate-type", "cdylib", "-C", "panic=abort",
                       "-C", "lto=fat", *profile, guest, "--extern", f"rackforge_plugin_sdk={sdk}"]
        scalar, simd, optimized = (AREA / name for name in ("pi-scalar.wasm", "pi-simd.wasm", "pi.wasm"))
        execute("scalar", [*guest_flags, "-o", scalar])
        execute("simd", [*guest_flags, "--cfg", "pilot_returns_simd", "-o", simd])
        execute("optimize", [WASM_OPT, simd, "-O4", "-o", optimized])
        score = json.dumps(reference["midi_score"])
        old_audio = execute("desktop_score", ["node", ROOT / NODE, old, score, N])
        scalar_audio = execute("scalar_score", ["node", ROOT / NODE, scalar, score, N])
        pi_audio = execute("simd_score", ["node", ROOT / NODE, optimized, score, N, "--panel-state"])
        assert digest(old_audio) == reference["direct_wasm"]["driven_j7_sha256"]
        report["scalar_matches_simd"] = scalar_audio == pi_audio
        assert report["scalar_matches_simd"]
        expected = np.frombuffer(old_audio, "<f4").astype("f8")
        delta = np.frombuffer(pi_audio, "<f4").astype("f8") - expected
        rms = float(np.linalg.norm(delta) / np.linalg.norm(expected))
        peak = float(abs(delta).max() / abs(expected).max())
        report["score_difference"] = dict(rms_relative=rms, peak_relative=peak)
        assert rms <= .003 and peak <= .01
        package = AREA / "pi-package"
        shutil.copytree(PACKAGE, package)
        for relative in ("rackforge-plugin.toml", "metadata/runtime.json", "web/play.html"):
            path = package / relative
            text = path.read_text(encoding="utf8")
            assert text.count("0.3.0") == 1
            path.write_text(text.replace("0.3.0", version), encoding="utf8", newline="\n")
        archive = AREA / artifact.name
        execute("package", [HOST / "target/release/rackforge-store.exe", "pack-wasm", package, optimized, archive])
        report["archive_sha256"] = sha(archive)
        report["component_sha256"] = sha(optimized)
        if wide:
            release = json.loads((ROOT / "evidence/rf_d_pi_pilot01.json").read_bytes())
            assert sha(ARTIFACT) == release["archive_sha256"]
            assert digest(pi_audio) == release["builds"]["simd_score"]["stdout_sha256"]
            report["old_package_sha256"] = release["archive_sha256"]
            report["partitions"] = {}
            for size in (127, 256, 480, 512, 1024, 4096):
                raw = execute(f"block_{size}", ["node", ROOT / NODE, optimized, score, N,
                                                "--panel-state", size, 4096])
                assert raw == pi_audio, size
                report["partitions"][size] = dict(prepare_frames=4096, output_sha256=digest(raw))
            store = HOST / "target/release/rackforge-store.exe"
            core = HOST / "target/release/rackforge-core.exe"
            old_store, new_store, data_root = (AREA / name for name in ("old-store", "new-store", "stress-state"))
            execute("install_legacy", [store, "install-local", ARTIFACT, old_store])
            execute("install_candidate", [store, "install-local", archive, new_store])
            old_package, = old_store.rglob("rackforge-plugin.toml")
            new_package, = new_store.rglob("rackforge-plugin.toml")

            def stress(manifest, size):
                return [core, "stress", manifest.parent, "--preset", "default", "--data-root", data_root,
                        "--voices", "1", "--blocks", "100", "--frames", size]

            report["legacy_rejections"] = {}
            report["host_stress"] = {}
            for size in (480, 4096):
                command = list(map(str, stress(old_package, size)))
                first, second = (subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=120)
                                 for _ in range(2))
                assert first.returncode != 0 and first.returncode == second.returncode
                assert first.stderr == second.stderr
                assert f"capacity 256 samples is smaller than requested {2 * size}".encode() in first.stderr
                report["legacy_rejections"][size] = dict(command=command, exit_code=first.returncode,
                                                         error=first.stderr.decode().strip(), repeat_identical=True)
            for size in (128, 256, 480, 4096):
                result = execute(f"host_{size}", stress(new_package, size)).decode().strip()
                assert "PLUGIN_STRESS_OK" in result and f"frames={size}" in result
                assert float(result.split("realtime_ratio=")[1]) < 1., result
                report["host_stress"][size] = result
        sources.unchanged()
        archive.replace(artifact)
        report["passed"] = True
        print("RF_D_PI", report["score_difference"], report["archive_sha256"], flush=True)
    except Exception:
        report["failure"] = traceback.format_exc()
        if last is not None and last[2].returncode:
            command, payload, prior = last
            replay = subprocess.run(command, cwd=ROOT, env=env, input=payload, capture_output=True, timeout=120)
            report["unchanged_replay"] = dict(same_exit=replay.returncode == prior.returncode,
                                               stdout_sha256=digest(replay.stdout), stderr=packed(replay.stderr))
        raise
    finally:
        for path in AREA.iterdir():
            assert path.resolve().parent == AREA.resolve()
            if path.is_dir():
                assert path.name in ("pi-package", "old-store", "new-store", "stress-state")
                shutil.rmtree(path)
            else:
                path.unlink()
        write(out, report)


if __name__ == "__main__":
    main()
