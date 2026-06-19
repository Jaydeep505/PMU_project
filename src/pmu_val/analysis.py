"""
Statistical characterization.

This is the 'statistical analysis for silicon characterization' piece of the
job posting. Operates on the collected pass/fail rows (one per measurement,
across units / Vin / temperature) and produces:

  * per-parameter distribution stats (mean, sigma, min, max)
  * process capability Cpk against the spec limits
  * yield (fraction of units/conditions passing)
  * a shmoo map (pass/fail grid over two swept axes, e.g. Vin x temperature)

Part-to-part spread across your multiple identical modules is the honest
proxy for process variation -- that is what makes Cpk and yield meaningful
here rather than invented.
"""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean, pstdev


def distribution(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    mu = mean(values)
    sigma = pstdev(values) if len(values) > 1 else 0.0
    return {"n": len(values), "mean": mu, "sigma": sigma,
            "min": min(values), "max": max(values)}


def cpk(values: list[float], lower: float | None, upper: float | None) -> float | None:
    """Process capability index. Higher is better; 1.33 is a common target."""
    if len(values) < 2:
        return None
    mu = mean(values)
    sigma = pstdev(values)
    if sigma == 0:
        return float("inf")
    candidates = []
    if upper is not None:
        candidates.append((upper - mu) / (3 * sigma))
    if lower is not None:
        candidates.append((mu - lower) / (3 * sigma))
    return min(candidates) if candidates else None


def yield_pct(passed_flags: list[bool]) -> float:
    if not passed_flags:
        return 0.0
    return 100.0 * sum(passed_flags) / len(passed_flags)


def summarize_parameter(rows: list[dict], parameter: str) -> dict:
    """Aggregate stats for one parameter across all rows."""
    sel = [r for r in rows if r["parameter"] == parameter]
    vals = [r["value"] for r in sel]
    lower = next((r["lower"] for r in sel), None)
    upper = next((r["upper"] for r in sel), None)
    return {
        "parameter": parameter,
        "dist": distribution(vals),
        "cpk": cpk(vals, lower, upper),
        "yield_pct": yield_pct([r["passed"] for r in sel]),
        "lower": lower, "upper": upper,
        "units": sel[0]["units"] if sel else "",
    }


def shmoo(rows: list[dict], parameter: str,
          x_key: str = "vin", y_key: str = "temp_c") -> dict:
    """Build a pass/fail grid over two axes for one parameter.

    Returns {'x': [...], 'y': [...], 'grid': {(y,x): pass_fraction}}.
    """
    sel = [r for r in rows if r["parameter"] == parameter
           and r[x_key] is not None and r[y_key] is not None]
    xs = sorted({r[x_key] for r in sel})
    ys = sorted({r[y_key] for r in sel})
    buckets: dict[tuple, list[bool]] = defaultdict(list)
    for r in sel:
        buckets[(r[y_key], r[x_key])].append(r["passed"])
    grid = {k: (sum(v) / len(v)) for k, v in buckets.items()}
    return {"x": xs, "y": ys, "x_key": x_key, "y_key": y_key, "grid": grid}
