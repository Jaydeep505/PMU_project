"""
Load instruments.

Two backends, same interface:

  * ResistorBank   -- your real ceramic power resistors. Because the load is a
                      *known* resistor, output current is computed as I = Vout/R
                      rather than measured, so a single multimeter is enough.
                      A solver picks safe series/parallel combinations for each
                      output rail so no resistor exceeds its power rating.

  * ElectronicLoad -- placeholder for an adjustable constant-current load, if you
                      ever buy one. Then load current becomes a dialed setpoint.

YOUR INVENTORY (from the photo, edit if it changes):
  * 4 x 7.5 ohm, 5 W   (marking 5W7.5RJ)
  * 2 x 5.6 ohm, 10 W  (marking BEC/10W5R6J)

Tolerance is 5% (J), so measure each resistor's true value once with the DMM
and put the measured ohms in config; the solver and I=V/R use real values.
"""
from __future__ import annotations

import csv
from pathlib import Path
from dataclasses import dataclass
from itertools import combinations
from typing import Literal

from .base import Instrument, InstrumentInfo


@dataclass(frozen=True)
class Resistor:
    ohms: float
    watts: float
    tag: str


@dataclass
class LoadConfig:
    """A concrete load made of resistors, with its computed properties."""
    label: str                 # e.g. "2x7.5 series"
    resistance: float          # total ohms
    topology: Literal["single", "series", "parallel"]
    members: tuple[Resistor, ...]

    def current(self, vout: float) -> float:
        return vout / self.resistance

    def power_per_resistor(self, vout: float) -> float:
        """Worst-case power in any single member at this output voltage."""
        i_total = self.current(vout)
        if self.topology in ("single", "series"):
            # same current through every member
            return max((i_total ** 2) * r.ohms for r in self.members)
        # parallel: each member sees full vout
        return max((vout ** 2) / r.ohms for r in self.members)

    def is_safe(self, vout: float, derate: float = 0.8) -> bool:
        """True if every member stays under `derate` x its rating."""
        i_total = self.current(vout)
        if self.topology in ("single", "series"):
            for r in self.members:
                if (i_total ** 2) * r.ohms > derate * r.watts:
                    return False
            return True
        for r in self.members:
            if (vout ** 2) / r.ohms > derate * r.watts:
                return False
        return True


def _equiv_resistance(members: tuple[Resistor, ...], topology: str) -> float:
    if topology == "series":
        return sum(r.ohms for r in members)
    inv = sum(1.0 / r.ohms for r in members)
    return 1.0 / inv


def enumerate_loads(inventory: list[Resistor], max_members: int = 4) -> list[LoadConfig]:
    """Build every distinct series/parallel load realizable from inventory."""
    configs: list[LoadConfig] = []
    n = len(inventory)
    idxs = range(n)

    # singles
    for i in idxs:
        r = inventory[i]
        configs.append(LoadConfig(r.tag, r.ohms, "single", (r,)))

    # series & parallel groupings of 2..max_members identical-or-mixed parts
    for k in range(2, min(max_members, n) + 1):
        for combo in combinations(idxs, k):
            members = tuple(inventory[i] for i in combo)
            for topo in ("series", "parallel"):
                req = _equiv_resistance(members, topo)
                tags = "+".join(f"{m.ohms:g}" for m in members)
                label = f"{tags} {topo}"
                configs.append(LoadConfig(label, req, topo, members))
    return configs


def safe_load_ladder(inventory: list[Resistor], vout: float,
                     derate: float = 0.8) -> list[LoadConfig]:
    """Return safe loads at `vout`, de-duplicated by resistance, sorted by current."""
    safe = [c for c in enumerate_loads(inventory) if c.is_safe(vout, derate)]
    # de-dup near-equal resistances, keep the one with most headroom
    safe.sort(key=lambda c: (round(c.resistance, 2),
                             c.power_per_resistor(vout)))
    seen, out = set(), []
    for c in safe:
        key = round(c.resistance, 1)
        if key not in seen:
            seen.add(key)
            out.append(c)
    out.sort(key=lambda c: c.current(vout))
    return out


# Nominal fallback, used only if data/resistors.csv doesn't exist yet.
_NOMINAL_INVENTORY = (
    [Resistor(7.5, 5.0, "7.5R/5W") for _ in range(4)]
    + [Resistor(5.6, 10.0, "5.6R/10W") for _ in range(2)]
)

# data/resistors.csv lives at the repo root: load.py is src/pmu_val/instruments/
_RESISTOR_CSV = Path(__file__).resolve().parents[3] / "data" / "resistors.csv"


def load_inventory(csv_path: str | Path = _RESISTOR_CSV) -> list[Resistor]:
    """Build the resistor inventory from measured values in resistors.csv.

    Falls back to nominal if the CSV hasn't been generated yet
    (run scripts/measure_resistors.py to create it). This is the single
    source of truth -- the solver and every I=Vout/R now use real ohms.
    """
    path = Path(csv_path)
    if not path.exists():
        return list(_NOMINAL_INVENTORY)
    inv = []
    with path.open() as f:
        for r in csv.DictReader(f):
            inv.append(Resistor(float(r["measured_ohm"]),
                                 float(r["watts"]), r["id"]))
    return inv


# Default inventory: measured values from data/resistors.csv if present.
DEFAULT_INVENTORY = load_inventory()


class ResistorBank(Instrument):
    """Manual resistor-based load. Operator wires the requested combination."""

    def __init__(self, name: str = "LOAD", inventory: list[Resistor] | None = None):
        super().__init__(name)
        self.inventory = inventory or list(DEFAULT_INVENTORY)

    def connect(self) -> None:
        self._connected = True
        print(f"[{self.name}] Resistor bank ready "
              f"({len(self.inventory)} resistors).")

    def disconnect(self) -> None:
        self._connected = False

    def info(self) -> InstrumentInfo:
        return InstrumentInfo("DIY", "ceramic resistor bank", "n/a",
                              backend="manual")

    def ladder(self, vout: float) -> list[LoadConfig]:
        return safe_load_ladder(self.inventory, vout)

    def apply(self, load: LoadConfig) -> None:
        print(f"\n>>> Wire load: {load.label}  "
              f"(~{load.resistance:.2f} ohm, {load.topology})")
        input("    Press Enter once wired...")


class ElectronicLoad(Instrument):
    """Adjustable CC load placeholder (if you buy one later). Dial a current."""

    def __init__(self, name: str = "LOAD", resource: str = "ASRL2::INSTR"):
        super().__init__(name)
        self.resource = resource

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def info(self) -> InstrumentInfo:
        return InstrumentInfo("TBD", "electronic load", "n/a", backend="manual")

    def set_current(self, amps: float) -> float:
        print(f"\n>>> Set electronic load to {amps:.3f} A")
        return float(input("    Confirm load current [A]: ").strip())


if __name__ == "__main__":
    # Quick demo: show the safe load ladder for each QC rail.
    for rail in (5.0, 9.0, 12.0):
        print(f"\n=== Safe loads at {rail:g} V ===")
        for c in safe_load_ladder(list(DEFAULT_INVENTORY), rail):
            print(f"  {c.label:18s} {c.resistance:6.2f} ohm  "
                  f"I={c.current(rail):.3f} A  "
                  f"Pmax/res={c.power_per_resistor(rail):.2f} W")
