"""
Instrument registry / bench builder.

This is the single place that decides which backend each instrument uses.
Going from your manual bench to a fully automated SCPI bench is editing the
three lines below -- nothing downstream changes. That is the whole point of
the abstraction layer.
"""

from __future__ import annotations

from .meter import ManualMeter, PyvisaMeter
from .source import ManualSource, PyvisaSource
from .load import ResistorBank, ElectronicLoad


def build_bench(backend: str = "manual"):
    """Return (source, meter, load) for the chosen backend.

    backend="manual"  -> SMPS+buck, handheld DMM, resistor bank (today)
    backend="pyvisa"  -> real SCPI source/meter (+ resistor bank or e-load)
    """
    if backend == "manual":
        return ManualSource(), ManualMeter(), ResistorBank()
    if backend == "pyvisa":
        # TODO: set the VISA resource strings for your instruments
        return PyvisaSource(), PyvisaMeter(), ResistorBank()
    raise ValueError(f"unknown backend: {backend}")
