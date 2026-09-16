# Steam Deck — is the start-of-run dip thermal? (2026-09-12 evening)

Prompted by six cells in `20260912-steamdeck/` that deviated 4–6 % from the
2026-09-11 reference, all clustered in the first minutes of the run. The
question was whether the Deck was throttling.

**Answer: no, and thermals are not involved at all. The cause is background
load — Baloo and Steam — and the effect is far larger than the anomaly that
prompted the investigation.**

## Design

Two identical 0.8B matrices back to back (`--experiment qwen3.5-0.8b-all-servers`,
57 min each) on a machine quiesced for the first time: `kde-baloo` stopped and
suspended, `app-steam@autostart` stopped, LM Studio left up because the
benchmark needs it. One continuous telemetry CSV (`tools/deck-telemetry.sh`,
2 s interval) covering both, timestamped ISO-8601 so rows join to cells.

Pass 1 absorbs any start-of-run transient; pass 2 runs fully warm. Comparing
pass 1 with pass 2 needs no cross-campaign assumption at all — same binary
(`779b9d7d...`), same SDK Vulkan module (`da7402e1...`), same config, same host,
40 minutes apart.

## Result 1 — the transient is gone, and it was never thermal

| | pp Δ% (p2 vs p1) | tg Δ% (p2 vs p1) |
|---|---|---|
| **first 4 cells** | **+0.2 %** | **+0.5 %** |
| last 28 cells | −0.2 % | +0.2 % |
| all 32, median | −0.0 % | +0.4 % |

Pass 1's first cells — the position where the original dip appeared — are
indistinguishable from pass 2's. Telemetry over the two passes:

| phase | edge °C min/mean/max | sclk MHz min/mean/max | fan rpm | load1 |
|---|---|---|---|---|
| pass 1 | 42 / 70.3 / 79 | 200 / 1357 / 1600 | 4521 | 0.53 |
| pass 2 | 55 / 70.3 / 79 | 200 / 1364 / 1600 | 4534 | 0.51 |

Pass 1 began 13 °C colder and produced the same numbers; both reached the
1600 MHz top clock state and neither shows clock suppression while hot (peak
79 °C, 732 samples ≥ 75 °C). A thermal explanation predicts the opposite of
every one of these observations:

- **Direction.** In the loaded campaign, deviations started negative and turned
  *positive* later (Ollama tg −3.3 % at minute 2, +3.5 % at minute 22). Heat
  makes a machine slower over time, not faster.
- **Selectivity.** At minute 3 LM Studio was −6.0 % while llamafile, running at
  the same minute, was at its full +17.4 %. A thermal or clock state is
  machine-wide; it cannot depress one process and spare the next.
- **Shape within a cell.** Ollama's 15 runs went 45.6–46.2 for runs 1–8 then
  stepped to 47.6–49.0 for runs 9–15, the second half matching the reference
  exactly. Heat decays; this recovers.

## Result 2 — Baloo and Steam were costing a great deal

Quiescing did not just remove the transient. Against the 2026-09-11 reference
(which ran loaded, as did every previous Deck campaign), pass 2's prefill is
higher by:

| pp | llamafile | llama-cpp | ollama | lm-studio |
|---|---|---|---|---|
| 1024 | +90 % | +50 % | +47 % | +48 % |
| 2048 | +65 % | +31 % | +39 % | +30 % |
| 4096 | +46 % | +17 % | +19 % | +18 % |
| 8192 | +31 % | +10 % | +11 % | +10 % |

Decode gains are smaller (+2 to +12 %). The effect shrinks as the prompt grows,
which is the signature of a roughly **fixed per-request cost** being removed
rather than a throughput change: at pp1024 a prefill takes ~2 s, at pp8192 ~16 s,
so the same absolute overhead is worth far more of the former.

## What this means for the campaign numbers

Absolute Deck throughput in `20260911-steamdeck/` and in the loaded 0.8B run of
`20260912-steamdeck/` is depressed, by a prompt-size-dependent amount. The
*ratios between runtimes* — what the comparison actually reports — mostly
survive, but not everywhere:

| pp | llamafile ÷ llama-cpp, loaded | quiesced | shift |
|---|---|---|---|
| 1024 | 1.17 | 1.29 | **+10.1 %** |
| 2048 | 1.23 | 1.28 | +4.2 % |
| 4096 | 1.22 | 1.25 | +3.0 % |
| 8192 | 1.17 | 1.19 | +1.5 % |

Ollama and LM Studio shift by ≤ 3 % on prefill at every size except pp2048
(ollama +6.9 %). Decode ratios are stable at pp1024 but move ~10 % at pp8192
for ollama (0.85 → 0.76) and lm-studio (0.87 → 0.79).

So the headline ordering is unchanged, but **small-prompt prefill ratios and
large-prompt decode ratios are materially affected by background load**, and
should not be quoted from a loaded run.

## Consequence for the runbook

Quiescing the Deck (stop `kde-baloo` and `app-steam@autostart`, keep LM Studio)
is now a precondition, not an optimisation, and telemetry should be logged
alongside every Deck run. Restore both services afterwards.

## Files

- `pass1/results/`, `pass2/results/` — 32 cells each.
- `telemetry-20260912-evening.csv` — 3398 rows covering both passes and the 9B.
