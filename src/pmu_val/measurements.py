"""
Measurement routines.

Each function drives the abstract instruments to take one DC characterization
measurement and returns the computed figure of merit. Because the instruments
are abstract, these exact functions work unchanged whether the data comes from
your manual bench or a real SCPI bench.

WHAT IS REAL WITH YOUR KIT (no scope):
  * line regulation   -- sweep Vin, watch Vout drift at fixed load
  * load regulation   -- sweep load current, watch Vout droop at fixed Vin
  * efficiency        -- eta = (Vout*Iout)/(Vin*Iin); Iout = Vout/R (known R)
  * dropout / min Vin -- lower Vin until the rail can no longer regulate
  * quiescent current -- input current at no/very light load

OUT OF SCOPE (needs an oscilloscope -- intentionally excluded, not faked):
  * output ripple, switching frequency, load-transient response, PSRR
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OperatingPoint:
    vin: float
    iin: float
    vout: float
    iout: float

    @property
    def pin(self) -> float:
        return self.vin * self.iin

    @property
    def pout(self) -> float:
        return self.vout * self.iout

    @property
    def efficiency_pct(self) -> float:
        return 100.0 * self.pout / self.pin if self.pin > 0 else 0.0


def line_regulation(source, meter, rail_nom: float,
                    vin_points: list[float]) -> dict:
    """Vout vs Vin at fixed (light) load. Returns deviation in %% of nominal."""
    readings = []
    for v in vin_points:
        source.set_voltage(v)
        vout = meter.measure_voltage(f"Vout @ Vin={v:g}V")
        readings.append((v, vout))
    vouts = [vo for _, vo in readings]
    span = max(vouts) - min(vouts)
    line_reg_pct = 100.0 * span / rail_nom
    return {"readings": readings, "line_reg_pct": line_reg_pct}


def load_regulation(source, meter, load, vin: float, rail_nom: float,
                    load_ladder) -> dict:
    """Vout vs Iout at fixed Vin. Returns droop in %% of nominal."""
    source.set_voltage(vin)
    points = []
    for lc in load_ladder:
        load.apply(lc)
        vout = meter.measure_voltage(f"Vout @ load={lc.label}")
        iout = vout / lc.resistance
        points.append((iout, vout))
    vouts = [vo for _, vo in points]
    droop = max(vouts) - min(vouts)
    load_reg_pct = 100.0 * droop / rail_nom
    return {"points": points, "load_reg_pct": load_reg_pct}


def efficiency_point(source, meter, load, vin: float, lc) -> OperatingPoint:
    """One efficiency operating point at given Vin and resistor load."""
    source.set_voltage(vin)
    load.apply(lc)
    iin = source.measure_current()
    vout = meter.measure_voltage(f"Vout @ {lc.label}")
    iout = vout / lc.resistance
    return OperatingPoint(vin=vin, iin=iin, vout=vout, iout=iout)


def dropout(source, meter, rail_nom: float, vin_start: float,
            vin_min: float, step: float, regulation_band_pct: float = 5.0) -> dict:
    """Lower Vin until Vout falls outside the regulation band; report that Vin."""
    band = rail_nom * (1 - regulation_band_pct / 100.0)
    v = vin_start
    last_ok = None
    trace = []
    while v >= vin_min:
        source.set_voltage(v)
        vout = meter.measure_voltage(f"Vout @ Vin={v:g}V (dropout search)")
        trace.append((v, vout))
        if vout >= band:
            last_ok = v
        else:
            break
        v -= step
    return {"trace": trace, "dropout_vin": last_ok, "band_v": band}
