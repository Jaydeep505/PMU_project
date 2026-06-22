# Day 3 Findings — Temperature Axis (U2, 5 °C / 25 °C / 50 °C)

> **Scope of this run.** Temperature axis characterized on **U2 only**, across
> all three rails, at ~5 °C and ~50 °C, pooled with the existing 25 °C data.
> U1/U3 were **not** measured over temperature (see "Scope honesty"). Every
> number here is a real DC reading; the one data-entry error and the
> source-limited load-reg rows are flagged, not cleaned away.

## Bench / method

- **Thermal source:** Peltier (TEC) module, run from its **own dedicated 12 V
  SMPS** — separate from the DUT input supply, so it does not load the boost.
- **Temperature readout:** thermistor mounted on the module body. Because it is
  a separate sensor, output voltage and temperature never contend for the single
  DMM — the soak-then-measure simultaneity concern does not apply to the temp
  reading. Points were taken after the thermistor reading had stabilised (soak
  to equilibrium).
- **Conditions matched to 25 °C** for poolability: Vin op = 15 V, line-reg sweep
  13–15 V (2-point), same three rails.

## Clean results (the headline)

Only `vout_noload` and `line_reg` are reported as temperature results.
`load_reg` over temperature is **not** a clean result on this bench — see
Finding 3.

| Rail | Parameter    | 5 °C  | 25 °C       | 50 °C | Limit       |
|------|--------------|-------|-------------|-------|-------------|
| 5 V  | no-load Vout | 5.11  | 5.12        | 5.12  | 4.75–5.25 V |
| 9 V  | no-load Vout | 9.14  | 9.12        | 9.14  | 8.55–9.45 V |
| 12 V | no-load Vout | 12.00 | 11.98       | 12.00 | 11.4–12.6 V |
| 5 V  | line reg     | 0.0   | 0.0         | 0.2   | ≤ 2 %       |
| 9 V  | line reg     | 0.0   | **2.11 (FAIL)** | 0.0 | ≤ 2 %   |
| 12 V | line reg     | 0.0   | 0.0         | 0.0   | ≤ 2 %       |

25 °C values are U2 from the Day-2 `multi.csv` run (same 13–15 V span).

## Findings

### 1. No-load Vout has no resolvable temperature drift

Across 5 → 50 °C every rail moves ≤ 20 mV (5 V: 10 mV, 9 V: 20 mV, 12 V: 20 mV),
at or below the handheld DMM's resolution and run-to-run repeatability. The
honest statement is **no measurable tempco** at no load — not a small one;
resolving an actual coefficient would need a higher-resolution meter. The rails
are temperature-stable at no load across this range.

### 2. The 9 V line-reg miss did NOT reproduce at the temperature endpoints (inconclusive)

The 9 V line-reg behaviour across temperature is **non-monotonic**:

- 5 °C: **0.0 % — PASS**
- 25 °C: **2.11 % — FAIL** (confirmed real on the Day-2 re-run)
- 50 °C: **0.0 % — PASS**

The miss is worst at room temperature and clean at *both* extremes. This does
**not** support a simple temperature-dependence ("loosens as it heats/cools")
explanation. At a single unit, with a 2-point sweep and one reading per point,
the most defensible statement is: the 25 °C miss was not reproduced at the 5/50 °C
re-runs, and the cause is **not established** — it may be condition/session
specific (e.g. boost thermal state, exact Vin values) rather than a stable
DUT-over-temperature characteristic. 5 V and 12 V line reg stay flat and capable
at all three temperatures; the irregularity is specific to the 9 V PDO,
consistent with the 25 °C picture. **Needs more units and controlled conditions
to resolve** — left open, not over-claimed.

### 3. Load regulation over temperature is source-limited — characterise at 25 °C only

The temperature load-reg points are confounded by an **input-power limit in the
source**, not the DUT:

- Original heavy-rung temp run folded the rail hard (5 V: 30.4/39.0 %, 12 V:
  46.0/65.7 %; Vout collapsed to ~3.6 V / ~4.1 V).
- Re-measuring 9 V/5 °C over lighter rungs still showed the rail sagging — 7.78 V
  at only ~0.26 A (30 Ω), 1.36 V below the 9.14 V no-load. The computed 3.33 %
  "passes" the 5 % limit only because all points sit in the already-sagged
  regime; it is not honest load regulation.

**Root cause — confirmed, mechanism isolated:** the 5 V phone-charger → XL6009
boost cannot supply the input current the loads demand (e.g. 12 V at ~1 A ≈ 12 W
out exceeds the ~10 W a 5 V/2 A charger can deliver). The rail browns out from
the **input** side. Diagnostic basis: (a) the *same* heavy rung gave clean load
reg at 25 °C (0.08–0.4 %) but folds at temperature — a fixed DUT current limit
would fold at 25 °C too; (b) re-measure reproduced the sag identically. The
Peltier was on a **separate 12 V SMPS**, so TEC current starving the boost was
considered and **ruled out** — the limit is the DUT input supply alone.

This also closes **Day-2 Finding 4** (LED hiccup under load): the same source
brown-out, with QC re-handshaking as the rail collapses — not DUT over-current
protection.

**Consequence:** load regulation is only valid where the source holds. The clean
load-reg data is the **25 °C population** (n = 3), which is retained — including
the genuine 9 V/U1 outlier (2.44 % vs U2/U3 0.11 %), which is real DUT part-to-part
variation and stays in. Load-reg-over-temperature is **out of scope on this
bench**, documented as a source limitation in the same spirit as efficiency and
ripple — not a gap.

## Data hygiene / corrections

- **9 V/5 °C line-reg typo corrected by re-measure.** The original row read
  65.11 % because Vout was entered as `15` instead of `9.14` at the 15 V sweep
  point. Re-measured to ~0 % in `data/temp_u2_fix.csv`; the newer timestamp
  supersedes the bad row via most-recent-wins dedup. Re-measured, **not
  hand-edited.**
- **`build_report.py` dedup key.** Extended to include `temp_c`; without it the
  same (unit, rail, parameter) collapses across temperatures and the T axis
  disappears on merge. Verified: 9 V line reg now shows n = 5 (U1/U2/U3 @ 25 °C
  + U2 @ 5/50 °C).

## Known limitations in the current merged report (acknowledged, not fixed)

Recorded here honestly so they are not mistaken for DUT behaviour:

- **5 V and 12 V `load_reg` show FAIL (60 % yield) in the merged summary.** These
  are the **source-limited foldback rows** from the original heavy-rung temp run
  (Finding 3), not DUT load-regulation failures. The DUT load regulation is
  capable at 25 °C (≤ 0.4 %). The foldback rows are kept in the raw slices as
  evidence; excluding them from load-reg statistics (filter `load_reg_pct` rows
  where `temp_c != 25`) would restore an honest load-reg figure — left as a
  documented item.
- **HTML spec table groups by parameter across all rails**, so it reports e.g.
  `vout_noload mean 8.741 V` — the 5/9/12 V rails averaged together, which is not
  a meaningful figure. The per-rail console summary in `build_report.py` is the
  correct view; the HTML table would need grouping by (rail, parameter).

## Scope honesty

- **Temperature axis is U2 only.** U1/U3 were not run over temperature.
  Expectation (engineering judgment, *not* measured data): given how tightly the
  three units cluster at 25 °C, U1/U3 are likely to track U2's temperature
  behaviour — but part-to-part temperature spread is **not characterised**.
- **Process axis remains n = 3** (no working U4/U5); Cpk stays directional.
- Efficiency deferred (single-DMM simultaneity). Ripple / transient / PSRR out of
  scope — need an oscilloscope, not simulated.
