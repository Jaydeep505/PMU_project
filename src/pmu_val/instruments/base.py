"""
Instrument abstraction layer.

Every physical instrument is represented by a subclass of `Instrument`.
The key design decision of this whole framework lives here:

    The measurement code never talks to a real instrument directly.
    It talks to this interface. A real pyvisa/SCPI instrument and a
    manual-entry bench setup are interchangeable backends behind it.

That means swapping a manually-read bench supply for a PC-controlled
SCPI source meter is a *one-line change* in the instrument registry --
the test sequencer, limit logic, statistics and reporting are untouched.
This mirrors how production validation/ATE software is structured.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class InstrumentInfo:
    """Identification returned by *IDN?-style queries."""
    manufacturer: str = "unknown"
    model: str = "unknown"
    serial: str = "unknown"
    backend: str = "unknown"  # "manual", "pyvisa", "simulated"

    def idn(self) -> str:
        return f"{self.manufacturer},{self.model},{self.serial}"


class Instrument(abc.ABC):
    """Abstract base for all instruments.

    Subclasses implement the small set of primitives below. The rest of
    the framework only ever calls these primitives, so any backend that
    can satisfy them (real SCPI, manual entry, simulation) plugs straight in.
    """

    def __init__(self, name: str):
        self.name = name
        self._connected = False

    # -- lifecycle ---------------------------------------------------------
    @abc.abstractmethod
    def connect(self) -> None:
        """Open the instrument (open VISA resource, print a banner, etc.)."""

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Release the instrument."""

    @abc.abstractmethod
    def info(self) -> InstrumentInfo:
        """Return identification info."""

    # -- context manager sugar --------------------------------------------
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.disconnect()
        return False
