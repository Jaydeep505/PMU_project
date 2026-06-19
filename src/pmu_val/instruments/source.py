"""
Voltage source instruments.

Physical setup today: 12 V SMPS -> adjustable buck module. You turn the pot
and read the value on the multimeter; this is your DUT input voltage (Vin).
The ManualSource backend prompts you to set that voltage and confirms it.

The PyvisaSource backend is the drop-in for a real PC-controlled supply
(Korad/Tenma/Rigol etc.). Fill in the SCPI strings for your model and the
rest of the framework runs an automated Vin sweep with zero other changes.
"""

from __future__ import annotations

from .base import Instrument, InstrumentInfo


class ManualSource(Instrument):
    """Operator-driven voltage source (SMPS + adjustable buck + multimeter)."""

    def __init__(self, name: str = "VIN_SOURCE"):
        super().__init__(name)

    def connect(self) -> None:
        self._connected = True
        print(f"[{self.name}] Manual source ready (SMPS + adjustable buck).")

    def disconnect(self) -> None:
        self._connected = False

    def info(self) -> InstrumentInfo:
        return InstrumentInfo("DIY", "SMPS+buck", "n/a", backend="manual")

    def set_voltage(self, volts: float) -> float:
        """Ask the operator to dial in `volts` and read back the true value."""
        print(f"\n>>> Set INPUT voltage to ~{volts:.2f} V (adjust the buck pot).")
        actual = float(input(f"    Measured Vin with multimeter [V]: ").strip())
        return actual

    def measure_current(self) -> float:
        """Read input current (meter in series on the input)."""
        return float(input(f"    Measured Iin [A]: ").strip())


class PyvisaSource(Instrument):
    """Real SCPI-controlled supply. One-line swap for ManualSource.

    TODO(day-2-or-later): set self.res_str and the SCPI command strings for
    your specific supply, then register this backend instead of ManualSource.
    """

    def __init__(self, name: str = "VIN_SOURCE", resource: str = "ASRL1::INSTR"):
        super().__init__(name)
        self.resource = resource
        self._rm = None
        self._inst = None

    def connect(self) -> None:
        import pyvisa  # imported lazily so the framework runs without hardware
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

    def set_voltage(self, volts: float) -> float:
        self._inst.write(f"VSET1:{volts:.3f}")          # adjust for your model
        return float(self._inst.query("VOUT1?"))         # adjust for your model

    def measure_current(self) -> float:
        return float(self._inst.query("IOUT1?"))         # adjust for your model
