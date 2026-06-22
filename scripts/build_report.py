"""
Build the consolidated validation report from all real campaign CSV slices.

Each rail/unit was collected into its own CSV slice (shakedown.csv, u1_rails.csv,
multi.csv, ...) so a mis-entry only ever costs one slice -- never the whole run.
This script reassembles them into one population and renders the report:

  * globs data/*.csv, keeping only real campaign-schema files
    (skips the synthetic demo and the resistor-calibration file)
  * collapses duplicates to ONE row per (unit, rail, parameter): the most
    recent measurement wins, so Day-1 re-runs don't double-count in Cpk/yield
  * writes the merged population to data/campaign_merged.csv
  * renders reports/validation_report.html via the existing report.py

  python scripts/build_report.py
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pmu_val.dut import DUT
from pmu_val.sequencer import load_rows, CSV_FIELDS
from pmu_val import analysis
from pmu_val import report as R

# Real measurement slices only. Exclude synthetic + non-campaign files.
EXCLUDE = {"campaign_demo.csv", "resistors.csv", "campaign_merged.csv"}


def discover_slices(data_dir: Path):
    """Return data/*.csv files that carry the real campaign schema."""
    slices = []
    for p in sorted(data_dir.glob("*.csv")):
        if p.name in EXCLUDE:
            continue
        if p.stat().st_size == 0:
            continue
        header = p.read_text().splitlines()[0].split(",")
        if header[:len(CSV_FIELDS)] != CSV_FIELDS:
            print(f"  skip {p.name} (not a campaign CSV)")
            continue
        slices.append(p)
    return slices


def dedup_latest(rows):
    """One row per (unit, rail, parameter); most recent timestamp wins.

    A re-test supersedes an earlier reading rather than adding a second
    sample -- otherwise a unit measured twice would be counted twice in
    Cpk/yield. ISO timestamps compare correctly as strings.
    """
    best = {}
    for r in rows:
        key = (r.get("unit_id", ""), r.get("rail", ""),
               r.get("parameter", ""), r.get("temp_c", ""))
        cur = best.get(key)
        if cur is None or r["timestamp"] > cur["timestamp"]:
            best[key] = r
    return list(best.values())


def main():
    data_dir = ROOT / "data"
    slices = discover_slices(data_dir)
    print(f"Including {len(slices)} slice(s): {[p.name for p in slices]}")

    all_rows = []
    for p in slices:
        all_rows.extend(load_rows(p))
    print(f"  raw rows: {len(all_rows)}")

    rows = dedup_latest(all_rows)
    dropped = len(all_rows) - len(rows)
    print(f"  after dedup (latest per unit/rail/param): {len(rows)} "
          f"({dropped} duplicate row(s) collapsed)")

    merged = data_dir / "campaign_merged.csv"
    with merged.open("w", newline="") as f:
        w = csv.DictWriter(f, CSV_FIELDS)
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["unit_id"], r["rail"],
                                             r["parameter"])):
            w.writerow({k: r.get(k, "") for k in CSV_FIELDS})
    print(f"  merged population -> {merged}")

    # console summary: per-rail, per-parameter yield/Cpk, flag any fails
    print("\nPer-parameter summary (across units @ 25 C):")
    params = sorted({r["parameter"] for r in rows})
    for rail in sorted({r["rail"] for r in rows}):
        print(f"  Rail {rail}:")
        for p in params:
            sel = [r for r in rows if r["rail"] == rail
                   and r["parameter"] == p]
            if not sel:
                continue
            vals = [r["value"] for r in sel]
            flags = [r["passed"] for r in sel]
            y = analysis.yield_pct(flags)
            lower = next((r["lower"] for r in sel), None)
            upper = next((r["upper"] for r in sel), None)
            c = analysis.cpk(vals, lower, upper)
            ctxt = ("inf" if c == float("inf")
                    else (f"{c:.2f}" if c is not None else "n/a"))
            tag = "" if all(flags) else "   <-- FAIL"
            print(f"    {p:14s} n={len(sel)}  yield={y:5.1f}%  "
                  f"Cpk={ctxt}{tag}")

    dut = DUT.from_yaml(ROOT / "config" / "dut_qc3.yaml")
    note = ("Real DC measurements on physical QC3.0 buck modules (5V charger -> "
            "XL6009 boost source, single DMM, ceramic resistor loads); 3 units "
            "@ 25 C. Cpk/yield use part-to-part spread as the process axis. "
            "Efficiency deferred (a single DMM can't capture Vout + Iin at one "
            "operating point). Ripple/transient/PSRR out of scope -- need a "
            "scope, not faked.")
    out = R.write_report(rows, dut,
                         ROOT / "reports" / "validation_report.html", note)
    R.render_pdf(out, ROOT / "reports" / "validation_report.pdf")
    print(f"\nReport written: {out}")


if __name__ == "__main__":
    main()
