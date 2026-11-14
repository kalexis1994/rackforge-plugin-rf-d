"""Generate the calibrated panel-to-tail-current table from the DC circuit."""
import json
import math

import numpy as np

from check_rf_d_playable_filter import RATE, linear_threshold
from rf_d_playable_build import ROOT, emit, sha
from cutoff_j7_vectors import initial_cutoff_ladder, setup

AMP_PER_STEP = 4 * 0.025693 * 68e-9 * RATE
OLD_TAIL_MID_A = 6.82489851e-6
OLD_TAIL_MAX_A = 144.421881e-6
CALIBRATION_MARK = 0.4
CALIBRATION_HZ = 440.


def calibrated_cutoff_table(report):
    # The service procedure uses full Emphasis. Recover the required step from
    # two measured steady oscillations, including the nonlinear frequency shift.
    source = ROOT / "evidence/rf_d_oboe_clarity01.json"
    measured = {row["cutoff"]: row["peak_hz"]
                for row in json.loads(source.read_bytes())["filter_range"]["comparison"]}
    proportion = math.log(CALIBRATION_HZ / measured[65]) / math.log(measured[66.5] / measured[65])
    old_control = (65. + proportion * 1.5) / 100.
    step = OLD_TAIL_MID_A * (OLD_TAIL_MAX_A / OLD_TAIL_MID_A)**(2 * old_control - 1) / AMP_PER_STEP
    target_a = AMP_PER_STEP * step / (1. - step)
    ladder, _, _, _, controls, _, _ = setup()

    def solve(seed, position, trim, control_seed=None):
        panel = dict(controls["panel"], cutoff_fraction_from_neg10=position)
        return initial_cutoff_ladder(seed, dict(controls, panel=panel, range_fraction=trim),
                                    control_seed=control_seed)

    low, high = 0.1, 0.5
    assert solve(ladder, CALIBRATION_MARK, low)[0]["tail_current_a"] < target_a
    assert solve(ladder, CALIBRATION_MARK, high)[0]["tail_current_a"] > target_a
    for _ in range(24):
        middle = (low + high) / 2.
        if solve(ladder, CALIBRATION_MARK, middle)[0]["tail_current_a"] < target_a:
            low = middle
        else:
            high = middle
    trim = (low + high) / 2.
    points = []
    residuals = []
    control_seed = None
    for position in np.linspace(0., 1., 81):
        ladder, control_seed, error = solve(ladder, float(position), trim, control_seed)
        points.append(ladder["tail_current_a"])
        residuals.append(error)
    knots = np.asarray(points[::2])
    reserves = np.asarray(points[1::2])
    relative_error = float(np.max(abs((knots[:-1] + knots[1:]) / (2. * reserves) - 1.)))
    assert np.all(np.diff(points) > 0.) and relative_error < 0.005
    assert max(residuals) < 1e-11 and abs(knots[16] / target_a - 1.) < 1e-5
    assert knots[-1] / (knots[-1] + AMP_PER_STEP) < 2**-0.75
    values = "".join(f"    {amp:.16e},\n" for amp in knots)
    path = emit("voice-cutoff.rs", f"pub const TAIL_A: [f64; {len(knots)}] = [\n{values}];\n")
    report["cutoff_calibration"] = dict(
        source_sha256=sha(source), service_hz=CALIBRATION_HZ, service_cutoff=CALIBRATION_MARK,
        range_trim_fraction=trim, calibrated_tail_a=target_a, linear_threshold_hz=linear_threshold(step)[1],
        knots_tail_a=knots.tolist(), max_midpoint_relative_error=relative_error,
        max_kcl_residual_a=max(residuals), sha256=sha(path),
    )
    return path
