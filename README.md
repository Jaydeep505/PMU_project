# PMU Validation & Characterization Framework

A Python framework for **DC validation and statistical characterization of a power
management DUT over process, voltage, and temperature (PVT)** — built and validated
against real QC3.0 USB buck-converter modules on a hobbyist bench, architected to
drop onto real lab/ATE equipment with a one-line backend change.

> **Data honesty (read first).** Every number in the generated report is a real DC
> measurement from physical modules, or is explicitly labelled otherwise. Fast
> AC behaviour (output ripple, switching frequency, load-transient response, PSRR)
> **requires an oscilloscope and is intentionally out of scope — it is not
> simulated or faked.** Stating exactly what was and wasn't measured is itself a
> validation discipline. See [`RESULTS.md`](RESULTS.md) for the full characterization
> writeup, including a spec the population misses (recorded as a miss, not relaxed).

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
| **V** oltage | input supply range | Vin swept via 5 V charger → XL6009 boost, read on the DMM |
| **T** emperature | operating range | Peltier (TEC) thermal source on a dedicated 12 V SMPS; module temperature read by an on-board **thermistor** (separate from the DMM). Endpoints ~5 °C / ~50 °C; room ~25 °C |

The QC trigger board negotiates the 5 V / 9 V / 12 V output rails so all three are
characterized. A solver picks **safe series/parallel resistor combinations** for
each rail so no power resistor exceeds its rating (see `instruments/load.py`).

## Bench setup

```
5V charger ──► XL6009 boost ──► [DUT: QC3.0 module] ──USB──► QC trigger ──► resistor load
                  │                      │                                        │
               (set Vin)            (DMM: Vout)                            (I = Vout / R)
```
One multimeter is sufficient: output current is computed from the *known measured*
resistor value (`scripts/measure_resistors.py`), not measured directly.

> **Source input-power ceiling (scope limit).** The input chain is a 5 V phone
> charger → XL6009 boost. Its input-power budget (~10 W) is below what the heavier
> loads demand, so above a modest load current the rail browns out from the
> **input side**, not the DUT. Load regulation is therefore characterized at 25 °C
> (where the source had headroom); load-reg over temperature is out of scope on this
> bench. Stated as a limitation, like efficiency and ripple — not simulated or
> worked around.

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

# 5. Reassemble all measurement slices into one population + report
python scripts/build_report.py             # -> reports/validation_report.html

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
config/          dut_qc3.yaml (limits), test_plan*.yaml (PVT matrices)
scripts/         run_campaign, build_report, measure_resistors, demo_pipeline
data/            per-slice measurement CSVs (the raw evidence)
tests/           pytest suite (runs in CI across Python 3.10–3.12)
RESULTS.md       characterization findings + honest scope
```

## Results

The headline result is a real failure, kept as a failure: the **9 V rail's line
regulation is not capable** against a 2 % design target (67 % yield across three
units), confirmed real on a re-run rather than relaxed away. The 5 V and 12 V rails
are capable on every parameter. Full numbers, the load-reg outlier, the temperature
behaviour, and the source-limited rows are written up in [`RESULTS.md`](RESULTS.md).

## How this maps to the target role (Silicon Validation Engineer, Power Mgmt)

- *Python scripts to validate ICs over process, voltage, temperature* → the whole framework
- *Generating validation reports and documentation* → `report.py` + `RESULTS.md`
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
variation given I can't vary a real fab process. With three units the Cpk is
directional only; a qualified index needs ~30 units.

**"Your report shows load-reg failures over temperature?"** Those are a source
input-power limit — the 5 V → XL6009 boost browns out under heavy load — not DUT
behaviour. The DUT's load regulation is capable at 25 °C (≤ 0.4 %). I left the
foldback rows in as evidence and documented the source limit rather than deleting
them; the honest scope is load-reg at 25 °C.
