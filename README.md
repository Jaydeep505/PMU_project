# PMU Validation & Characterization Framework

A Python framework for **DC validation and statistical characterization of a power
management DUT over process, voltage, and temperature (PVT)** — built and validated
against real QC3.0 USB buck-converter modules on a hobbyist bench, architected to
drop onto real lab/ATE equipment with a one-line backend change.

> **Data honesty (read first).** Every number in the generated report is real DC
> measurement from physical modules, or is explicitly labelled otherwise. Fast
> AC behaviour (output ripple, switching frequency, load-transient response, PSRR)
> **requires an oscilloscope and is intentionally out of scope — it is not
> simulated or faked.** Stating exactly what was and wasn't measured is itself a
> validation discipline.

## What it does

- **Instrument abstraction layer** — a SCPI-style interface with interchangeable
  backends: manual bench entry today, `pyvisa` SCPI tomorrow. The measurement,
  limit, statistics and reporting code never changes between them.
- **Test sequencer** — executes an ordered PVT test plan, checks every result
  against data-driven spec limits, logs pass/fail to CSV.
- **DC measurements** — line regulation, load regulation, efficiency, dropout.
- **Statistical characterization** — distributions, **Cpk**, **yield**, and a
  **shmoo** pass/fail map over Vin × temperature.
- **Auto-generated report** — single-file HTML (optional PDF) with an executive
  summary, spec table, and shmoo grid.

## How PVT is made real on a hobby bench

| Axis | Real-world meaning | How it's covered here |
|------|--------------------|------------------------|
| **P** rocess | part-to-part / die variation | **multiple identical modules** — unit-to-unit spread is the honest proxy; drives real Cpk & yield |
| **V** oltage | input supply range | Vin swept via SMPS + adjustable buck, read on the DMM |
| **T** emperature | operating range | rough points: fridge ~5 °C, room ~25 °C, warm-air ~50 °C |

The QC trigger board negotiates the 5 V / 9 V / 12 V output rails so all three are
characterized. A solver picks **safe series/parallel resistor combinations** for
each rail so no power resistor exceeds its rating (see `instruments/load.py`).

## Bench setup

```
12V SMPS ──► adjustable buck ──► [DUT: QC3.0 module] ──USB──► QC trigger ──► resistor load
                  │                      │                                        │
               (set Vin)            (DMM: Vout)                            (I = Vout / R)
```
One multimeter is sufficient: output current is computed from the *known measured*
resistor value (`scripts/measure_resistors.py`), not measured directly.

## Quick start

```bash
pip install -r requirements.txt

# 1. See the safe load ladder the solver picks for each rail
PYTHONPATH=src python -m pmu_val.instruments.load

# 2. Exercise the analysis+report pipeline with synthetic data (no hardware)
python scripts/demo_pipeline.py            # -> reports/demo_report.html

# 3. Calibrate your real resistors once
python scripts/measure_resistors.py        # -> data/resistors.csv

# 4. Run the real campaign (prompts you at the bench)
python scripts/run_campaign.py             # -> data/campaign.csv + report

# tests
PYTHONPATH=src pytest -q
```

Swapping to automated SCPI hardware later: implement the `*_QUERY` strings in
`instruments/source.py` / `meter.py` and call `build_bench("pyvisa")`. Nothing
else changes.

## Repository layout

```
src/pmu_val/
  instruments/   base, source, meter, load (+ safe-combo solver), registry
  dut.py         DUT + spec limits (from YAML)
  limits.py      pass/fail checking
  measurements.py line/load reg, efficiency, dropout
  sequencer.py   campaign runner + CSV logging
  analysis.py    Cpk, yield, distributions, shmoo
  report.py      HTML/PDF report
config/          dut_qc3.yaml (limits), test_plan.yaml (PVT matrix)
scripts/         run_campaign, measure_resistors, demo_pipeline
tests/           pytest suite
```

## How this maps to the target role (Silicon Validation Engineer, Power Mgmt)

- *Python scripts to validate ICs over process, voltage, temperature* → the whole framework
- *Generating validation reports and documentation* → `report.py` + this README
- *Power topologies (LDO/buck/switch)* → buck DUT characterized across rails
- *Lab equipment / measurement automation* → SCPI-ready instrument layer
- *Statistical analysis for silicon characterization* → Cpk, yield, shmoo
- *Read/interpret schematics* → bench schematic + labelled test points

## Notes for the interview

**"Why a cheap module and not real silicon?"** I scoped to what demonstrates the
*methodology* end-to-end: real DC characterization, part-to-part statistics, an
ATE-style sequencer, and a hardware-ready instrument layer. The framework is
backend-swappable, so on real lab equipment it's a one-line change and re-run.

**"Why no ripple/transient?"** Those need an oscilloscope, which I didn't have, so
I left them explicitly out of scope rather than fabricate them. I'd add them as
scope-driven measurements behind the same instrument interface.

**"What does Cpk mean here?"** Process capability of each spec against its limits,
computed across the unit-to-unit population — my honest stand-in for process
variation given I can't vary a real fab process.
```
```
