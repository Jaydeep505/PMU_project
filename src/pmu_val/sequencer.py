"""
Test sequencer / campaign runner.

Walks the PVT matrix (units x Vin x temperature x rail), invokes the
measurement routines, checks each result against the DUT spec limits, and
appends every result to a CSV. This is the ATE-style 'execute a test plan'
layer: ordered tests, limits, pass/fail, logged results.

The sequencer is deliberately backend-agnostic -- it only sees abstract
instruments and a test plan, so the same campaign runs on the manual bench
today and a real SCPI bench later.
"""

from __future__ import annotations

import csv
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .limits import check, TestResult


CSV_FIELDS = ["timestamp", "parameter", "value", "units", "lower", "upper",
              "passed", "rail", "unit_id", "vin", "iout", "temp_c"]


class Campaign:
    def __init__(self, dut, out_csv: str | Path):
        self.dut = dut
        self.out_csv = Path(out_csv)
        self.results: list[TestResult] = []
        self._ensure_csv()

    def _ensure_csv(self):
        self.out_csv.parent.mkdir(parents=True, exist_ok=True)
        if not self.out_csv.exists():
            with self.out_csv.open("w", newline="") as f:
                csv.DictWriter(f, CSV_FIELDS).writeheader()

    def record(self, result: TestResult):
        self.results.append(result)
        row = {"timestamp": datetime.now().isoformat(timespec="seconds")}
        row.update({k: v for k, v in result.as_row().items() if k in CSV_FIELDS})
        with self.out_csv.open("a", newline="") as f:
            csv.DictWriter(f, CSV_FIELDS).writerow(row)
        flag = "PASS" if result.passed else "FAIL"
        print(f"    [{flag}] {result.parameter} = "
              f"{result.value:.4g} {result.units}")

    def check_and_record(self, parameter: str, value: float, rail: str, **ctx):
        """Look up the limit for `parameter` on `rail`, check, record."""
        rail_obj = self.dut.rails[rail]
        lim = rail_obj.limits.get(parameter)
        lower = lim.lower if lim else None
        upper = lim.upper if lim else None
        units = lim.units if lim else ""
        res = check(parameter, value, units, lower, upper, rail=rail, **ctx)
        self.record(res)
        return res

    @property
    def rows(self) -> list[dict]:
        return [r.as_row() for r in self.results]


def load_rows(csv_path: str | Path) -> list[dict]:
    """Re-load a campaign CSV into typed rows (for re-analysis/reporting)."""
    rows = []
    with Path(csv_path).open() as f:
        for r in csv.DictReader(f):
            for k in ("value", "lower", "upper", "vin", "iout", "temp_c"):
                r[k] = float(r[k]) if r[k] not in ("", "None") else None
            r["passed"] = r["passed"] in ("True", "true", "1")
            rows.append(r)
    return rows
