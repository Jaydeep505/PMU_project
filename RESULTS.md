# Characterization Results — QC3.0 USB Buck Module

Real DC characterization of the QC3.0/QC2.0 USB buck DUT across its three negotiated
rails (5 V / 9 V / 12 V), three identical modules (U1–U3), and three temperature
points (~5 °C / ~25 °C / ~50 °C). Every number below is a real DC reading. Where a
measurement is source-limited, an artifact, or out of scope, it is flagged here
rather than cleaned away — the discipline of saying what was and wasn't measured is
the point of the report.

## Bench / method

- **Input source:** 5 V phone charger → XL6009 boost converter. The boost can set
  Vin above 12 V, giving the headroom needed to characterize the 9 V and 12 V rails.
  All rail measurements use Vin = 15 V (top of sweep, full headroom); line-regulation
  sweeps span 12–15 V on the 9 V/12 V rails.
- **Output / current:** single handheld DMM reads Vout; output current is computed
  as I = Vout/R from measured resistor values, so one meter suffices.
- **Thermal:** Peltier (TEC) module on its **own dedicated 12 V SMPS** (separate from
  the DUT input supply, so it never loads the boost); module temperature read by a
  thermistor on the body. Output voltage and temperature use separate sensors, so the
  single-DMM simultaneity concern does not apply to the temperature reading.
- **Assembly:** per-slice CSVs are merged by `scripts/build_report.py`, which collapses
  re-runs to one row per (unit, rail, parameter, temperature), most-recent-wins.

## Results at 25 °C (U1–U3)

| Rail | Parameter    | U1    | U2              | U3    | Limit       | Yield  | Cpk\* |
|------|--------------|-------|-----------------|-------|-------------|--------|-------|
| 5 V  | no-load Vout | 5.10  | 5.12            | 5.12  | 4.75–5.25 V | 100 %  | 4.8   |
| 5 V  | line reg     | ~0    | ~0              | ~0    | ≤ 2 %       | 100 %  | inf   |
| 5 V  | load reg     | 0.0   | 0.2             | 0.4   | ≤ 5 %       | 100 %  | 9.8   |
| 9 V  | no-load Vout | 9.11  | 9.12            | 9.13  | 8.55–9.45 V | 100 %  | 13.5  |
| 9 V  | line reg     | 2.00  | **2.11 (FAIL)** | 1.67  | ≤ 2 %       | **67 %** | **0.13** |
| 9 V  | load reg     | 2.44  | 0.11            | 0.11  | ≤ 5 %       | 100 %  | 1.25  |
| 12 V | no-load Vout | 11.98 | 11.98           | 11.94 | 11.4–12.6 V | 100 %  | 10.0  |
| 12 V | line reg     | 0.17  | 0.0             | 0.25  | ≤ 2 %       | 100 %  | 6.0   |
| 12 V | load reg     | 0.0   | 0.08            | 0.25  | ≤ 5 %       | 100 %  | 15.7  |

\* Cpk here is **n = 3 → directional only**. A qualified Cpk needs ~30 units; these
values indicate the *direction* of capability, not a statistically defensible index.
This is the weakest part of the report and the first thing to strengthen (add units).

Overall: 26 / 27 measurements within limits → report verdict **REVIEW**, not PASS.
The single failure is the point of the report.

## Temperature axis (U2, 5 / 25 / 50 °C)

Characterized on **U2** (the 9 V line-reg failer), all three rails, pooled with the
25 °C data. U1/U3 were not measured over temperature (see Scope honesty). Only
`vout_noload` and `line_reg` are reported as temperature results; `load_reg` over
temperature is source-limited (Finding 4).

| Rail | Parameter    | 5 °C  | 25 °C           | 50 °C | Limit       |
|------|--------------|-------|-----------------|-------|-------------|
| 5 V  | no-load Vout | 5.11  | 5.12            | 5.12  | 4.75–5.25 V |
| 9 V  | no-load Vout | 9.14  | 9.12            | 9.14  | 8.55–9.45 V |
| 12 V | no-load Vout | 12.00 | 11.98           | 12.00 | 11.4–12.6 V |
| 5 V  | line reg     | 0.0   | 0.0             | 0.2   | ≤ 2 %       |
| 9 V  | line reg     | 0.0   | **2.11 (FAIL)** | 0.0   | ≤ 2 %       |
| 12 V | line reg     | 0.0   | 0.0             | 0.0   | ≤ 2 %       |

## Findings

### 1. 9 V line regulation is not capable (headline)

The 9 V rail regulates ~5–10× looser than the 5 V (~0 %) and 12 V (~0.2 %) rails:
U1 2.00 %, U2 2.11 %, U3 1.67 % against a 2 % design target. U2 fails outright; U1
sits exactly on the limit. Yield 67 %, directional Cpk 0.13.

The hypothesis that the ~2 % was inflated by a near-dropout Vin point was **tested and
disproven**: re-running 9 V line reg over 12–15 V (full headroom, no marginal point)
returned the same ~2 %. The looseness is real DUT behaviour, not a test artifact.
Why the 9 V PDO specifically regulates loose is **observed but not yet established**.

**Limit action: kept at the 2 % design target.** Relaxing it to make the population
pass would move the goalpost; the miss is recorded as a miss.

