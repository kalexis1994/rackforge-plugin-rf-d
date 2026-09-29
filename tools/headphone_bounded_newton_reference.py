"""Re-run declared headphone stresses under a finite Newton budget."""

from __future__ import annotations

import json
from pathlib import Path

from headphone_transient_bipolar_reference import bipolar_stress
from headphone_transient_stress_reference import stress_grid


EVIDENCE = (Path(__file__).resolve().parents[1] / "evidence"
            / "headphone_bounded_newton_grid.json")


def bounded_grid(*, linear_solver: str = "python") -> dict:
    budget = {"newton_max_iterations": 16,
              "line_search_max_halvings": 16}
    short = stress_grid(**budget, linear_solver=linear_solver)
    bipolar = bipolar_stress(**budget, linear_solver=linear_solver)
    return {"budget": budget, "linear_solver": linear_solver,
            "scenario_count": short["scenario_count"]+bipolar["scenario_count"],
            "step_count": short["step_count"]+bipolar["step_count"],
            "max_newton_iterations": max(
                short["max_newton_iterations"],
                *(row["max_newton_iterations"] for row in bipolar["rows"])),
            "max_halvings_used": max(short["max_halvings_used"],
                                     bipolar["max_halvings_used"]),
            "max_kcl_residual_a": max(
                short["max_kcl_residual_a"],
                *(row["max_kcl_residual_a"] for row in bipolar["rows"])),
            "short": short, "bipolar": bipolar,
            "interpretation": "Finite budget observed on declared synthetic inputs only; not a universal convergence or realtime guarantee."}


if __name__ == "__main__":
    print(json.dumps(bounded_grid(), indent=2))
