"""
Multimeter / voltmeter abstraction.

Today this is your handheld DMM, read by eye (ManualMeter). If your DMM has
a serial/USB-PC interface, PyvisaMeter turns the same reads into automated
SCPI queries with no change to the calling code.
"""

from __future__ import annotations

from .base import Instrument, InstrumentInfo


class ManualMeter(Instrument):
    """Operator reads the multimeter and types the value."""

    def __init__(self, name: str = "DMM"):
        super().__init__(name)

    def connect(self) -> None:
        self._connected = True
        print(f"[{self.name}] Manual multimeter ready.")

    def disconnect(self) -> None:
        self._connected = False

    def info(self) -> InstrumentInfo:
        return InstrumentInfo("DIY", "handheld DMM", "n/a", backend="manual")

    def measure_voltage(self, label: str = "Vout") -> float:
        return float(input(f"    Measured {label} [V]: ").strip())


class PyvisaMeter(Instrument):
    """Real SCPI multimeter. Drop-in replacement for ManualMeter."""

    def __init__(self, name: str = "DMM", resource: str = "USB0::INSTR"):
        super().__init__(name)
        self.resource = resource
        self._rm = None
        self._inst = None

    def connect(self) -> None:
        import pyvisa
        self._rm = pyvisa.ResourceManager()
        self._inst = self._rm.open_resource(self.resource)
        self._connected = True

    def disconnect(self) -> None:
        if self._inst:
            self._inst.close()
        self._connected = False

    def info(self) -> InstrumentInfo:
        idn = self._inst.query("*IDN?") if self._inst else "n/a"
        parts = (idn.split(",") + ["", "", ""])[:3]
        return InstrumentInfo(*[p.strip() for p in parts], backend="pyvisa")

    def measure_voltage(self, label: str = "Vout") -> float:
        return float(self._inst.query("MEAS:VOLT:DC?"))  # adjust for your model
