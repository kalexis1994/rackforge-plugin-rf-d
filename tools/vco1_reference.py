"""Event reference for the *internal timing capacitor* of old Model D VCO 1.

The source is SVC-204D, PDF pp. 14-15 and Fig. 9-3 (PDF p. 61).
This models a prescribed constant current, an ideal reset and the documented
nominal voltage endpoints. It is not a CA3046 transistor model or audio output.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path


CAPACITANCE_F = 0.01e-6  # Fig. 9-3 + Table 7-5: .01 uF nominal; replacement +/-2%
RESET_V = 0.0  # capacitor after Q10 reset, SVC-204D section 2.16
TRIGGER_V = -4.0  # capacitor at Schmitt trigger, same section
Q3_START_V = 4.0  # nominal collector after reset, same section
Q3_END_V = -4.0  # nominal collector at trigger, same section
RAMP_SPAN_V = RESET_V - TRIGGER_V
MAX_CYCLES_PER_STEP = 2**20


def _nonnegative_finite(name: str, value: float) -> float:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and >= 0")
    return value


@dataclass(frozen=True)
class TimingSnapshot:
    capacitor_v: float
    q3_nominal_v: float
    resets: int


class IdealTimingCapacitor:
    """Integrate a constant discharge current with analytic threshold events.

    `phase` is only a numerical coordinate for V_C1, not an audio oscillator
    phase inferred from a physical unit. Input current is supplied by a future
    exponential converter model; the current implementation does not derive it.
    """

    def __init__(self, capacitance_f: float = CAPACITANCE_F) -> None:
        if not math.isfinite(capacitance_f) or capacitance_f <= 0.0:
            raise ValueError("capacitance_f must be finite and > 0")
        self.capacitance_f = capacitance_f
        self.phase = 0.0
        self.total_resets = 0

    def frequency_hz(self, current_a: float) -> float:
        _nonnegative_finite("current_a", current_a)
        frequency = current_a / (self.capacitance_f * RAMP_SPAN_V)
        if not math.isfinite(frequency):
            raise ValueError("derived frequency exceeds floating-point range")
        return frequency

    def snapshot(self, resets: int = 0) -> TimingSnapshot:
        cap_v = RESET_V - self.phase * RAMP_SPAN_V
        # Affine interpolation of two manufacturer-described Q3 endpoints.
        # Its transistor-level gain and load response remain unverified.
        q3_v = Q3_START_V + self.phase * (Q3_END_V - Q3_START_V)
        return TimingSnapshot(cap_v, q3_v, resets)

    def advance(self, seconds: float, current_a: float) -> TimingSnapshot:
        _nonnegative_finite("seconds", seconds)
        cycles = self.frequency_hz(current_a) * seconds
        if not math.isfinite(cycles) or cycles > MAX_CYCLES_PER_STEP:
            raise ValueError("step too large for reliable fractional-cycle precision")
        resets, self.phase = divmod(self.phase + cycles, 1.0)
        self.total_resets += int(resets)
        return self.snapshot(int(resets))


def run_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-ua", type=float, required=True,
                        help="imposed positive discharge current in microamperes")
    parser.add_argument("--duration", type=float, default=0.02, help="seconds")
    parser.add_argument("--sample-rate", type=int, default=192_000,
                        help="CSV observation rate in samples/s; does not set event accuracy")
    parser.add_argument("--csv", type=Path, help="write internal-node trace to this file")
    args = parser.parse_args()

    try:
        current_a = _nonnegative_finite("current_ua", args.current_ua) * 1e-6
        _nonnegative_finite("duration", args.duration)
    except ValueError as error:
        parser.error(str(error))
    if args.sample_rate <= 0:
        parser.error("sample-rate must be positive")
    steps = round(args.duration * args.sample_rate)
    if steps > 10_000_000:
        parser.error("observation would exceed 10 million samples")

    model = IdealTimingCapacitor()
    if args.csv is not None:
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("time_s", "c1_v", "q3_nominal_v", "resets_in_previous_step"))
            initial = model.snapshot()
            writer.writerow((0.0, initial.capacitor_v, initial.q3_nominal_v, 0))
            for step in range(1, steps + 1):
                point = model.advance(1.0 / args.sample_rate, current_a)
                writer.writerow((step / args.sample_rate, point.capacitor_v,
                                 point.q3_nominal_v, point.resets))
    else:
        model.advance(steps / args.sample_rate, current_a)

    summary = {
        "model": "ideal_internal_timing_capacitor_only",
        "capacitance_f_nominal": model.capacitance_f,
        "current_a_imposed": current_a,
        "analytic_frequency_hz": model.frequency_hz(current_a),
        "observed_duration_s": steps / args.sample_rate,
        "resets_in_window": model.total_resets,
        "final_c1_v": model.snapshot().capacitor_v,
        "physical_fidelity": "unverified",
    }
    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    run_cli()
