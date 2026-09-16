# Steam Deck, integer-dot default — the set the published figure is drawn from

**This folder is composed, not a single run.** It exists because the Deck's
llama.cpp default changed on 2026-09-14 (to the official b10441 release build,
whose Vulkan shaders have the integer-dot fast path) and the figure had to
reflect that without re-running an 8-hour campaign.

| runtime | cells from | run |
|---|---|---|
| llamafile, LM Studio, Ollama | `../20260912-steamdeck/results/` | campaign, 2026-09-12 |
| **llama.cpp** | `../20260913-steamdeck-idot-ab/results/` (the `llama-cpp-idot` arm, renamed into the campaign's experiment ids) | A/B, 2026-09-13 |

16 cells per runtime (2 models x 4 prompt lengths x 2 tg), 64 total.

## Why the two runs can sit in one figure

Both ran on a quiesced Deck (Baloo and Steam stopped) with telemetry logged, and
the A/B carried its own control: its **stock arm reproduced the campaign's
llama.cpp to −0.0 % median, max 0.2 %**. That is the check that licenses the
composition — the machine was in the same state on both nights.

What it does *not* preserve is the campaign's interleaving discipline. In the
campaign all four runtimes rotate within each cell group; here llama.cpp's cells
come from a run where it was interleaved only against the stock build. Given the
±0.2 % agreement that is a small price, but it is the reason this is a separate
folder with a README rather than an edit to `../20260912-steamdeck/`, which
stands exactly as it was run.

**A single clean campaign on the new default would supersede this folder.** Until
then, cite it as composed.

## What the figure now shows

With three of four runtimes on integer-dot shaders, the Deck picture inverts:

- **llama.cpp and llamafile are indistinguishable** on the 9B (109 vs 109
  prefill, 13.7 vs 13.7 decode) and on 0.8B prefill (852 vs 861). The gap the
  earlier figures showed was the shader toolchain, and it is gone.
- **LM Studio is now the only runtime without the fast path** — its runtime is a
  prebuilt download at `int dot: 0` and cannot follow. It sits alone at 66 tok/s
  on 9B prefill against the others' 107-109, a 1.6x deficit that is a build
  property of its shipped runtime, not an engine result. Say so when reporting
  it, in the same breath as the number.
- **llamafile keeps a real decode lead on the 0.8B** — 65.0 against llama.cpp's
  59.4, +9 %. Shaders move 0.8B decode by −0.6 %, so this one survives
  equalisation and is genuine. It does not appear on the 9B.
- **Ollama sits just below the other two int-dot builds** (756 vs ~855 on 0.8B
  prefill, 107 vs 109 on the 9B). Its module carries 252/196 pipelines against
  the release's 396/364 — plausibly a narrower specialisation set; untested.

## Provenance of the llama.cpp cells

Renamed, not modified: `idot-ab-<model>_..-llamacpp-idot_pp*_tg*.json` ->
`qwen3.5-<model>-all-servers_..-llamacpp_pp*_tg*.json`, so `plot_campaign.py`
reads them as the campaign's llama.cpp series. Contents are byte-identical to
the A/B originals; `host-info.txt` is the campaign's and therefore describes the
*old* llama-server — the binary actually behind the llama.cpp series here is
`/home/deck/Downloads/llama-b10441/llama-server` (396 `matmul_*_q8_1`).
