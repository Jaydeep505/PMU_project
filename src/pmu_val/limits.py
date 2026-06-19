"""
Limit checking. Turns a raw measurement into a pass/fail record against a SpecLimit.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    parameter: str
    value: float
    units: str
    lower: float | None
    upper: float | None
    passed: bool
    # context for the campaign
    rail: str = ""
    unit_id: str = ""
    vin: float | None = None
    iout: float | None = None
    temp_c: float | None = None

    def as_row(self) -> dict:
        return asdict(self)


def check(parameter: str, value: float, units: str,
          lower: float | None, upper: float | None, **ctx) -> TestResult:
    ok = True
    if lower is not None and value < lower:
        ok = False
    if upper is not None and value > upper:
        ok = False
    return TestResult(parameter, value, units, lower, upper, ok, **ctx)
