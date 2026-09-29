"""Explicit offline subdivision after a bounded 62-node Newton failure."""

from __future__ import annotations

import json
from pathlib import Path

from headphone_coupled_transient_reference import (
    HeadphoneStepConvergenceError, initial_coupled_headphone_state,
    nonlinear_coupled_headphone_step)
from headphone_transient_stress_reference import _scenario, reference_dc


EVIDENCE = (Path(__file__).resolve().parents[1] / "evidence"
            / "headphone_substep_retry.json")


def retry_headphone_step(*, previous_state: dict, bus_v: float, dt_s: float,
                         max_subdivision_depth: int = 1,
                         **step_parameters) -> dict:
    """Retry by binary time subdivision with BUS held at its new value.

    The first substep sees the complete BUS jump. Subsequent substeps see
    zero BUS increment. Switch, load and panel controls remain fixed over
    the original interval. Only convergence failures trigger subdivision.
    """
    if (type(max_subdivision_depth) is not int
            or not 0 <= max_subdivision_depth <= 4):
        raise ValueError("subdivision depth must be an integer from 0 to 4")

    def attempt(prior: dict, interval_s: float,
                depth: int) -> tuple[dict, int, int, int]:
        try:
            result = nonlinear_coupled_headphone_step(
                previous_state=prior, bus_v=bus_v, dt_s=interval_s,
                **step_parameters)
            return result, 1, 1, depth
        except HeadphoneStepConvergenceError:
            if depth == max_subdivision_depth:
                raise
            left, left_attempts, left_leaves, left_depth = attempt(
                prior, interval_s/2, depth+1)
            right, right_attempts, right_leaves, right_depth = attempt(
                left, interval_s/2, depth+1)
            return (right, 1+left_attempts+right_attempts,
                    left_leaves+right_leaves, max(left_depth, right_depth))

    result, attempts, accepted, depth = attempt(previous_state, dt_s, 0)
    return {**result, "solver_attempt_count": attempts,
            "accepted_substeps": accepted,
            "subdivision_depth_used": depth,
            "retry_policy": "offline_zoh_bus_at_interval_start"}


def retry_example() -> dict:
    scenario = _scenario()
    base = reference_dc(scenario)
    prior = initial_coupled_headphone_state(**base)
    panel = dict(
        r14_pin7_to_pin6_ohm=scenario["r14_pin7_to_pin6_ohm"],
        r73_bottom_side_to_wiper_ohm=scenario["r73_bottom_side_to_wiper_ohm"],
        r20_wiper_to_ground_ohm=scenario["r20_wiper_to_ground_ohm"],
        r21_wiper_to_ground_ohm=scenario["r21_wiper_to_ground_ohm"],
        hi_load_ohm=scenario["hi_load_ohm"],
        lo_load_ohm=scenario["lo_load_ohm"],
        tip_load_ohm=32, ring_load_ohm=32)
    budget = dict(newton_max_iterations=10,
                  line_search_max_halvings=4)
    try:
        nonlinear_coupled_headphone_step(
            **base, **panel, **budget, previous_state=prior,
            bus_v=-3.0, dt_s=1/480)
    except HeadphoneStepConvergenceError as error:
        failed_reason = error.reason
    else:
        raise ValueError("declared full-step stress unexpectedly converged")
    retried = retry_headphone_step(
        **base, **panel, **budget, previous_state=prior,
        bus_v=-3.0, dt_s=1/480, max_subdivision_depth=1)
    full = nonlinear_coupled_headphone_step(
        **base, **panel, previous_state=prior, bus_v=-3.0, dt_s=1/480)
    return {"bus_v": -3.0, "dt_s": 1/480,
            "tip_ring_ohm": 32, "budget": budget,
            "full_step_failure_reason": failed_reason,
            "retry_attempt_count": retried["solver_attempt_count"],
            "accepted_substeps": retried["accepted_substeps"],
            "subdivision_depth_used": retried["subdivision_depth_used"],
            "retry_j7_v": retried["j7_tip_v"],
            "retry_max_kcl_residual_a": retried["max_charge_kcl_residual_a"],
            "unrestricted_full_step_j7_v": full["j7_tip_v"],
            "unrestricted_full_step_iterations": full["iterations"],
            "j7_difference_due_to_discretization_v": (
                retried["j7_tip_v"]-full["j7_tip_v"]),
            "interpretation": "Synthetic stress and offline ZOH retry only; subdivision changes the numerical solution."}


if __name__ == "__main__":
    print(json.dumps(retry_example(), indent=2))
