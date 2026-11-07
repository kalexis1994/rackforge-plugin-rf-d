"""Compare matching O3 render ordinals with and without the NVIDIA ASIO stream."""

import subprocess

import numpy as np

from check_hybrid_voice import packed, unpack
from check_recovery_cost import digest, read
from check_recovery_engine128_schedule import analyze_markers, placements
from check_recovery_host import COLUMNS
from prepare_dual_chain import ROOT, sha

HISTORY = ("evidence/recovery_engine128_smt09.json", "evidence/recovery_engine128_smt10.json")
BLOCKS = 4800
CPU = 8
MARGIN_NS = 128e9 / 48000 / 2


def render_rows(item, asio):
    raw = unpack(item["rows"])
    assert digest(raw) == item["sha256"] and item["blocks"] == BLOCKS
    rows = np.frombuffer(raw, "<u8").reshape(BLOCKS, len(COLUMNS) + (8 if asio else 6))
    return rows[:, [len(COLUMNS) + 2, len(COLUMNS) + 3]]


def compare(items, offline):
    sources = [render_rows(item, asio=True) for item in items]
    other = render_rows(offline, asio=False)
    comparisons = []
    for source in sources:
        wall, cycles = source.T
        over = wall > MARGIN_NS
        peak = int(wall.argmax())
        comparisons.append(dict(
            peak_block=peak, physical_render_ns=int(wall[peak]), physical_render_cycles=int(cycles[peak]),
            offline_same_block_ns=int(other[peak, 0]), offline_same_block_cycles=int(other[peak, 1]),
            physical_render_over_margin=int(over.sum()),
            same_block_over_margin_both=int((over & (other[:, 0] > MARGIN_NS)).sum()),
            render_ns_pearson=float(np.corrcoef(wall, other[:, 0])[0, 1]),
        ))
    return comparisons


def compare_offline(report, exe, env, dsp_package, cache, rows_path, analyze_asio):
    assert CPU in placements(report["topology"])
    history = [read(name) for name in HISTORY]
    for prior in history:
        assert prior["artifact_sha256"]["package-dsp/component.wasm"] == report["artifact_sha256"]["package-dsp/component.wasm"]
        assert prior["fixtures"]["sha256"] == report["fixtures"]["sha256"]
    report["ordinal_inputs"] = {name: sha(ROOT / name) for name in HISTORY}

    bank_env = dict(env, RF_D_ENGINE_ROUTE="rack", RF_D_ENGINE_PACKAGE=str(dsp_package),
                    RF_D_ENGINE_CACHE=str(cache), RF_D_SCHED_CPU=str(CPU))
    bank_env.pop("RF_D_SCHED_LOAD", None)
    rows_path.unlink(missing_ok=True)
    result = subprocess.run([str(exe), "schedule-offline", str(BLOCKS)], cwd=ROOT, env=bank_env,
                            capture_output=True, timeout=45)
    raw = rows_path.read_bytes() if rows_path.exists() else b""
    stream = result.stderr.decode(errors="replace")
    offline = dict(mode="quiet", cpu=CPU, blocks=BLOCKS, exit_code=result.returncode,
                   rows=packed(raw), sha256=digest(raw), stream=stream, log=result.stdout.decode(errors="replace"))
    report["offline_comparison"] = offline
    if result.returncode != 0:
        print("NVIDIA128_OFFLINE_FAILED", stream, flush=True)
        return
    metrics = analyze_markers(raw, stream, BLOCKS, "quiet", CPU, None, analyze_asio)
    offline["metrics"] = metrics
    assert metrics["pinned_verified"]
    banks = [item for campaign in (*history, report) for item in campaign["confirmations"][0]["runs"]
             if item.get("metrics", {}).get("physical_endpoint_verified")]
    offline["ordinal_comparison"] = compare(banks, offline)
    print("NVIDIA128_OFFLINE", metrics["render_window_ns"], offline["ordinal_comparison"], flush=True)
