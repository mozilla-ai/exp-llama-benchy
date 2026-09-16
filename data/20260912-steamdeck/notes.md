# Steam Deck, 2026-09-12 — llamafile 42ff11b + SDK Vulkan module, quiesced

**Complete: 0.8B 32/32 and 9B 32/32, no failures, none quarantined.** Config
`experiments.steamdeck.yaml` at commit `050146d`.

## Read this first: two variables moved, and one of them is the machine

Against `20260911-steamdeck/` this campaign changes three things at once. Two
are deliberate, the third was discovered during the run:

1. llamafile `c73be59` → `42ff11b`. The build fixes CUDA/HIP graphs, which does
   nothing on Vulkan — expected to be a no-op here, and is.
2. llamafile's Vulkan module: shipped (stock glslc, `int dot: 0`) → LunarG SDK
   1.4.357.1 (`int dot: 1`). This puts **two runtimes on each side** of the
   shader question, which is what makes this campaign's Deck data more useful
   than the last one's — see below.
3. **The machine was quiesced** (Baloo and Steam stopped). Every previous Deck
   campaign ran with them active. This is worth more than it sounds and is
   documented in `../20260912-steamdeck-warmab/README.md`.

### The 0.8B here is the evening quiesced run, not the morning one

The 0.8B matrix was run twice on 2026-09-12. The morning run (loaded, like all
previous campaigns) is preserved in `loaded-0.8b/`; the campaign's 0.8B is the
evening quiesced run, so that it matches the conditions the 9B was measured
under. Its replication control is the pass immediately before it: two
independent quiesced matrices 40 minutes apart agreeing to a median of −0.0 %
prefill and +0.4 % decode.

`logs/ollama-serve.log` was trimmed to the 9B window for the same reason — the
0.8B's server-side rows in `server-timings.csv` come from
`logs/diag-pass2-ollama.log`. The untrimmed original is in
`loaded-0.8b/ollama-serve.loaded-0.8b-and-9b.log`.

## Decomposing the change vs 20260911

Median Δ% per server. The three stock-shader runtimes move only because of
quiescing; llamafile carries quiescing **plus** the SDK shaders:

| | 0.8B pp | 0.8B tg | 9B pp | 9B tg | contains |
|---|---|---|---|---|---|
| llama-cpp | +23.9 % | +6.5 % | +5.8 % | +1.0 % | quiescing only |
| lm-studio | +23.5 % | +0.5 % | +5.0 % | +2.1 % | quiescing only |
| ollama | +27.7 % | +0.7 % | +9.1 % | +2.1 % | quiescing only |
| **llamafile** | **+55.5 %** | **+11.0 %** | **+72.9 %** | **+19.4 %** | quiescing + SDK shaders |

### The prefill split follows the shaders, not the engine

All four runtimes are llama.cpp-derived, so the engine is near enough constant.
What differs is which toolchain compiled their Vulkan shaders — and Ollama
ships its own module (`~/.local/lib/ollama/vulkan/libggml-vulkan.so`, 252
`matmul_*_q8_1` + 196 `mul_mat_vec_*_q8_1`) that has had the integer-dot fast
path all along. 9B prefill, tok/s:

| runtime | shaders | 1024 | 2048 | 4096 | 8192 |
|---|---|---|---|---|---|
| llamafile | int-dot (SDK) | 109 | 111 | 109 | 102 |
| ollama | int-dot (own module) | 107 | 109 | 107 | 101 |
| llama-cpp | stock glslc 2023.8 | 67 | 68 | 67 | 64 |
| lm-studio | stock (vulkan 2.28.2) | 66 | 67 | 66 | 64 |

**1.62x between the groups, ~2 % within them.** In `20260911-steamdeck/` Ollama
was the only int-dot runtime, so its prefill lead was confounded with
everything else that makes Ollama different; here llamafile crossed the line
and moved with the shaders rather than with its lineage. Parameters do not
explain it either: Ollama runs the 9B with `-b 512 -ub 512 -np 1` against
llama.cpp's `-b 2048 -ub 512 -np 4`, so the **micro-batch — what actually sets
the prefill chunk — is 512 on both**.

Decode reverses the order, which is the control that rules the engine out from
the other side: on the 0.8B llama.cpp does 59.6 against Ollama's 48.1 (+24 %).
There the split is host-side per-token overhead — the two lean servers
(llamafile 65.0, llama-cpp 59.6) above the two wrapper runtimes (lm-studio
48.5, ollama 48.1) — and shaders contribute nothing, exactly as the A/B
predicted (+0.1 % decode on the 0.8B versus +18 % on the 9B, because the
int-dot mat-vec path only engages for K-quants at k >= 2048).

To separate machine state from shaders, take llamafile ÷ llama-cpp *within*
each campaign, which cancels the machine state entirely:

| | 0.8B pp | 0.8B tg | 9B pp | 9B tg |
|---|---|---|---|---|
| 20260911 (loaded, both stock shaders) | 1.00x | 1.02x | 1.00x | 1.00x |
| 20260912 (quiesced, llamafile on SDK) | 1.27x | 1.06x | **1.63x** | **1.18x** |

Two things follow, and they matter more than the headline numbers:

- **At shader parity, llamafile and llama-server prefill identically on this
  GPU** — 1.00x on both models in the 2026-09-11 campaign. The Deck prefill gap
  is a toolchain artifact end to end, not an engine difference.
- **The SDK module's effect reproduces the A/B exactly.** `20260911-steamdeck-vulkan-sdk/`
  measured +58-61 % prefill and +18 % decode on the 9B and +22-24 % prefill on
  the 0.8B by swapping only the module under one binary. Here the ratio shifts
  +63 % / +18 % (9B) and +27 % (0.8B) — independent confirmation from a full
  matrix rather than a targeted A/B.

**So: do not report the Deck's llamafile prefill lead as an engine result.** It
is integer-dot shaders that llama-server and LM Studio were not built with.
Restoring parity means rebuilding llama-server with an SDK glslc.

## Thermals

`telemetry-20260912-evening.csv` (15,688 rows at 2 s, ISO-8601 UTC, joins to
cells by the result JSON `timestamp`) covers both 0.8B passes and the whole 9B.
Nothing throttled: the GPU held its 1600 MHz top state, edge temp peaked at
79 C, and two passes starting 13 C apart produced identical numbers. A Deck run
that looks slow should be checked against this file before heat is blamed —
suppressed clocks are throttling, a dip with clocks still at the top state is
contention.

## Files

- `results/` — 64 cells (0.8B = quiesced evening pass, 9B) + per-cell server logs.
- `report/` — regenerated from `results/` after the 0.8B swap. **The reports
  run.py wrote at the end of the 9B were stale**: it had read `results/` into
  memory when the 9B started, hours before the 0.8B files were replaced, so it
  reported the demoted loaded numbers. Regenerated with `run.py --report-only`.
- `loaded-0.8b/` — the morning loaded run, its report and untrimmed Ollama log.
- `server-timings.csv` — 960 per-request rows.
- `host-info.txt` — every llamafile module with its `int-dot` count; the one in
  use is `llamafile-42ff11b/ggml-vulkan.so` (`da7402e1...`, int-dot 11) against
  `llama-server int-dot: 0`.
- `telemetry-20260912-evening.csv`.
