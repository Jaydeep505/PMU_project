# Day 2 Findings — PVT Characterization (5 V / 9 V / 12 V, U1–U3, 25 °C)

## Scope

Day 2 extended the Day-1 5 V shakedown to all three negotiated rails (5 V, 9 V,
12 V) across three identical modules (U1, U2, U3) at room temperature (~25 °C).

**Source change.** The adjustable buck used on Day 1 was defective and replaced
with a 5 V phone charger → XL6009 boost converter. Unlike the buck, the boost
can set Vin above 12 V, which provides the headroom needed to characterize the
9 V and 12 V rails. All rail measurements use Vin = 15 V (top of sweep, full
headroom); line-regulation sweeps span 12–15 V on the 9 V/12 V rails.

**Population.** 3 units × 3 rails × 3 DC parameters (no-load Vout, line reg,
load reg) = 27 measurements, room temp only. Assembled with
`scripts/build_report.py`, which merges the per-slice CSVs and collapses re-runs
to one row per (unit, rail, parameter), most-recent-wins.

## Results

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

\* Cpk is **n = 3 → directional only**. A qualified Cpk needs ~30 units; these
values indicate the *direction* of capability, not a statistically defensible
index. This is the weakest part of the current report and the first thing to
strengthen (add units).

Overall: 26 / 27 measurements within limits → report verdict **REVIEW**, not
PASS. The single failure is the point of the report.

## Key findings

### 1. 9 V line regulation is not capable (headline)

The 9 V rail regulates ~5–10× looser than the 5 V (~0 %) and 12 V (~0.2 %)
rails: U1 2.00 %, U2 2.11 %, U3 1.67 % against a 2 % design target. U2 fails
outright; U1 sits exactly on the limit. Yield 67 %, directional Cpk 0.13.

The earlier hypothesis — that the ~2 % was inflated by including a near-dropout
Vin point in the sweep — was **tested and disproven**: re-running 9 V line reg
over 12–15 V (full headroom, no marginal point) returned the same ~2 %. The
looseness is real DUT behaviour, not a test artifact. Why the 9 V PDO
specifically regulates loose is **observed but not yet established**.

Limit action: **kept at the 2 % design target.** Relaxing it to make the
population pass would move the goalpost; the miss is recorded as a miss.

### 2. 9 V load regulation is marginal

100 % yield (all under 5 %) but directional Cpk 1.25 (below the 1.33 target),
because U1 droops 2.44 % while U2/U3 droop ~0.11 % — a 20× outlier on one unit.
**To resolve:** confirm whether this is genuine part-to-part variation or
whether U1's 9 V load points were taken over a different load-current range than
U2/U3 (which would make the spread a measurement inconsistency, not the DUT).

### 3. 5 V and 12 V rails are capable

Both pass on every parameter with high directional Cpk; 12 V is the cleanest
rail (Cpk 6–16). **Caveat on 5 V line reg:** the per-unit values were taken over
*different Vin spans* (U1 ~11.5–12 V, U2/U3 13–15 V), so the pooled ~0 % is not a
clean common-span figure. Re-run all three over one span to qualify it.

### 4. LED blink / hiccup under load (observed, not logged)

While wiring a hand-built series load, the module's output LED began blinking
periodically — characteristic of hiccup / over-current protection, or QC
re-negotiation as the rail collapses and re-handshakes. **Not recorded as a
measurement.** Attribution requires the source-vs-DUT check: apply the load
briefly and read the boost output (= DUT Vin). If Vin sags, it is the source
(XL6009 sagging or thermal-folding — it ran hot late in the session). If Vin
holds and the rail collapses, it is the DUT's own current limit (a real spec
worth capturing deliberately). Deferred to Day 3.

## Corrections to the Day-1 record

- **Efficiency blocker is the single DMM** — it cannot capture Vout *and* Iin at
  the same operating point on a module whose operating point isn't repeatable —
  **not** the unfused 10 A range. The unfused jack is a secondary safety caveat.
- Efficiency, the dropout sweep, and ripple/transient/PSRR remain deferred or
  out of scope for the same honest reasons (the first two are opt-in via flags;
  the last needs an oscilloscope and is not simulated).

## Framework gaps surfaced (Day-3 hardening)

- **Vin logged is the commanded value, not the measured one.**
  `run_campaign.py` records the setpoint (`vin_op`) and discards the readback
  that `source.set_voltage()` returns, so a divergence between commanded and
  actual Vin goes unrecorded. Capture the readback into the row — "log what you
  measured, not what you commanded."
- Stale prompt strings in `ManualSource` still say "adjust the buck pot"; the
  source is now the boost. Cosmetic, but it should match reality.

## Day-3 candidates

1. **Add U4 / U5.** Extra units improve the statistics far more than extra Vin
   points; the n = 3 Cpk is the report's weakest claim.
2. Resolve the 9 V load-reg U1 outlier (finding 2).
3. Investigate the 9 V line-reg root cause (finding 1).
4. Run the source-vs-DUT check on the hiccup behaviour (finding 4).
5. Common-span re-run of 5 V line reg (finding 3 caveat).
6. Temperature axis (fridge / warm-air) — pending a confirmed temperature
   measurement tool.
