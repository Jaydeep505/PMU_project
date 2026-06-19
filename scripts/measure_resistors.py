"""
Measure the true resistance of each power resistor once, with the DMM, and
save to data/resistors.csv. The 'J' tolerance is 5%, so using measured values
(not nominal) makes every Iout = Vout/R computation honest.

Run:  python scripts/measure_resistors.py
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "resistors.csv"

NOMINAL = (
    [("7.5R/5W", 7.5, 5.0)] * 4 
    + [("5.6R/10W", 5.6, 10.0)] * 2 
)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    print("Measure each resistor with the DMM (ohms) and enter the reading.\n")
    for i, (tag, nom, watt) in enumerate(NOMINAL, 1):
        try:
            r = input(f"  R{i} ({tag}, nominal {nom} ohm) measured [ohm]: ").strip()
        except EOFError:
            print("\n(no input -- using nominal values)")
            r = nom
        rows.append({"id": f"R{i}", "tag": tag, "nominal_ohm": nom,
                     "measured_ohm": float(r), "watts": watt})
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, ["id", "tag", "nominal_ohm", "measured_ohm", "watts"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved {len(rows)} resistors -> {OUT}")


if __name__ == "__main__":
    main()
