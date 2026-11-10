"""Compare the physical return readout with imposed receiver loads."""
import numpy as np

import check_rf_d_pilot_contours as c

PROBE = "tools/rf_d_pilot_return_readout_probe.rs"
SOURCES = (PROBE, "tools/rf_d_reduced_engine_lu.rs", "tools/latch_charge_driver.rs")
RETURN_LIMIT_A = 2e-9


def prepare(run, build):
    target = c.AREA / "pilot-return-readout.exe"
    run([*build, "-A", "dead_code", "--cfg", "pilot_closed_cv", c.ROOT / PROBE,
         "--extern", f"rf_d_circuit={c.LIB}", "-o", target])
    return target


def assess(run, target, reference, candidate, skip):
    seed = reference[0, [0, 1, 3, 35, 36, 37]]
    loads = reference[:, [2, 4, 54, 55]]
    expected = np.column_stack((reference[:, [3, 37]],
                                (reference[:, 3] - reference[:, 54]) / 68_000.,
                                (reference[:, 55] - reference[:, 37]) / 680.))

    def measure(ports):
        data = np.r_[seed, np.column_stack((ports, loads)).ravel()].astype("<f8").tobytes()
        raw = run([target], data)
        assert raw == run([target], data)
        rows = np.frombuffer(raw, "<f8").reshape(-1, 4)
        assert rows.shape == expected.shape and np.isfinite(rows).all()
        error = abs(rows[skip:] - expected[skip:]).max(axis=0)
        return dict(passed=bool(error[2:].max() <= RETURN_LIMIT_A),
                    max_source_error_v=error[:2].tolist(), max_current_error_a=error[2:].tolist(),
                    input_sha256=c.digest(data), output_sha256=c.digest(raw))

    control = measure(reference[:, [5, 34]])
    observed = measure(candidate)
    error = abs(candidate[skip:] - reference[skip:, [5, 34]]).max(axis=0)
    return dict(passed=control["passed"] and observed["passed"], compared=len(reference) - skip,
                skipped_unresolved_anchor=bool(skip), current_limit_a=RETURN_LIMIT_A,
                max_c2_sum_error_v=error.tolist(), oracle_ports=control, generated_ports=observed)
