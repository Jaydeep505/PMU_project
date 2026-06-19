"""
Device-under-test description and spec limits.

The DUT is your QC3.0/QC2.0 USB buck converter module. Each output rail
(5 V / 9 V / 12 V) has a set of spec limits. Limits live in YAML
(config/dut_qc3.yaml) so the framework is data-driven, not hard-coded.

HONESTY NOTE: this module has no real datasheet. The starting limits below
are grounded in the USB QC voltage tolerance (typically +/-5%) and typical
small buck efficiency. The intended workflow is: measure nominal behaviour
once, then set limits around observed + spec values. Document where each
limit came from -- that traceability is itself a validation skill.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SpecLimit:
    parameter: str
    units: str
    lower: float | None = None
    upper: float | None = None
    typ: float | None = None
    source: str = ""        # where this limit came from (traceability)


@dataclass
class Rail:
    name: str               # e.g. "5V"
    vout_nom: float
    limits: dict[str, SpecLimit] = field(default_factory=dict)


@dataclass
class DUT:
    part: str
    description: str
    rails: dict[str, Rail] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "DUT":
        data = yaml.safe_load(Path(path).read_text())
        rails: dict[str, Rail] = {}
        for rname, rdata in data["rails"].items():
            limits = {
                p: SpecLimit(parameter=p, **ldata)
                for p, ldata in rdata.get("limits", {}).items()
            }
            rails[rname] = Rail(rname, rdata["vout_nom"], limits)
        return cls(data["part"], data.get("description", ""), rails)