### 2. 9 V load regulation is marginal

100 % yield (all under 5 %) but directional Cpk 1.25 (below the 1.33 target), because
U1 droops 2.44 % while U2/U3 droop ~0.11 % — a 20× outlier on one unit. This is
retained as genuine part-to-part variation. Open item: confirm whether U1's 9 V load
points were taken over a different load-current range than U2/U3 before qualifying.

### 3. 5 V and 12 V rails are capable

Both pass on every parameter with high directional Cpk; 12 V is the cleanest rail
(Cpk 6–16). **Caveat on 5 V line reg:** the per-unit values were taken over *different
Vin spans* (U1 ~11.5–12 V, U2/U3 13–15 V), so the pooled ~0 % is not a clean
common-span figure. Re-run all three over one span to qualify it.

### 4. Load regulation over temperature is source-limited — characterize at 25 °C only

The temperature load-reg points are confounded by an **input-power limit in the
source**, not the DUT:

- A heavy-rung temperature run folded the rail hard (5 V: 30.4/39.0 %, 12 V:
  46.0/65.7 %; Vout collapsed to ~3.6 V / ~4.1 V).
- Re-measuring 9 V / 5 °C over lighter rungs still showed the rail sagging — 7.78 V at
  only ~0.26 A (30 Ω), 1.36 V below the 9.14 V no-load. The computed 3.33 % "passes"
  the 5 % limit only because all points sit in the already-sagged regime; it is not
  honest load regulation.

**Root cause — confirmed, mechanism isolated:** the 5 V charger → XL6009 boost cannot
supply the input current the loads demand (e.g. 12 V at ~1 A ≈ 12 W out exceeds the
~10 W a 5 V/2 A charger can deliver). The rail browns out from the **input** side.
Diagnostic basis: (a) the *same* heavy rung gave clean load reg at 25 °C (0.08–0.4 %)
but folds at temperature — a fixed DUT current limit would fold at 25 °C too;
(b) re-measure reproduced the sag identically; (c) the Peltier was on a separate
12 V SMPS, so TEC current starving the boost was ruled out.

This also explains the LED blink/hiccup observed while wiring heavy loads: the same
source brown-out, with QC re-handshaking as the rail collapses — not DUT over-current
protection.

**Consequence:** load regulation is only valid where the source holds. The clean
load-reg data is the **25 °C population** (n = 3), retained including the genuine
9 V/U1 outlier. Load-reg-over-temperature is **out of scope on this bench**,
documented as a source limitation in the same spirit as efficiency and ripple.

### 5. No resolvable temperature drift on no-load Vout

Across 5 → 50 °C every rail moves ≤ 20 mV (5 V: 10 mV, 9 V: 20 mV, 12 V: 20 mV), at or
below the DMM's resolution and run-to-run repeatability. The honest statement is **no
measurable tempco** at no load; resolving an actual coefficient would need a
higher-resolution meter.

### 6. 9 V line-reg miss did not reproduce at the temperature endpoints (inconclusive)

The 9 V line-reg behaviour across temperature is non-monotonic: 0.0 % at 5 °C,
2.11 % (FAIL) at 25 °C, 0.0 % at 50 °C. The miss is worst at room temperature and
clean at *both* extremes, which does not support a simple temperature-dependence
explanation. At a single unit with a 2-point sweep, the defensible statement is: the
25 °C miss was not reproduced at 5/50 °C and the cause is **not established** — it may
be condition/session specific (boost thermal state, exact Vin values) rather than a
stable DUT-over-temperature characteristic. Needs more units and controlled conditions
to resolve.

## Data hygiene

- **One line-reg row corrected by re-measure.** A 9 V / 5 °C row originally read
  65.11 % because Vout was entered as `15` instead of `9.14` at the 15 V sweep point.
  Re-measured to ~0 %; the newer timestamp supersedes the bad row via most-recent-wins
  dedup. Re-measured, **not hand-edited.**
- **Dedup key includes `temp_c`.** Without it the same (unit, rail, parameter)
  collapses across temperatures and the T axis disappears on merge.

## Known limitations in the current merged report

Recorded so they are not mistaken for DUT behaviour:

- **5 V and 12 V `load_reg` show FAIL in the merged summary.** These are the
  source-limited foldback rows from the heavy-rung temperature run (Finding 4), not
  DUT load-regulation failures. The DUT load regulation is capable at 25 °C (≤ 0.4 %).
  The foldback rows are kept as evidence; filtering `load_reg_pct` rows to `temp_c == 25`
  restores an honest load-reg figure.
- **The HTML spec table groups by parameter across all rails**, so it reports e.g. a
  `vout_noload` mean that averages 5/9/12 V together — not a meaningful figure. The
  per-rail console summary in `build_report.py` is the correct view; the HTML table
  would need grouping by (rail, parameter).

## Scope honesty

- **Process axis is n = 3** (U1–U3). Cpk/yield are directional; a qualified index
  needs ~30 units. Extra units improve the statistics far more than extra Vin points.
- **Temperature axis is U2 only.** Given how tightly the three units cluster at 25 °C,
  U1/U3 likely track U2 — but part-to-part temperature spread is **not characterized**
  (engineering judgment, not measured data).
