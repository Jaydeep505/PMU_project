"""
Run the PVT validation campaign.

  python scripts/run_campaign.py                 # manual bench (prompts you)
  python scripts/run_campaign.py --backend pyvisa  # automated SCPI bench
  python scripts/run_campaign.py --dropout       # also run the slow dropout sweep

For each unit / temperature / rail it runs: no-load Vout, line reg, load reg,
efficiency (and optionally dropout), checks each against the spec limits, logs to
CSV, then generates a validation report in reports/.

The order of operations is intentionally the order you would follow at the bench.
"""

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pmu_val.dut import DUT
from pmu_val.instruments.registry import build_bench
from pmu_val.sequencer import Campaign
from pmu_val import measurements as M
from pmu_val import report as R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="manual", choices=["manual", "pyvisa"])
    ap.add_argument("--dut", default=str(ROOT / "config" / "dut_qc3.yaml"))
    ap.add_argument("--plan", default=str(ROOT / "config" / "test_plan.yaml"))
    ap.add_argument("--csv", default=str(ROOT / "data" / "campaign.csv"))
    ap.add_argument("--dropout", action="store_true",
                    help="also run the (slow) dropout Vin sweep on rails "
                         "that define a dropout_vin limit")
    ap.add_argument("--efficiency", action="store_true",
                    help="also measure efficiency (needs input-current sensing: "
                         "DMM in series on the input). Off by default.")
    args = ap.parse_args()

    dut = DUT.from_yaml(args.dut)
    plan = yaml.safe_load(Path(args.plan).read_text())
    source, meter, load = build_bench(args.backend)
    campaign = Campaign(dut, args.csv)

    with source, meter, load:
        for unit in plan["units"]:
            for temp in plan["temperatures_c"]:
                print(f"\n########## UNIT {unit} @ {temp} C ##########")
                input(f"Set up {unit}, stabilize at ~{temp} C, press Enter...")
                for rail_name in plan["rails"]:
                    rail = dut.rails[rail_name]
                    nom = rail.vout_nom
                    print(f"\n---- Rail {rail_name} ----")

                    vin_pts = [v for v in plan["vin_points"] if v >= nom + 0.5]
                    # Operate load-reg / efficiency / no-load at the HIGH end of
                    # the Vin sweep. This QC module needs ~12 V input to hold the
                    # rail under load (it browns out lower), so use the top point.
                    vin_op = max(vin_pts) if vin_pts else nom + 1.0

                    # no-load output voltage (nothing wired to the output) --
                    # confirms the rail negotiated and anchors the spec window.
                    source.set_voltage(vin_op)
                    vnl = meter.measure_voltage(
                        f"Vout NO-LOAD @ {rail_name} (nothing on output)")
                    campaign.check_and_record(
                        "vout_noload", vnl, rail_name,
                        unit_id=unit, vin=vin_op, temp_c=temp)

                    # line regulation across the Vin sweep (no load)
                    if vin_pts:
                        lr = M.line_regulation(source, meter, nom, vin_pts)
                        campaign.check_and_record(
                            "line_reg_pct", lr["line_reg_pct"], rail_name,
                            unit_id=unit, temp_c=temp)

                    # load regulation + efficiency at vin_op. Subsample the safe
                    # ladder to light/mid/heavy so a manual run stays feasible
                    # (the full 5V ladder is 26 rungs).
                    full = load.ladder(nom)
                    if full:
                        idxs = sorted({0, len(full) // 2, len(full) - 1})
                        ladder = [full[i] for i in idxs]
                    else:
                        ladder = []
                    if ladder:
                        loadreg = M.load_regulation(source, meter, load,
                                                    vin_op, nom, ladder)
                        campaign.check_and_record(
                            "load_reg_pct", loadreg["load_reg_pct"], rail_name,
                            unit_id=unit, vin=vin_op, temp_c=temp)

                        # efficiency -- opt-in: needs a second (input current)
                        # measurement. Skipped unless --efficiency is passed.
                        if args.efficiency:
                            mid = ladder[len(ladder) // 2]
                            op = M.efficiency_point(source, meter, load, vin_op, mid)
                            campaign.check_and_record(
                                "efficiency_pct", op.efficiency_pct, rail_name,
                                unit_id=unit, vin=vin_op, iout=op.iout, temp_c=temp)

                    # dropout / min Vin -- slow, opt-in, only on rails defining it
                    if args.dropout and "dropout_vin" in rail.limits and "dropout" in plan:
                        dp = plan["dropout"]
                        res = M.dropout(source, meter, nom, dp["vin_start"],
                                        dp["vin_min"], dp["step"])
                        if res["dropout_vin"] is not None:
                            campaign.check_and_record(
                                "dropout_vin", res["dropout_vin"], rail_name,
                                unit_id=unit, temp_c=temp)

    note = ("Real DC measurements on physical QC3.0 buck modules "
            "(SMPS+buck source, DMM, resistor loads). Ripple/transient/PSRR "
            "out of scope -- require an oscilloscope, not faked.")
    html_path = R.write_report(campaign.rows, dut,
                               ROOT / "reports" / "validation_report.html", note)
    R.render_pdf(html_path, ROOT / "reports" / "validation_report.pdf")
    print(f"\nReport written: {html_path}")


if __name__ == "__main__":
    main()