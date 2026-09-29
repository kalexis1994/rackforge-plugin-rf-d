"""Optional NumPy dense solve for offline 62-node headphone experiments."""

from __future__ import annotations

from filter_ladder_ebers_moll_dc_reference import _solve_linear


def solve_headphone_linear(matrix: list[list[float]], rhs: list[float], *,
                           method: str) -> list[float]:
    if method == "python":
        return _solve_linear(matrix, rhs)
    if method != "numpy":
        raise ValueError("linear solver must be python or numpy")
    try:
        import numpy as np
    except ImportError as exc:
        raise ValueError("numpy linear solver requires NumPy") from exc
    a = np.asarray(matrix, dtype=np.float64)
    b = np.asarray(rhs, dtype=np.float64)
    if (a.shape != (len(rhs), len(rhs)) or not np.isfinite(a).all()
            or not np.isfinite(b).all()):
        raise ValueError("finite square headphone matrix required")
    try:
        solution = np.linalg.solve(a, b)
    except np.linalg.LinAlgError as exc:
        raise ValueError("singular headphone nodal Jacobian") from exc
    if not np.isfinite(solution).all():
        raise ValueError("nonfinite headphone linear solution")
    # Relative backward error checks the equation rather than conditioning;
    # ill-conditioned cases still need an independent scenario audit.
    defect = np.max(np.abs(a @ solution-b))
    scale = np.max(np.abs(a))*np.max(np.abs(solution))+np.max(np.abs(b))
    if defect > 1e-10*scale:
        raise ValueError("headphone linear solution has excessive residual")
    return [float(value) for value in solution]
