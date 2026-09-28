"""SI thermal voltage used by conditional ideal bipolar references.

Exact SI definitions: NIST 2022 CODATA k and elementary charge. Junction
temperature is always an explicit model boundary, never ambient by default.
"""

from __future__ import annotations

import math


K_BOLTZMANN_J_PER_K = 1.380649e-23
ELEMENTARY_CHARGE_C = 1.602176634e-19


def thermal_voltage_v(temperature_k: float) -> float:
    if not math.isfinite(temperature_k) or temperature_k <= 0:
        raise ValueError("junction temperature must be finite and above 0 K")
    return K_BOLTZMANN_J_PER_K * temperature_k / ELEMENTARY_CHARGE_C
