# README additions — Day 3 (temperature axis)

Paste these into README.md where indicated.

---

## 1. Update the PVT table (replace the Temperature row)

In the "How PVT is made real on a hobby bench" table, the **T** row becomes:

| **T** emperature | operating range | Peltier (TEC) thermal source on a dedicated 12 V SMPS; module temperature read by an on-board **thermistor** (separate from the DMM). Endpoints ~5 °C / ~50 °C characterised on U2; 25 °C on U1–U3 |

---

## 2. Add to the "Data honesty" block or scope notes

> **Source input-power ceiling (scope limit).** The input chain is a 5 V phone
> charger → XL6009 boost. Its input-power budget (~10 W) is below what the
> heavier loads demand, so above a modest load current the rail browns out from
> the **input side**, not the DUT. Load regulation is therefore characterised at
> 25 °C (where the source had headroom); load-reg over temperature is out of
> scope on this bench. Stated as a limitation, like efficiency and ripple — not
> simulated or worked around.

---

## 3. Optional — one line in the results/headline summary

> Temperature axis (U2, 5/25/50 °C): no-load Vout shows no resolvable tempco
> (≤ 20 mV, within DMM resolution); 5 V and 12 V line regulation are flat and
> capable across temperature. The 9 V line-reg miss seen at 25 °C did not
> reproduce at 5/50 °C — non-monotonic and unresolved at a single unit.

---

## 4. Interview note (optional, for the "Notes for the interview" section)

> **"Why only one unit over temperature?"** I characterised the full temperature
> range on U2 (the 9 V line-reg failer) and scoped to one unit given time and a
> three-module supply. The rails cluster tightly at 25 °C, so I expected U1/U3 to
> track U2 — but I did not measure them over temperature, so part-to-part
> temperature spread is stated as uncharacterised rather than claimed.

> **"Your report shows load-reg failures?"** Two of those (5 V, 12 V over
> temperature) are a source input-power limit — the 5 V→XL6009 boost browns out
> under load — not DUT behaviour. The DUT's load regulation is capable at 25 °C
> (≤ 0.4 %). I left the foldback rows in as evidence and documented the source
> limit rather than deleting them; the honest scope is load-reg at 25 °C.
