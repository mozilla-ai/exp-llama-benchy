# Mac Studio, 2026-09-14 — each runtime's own 27B artifact (MLX)

**Complete: 16/16 cells, no failures.** Experiment `qwen3.8-27b-mlx`, Ollama and
LM Studio interleaved per cell, config `experiments.yaml` at commit 90be126.

Everything else in the campaign holds the weights fixed. This one deliberately
does not: on Apple silicon both runtimes ship an MLX build of the 27B, and
LM Studio serves it by default until the GGUF variant is chosen by hand. The
question is "how fast is each runtime at its default", not "which engine is
faster". llama.cpp and llamafile have no MLX path and are absent.

## What ran

| runtime | artifact | size | quantisation |
|---|---|---|---|
| Ollama | `qwen3.8:27b-mlx` (registry, `vnd.ollama.image.tensor`) | 18.2 GB | reports `nvfp4` |
| LM Studio | `mlx-local/qwen3.8-27b-mlx` | 15 GB | 4-bit affine, group_size 64 |
| *(baseline)* | shared `Qwen3.8-27B-Q4_K_M.gguf` | 17.7 GB | Q4_K_M |

Both verified to be genuinely on MLX, from the runtime's own log rather than
assumed — Ollama: `starting mlx runner subprocess`, `MLX engine initialized ...
device=gpu`, 2017 tensors; LM Studio: `Loading model: mlx-local/qwen3.8-27b-mlx`
at 16.08 GB, context 16384.

## Result (tg at 64, vs the shared GGUF at draft 2)

| | prefill 1024 → 8192 | decode 1024 → 8192 |
|---|---|---|
| Ollama | +9.9 % → +5.9 % | **+146 % → +120 %** |
| LM Studio | +10.7 % → +8.6 % | **+23.8 % → +17.5 %** |

**The two decode columns are not measuring the same thing.** Ollama's MLX runner
enables speculative decoding on its own with an adaptive draft depth (median
2.26, acceptance 0.72, 1.67 tokens accepted per iteration over 120 windows in
`logs/ollama-serve.log`); LM Studio's MLX does none. 58.3 ÷ 1.67 ≈ 35 tok/s of
un-drafted MLX decode, against LM Studio's measured 30.1 — the same
neighbourhood, so most of Ollama's apparent lead is drafting.

Two readings survive that:

- **MLX itself is worth roughly 25-45 % on decode.** LM Studio's +24 % is the
  conservative figure and is *understated*: its GGUF column has MTP forced on
  and its MLX column has no drafting, so MLX wins while giving up speculation.
- **Speculation works on MLX where it failed on GGUF.** On this machine GGUF
  draft-4 was slower than not speculating (≈15 vs 23.4 tok/s) and draft-2 barely
  broke even; adaptive MLX drafting roughly doubles decode.

## Setting it up surfaced a hazard

LM Studio's preferred *variant* for the 9B and 27B had silently flipped from
GGUF to MLX, and both variants register under the same API id — so
`lms load qwen/qwen3.8-27b` would have served MLX weights into a shared-GGUF
comparison, invisibly. The 2026-09-12 campaign predates the flip (its server log
shows the `.gguf` files). This `lms` version cannot address a variant at all
(`...@4bit` → "Model not found"), so every LM Studio model is now pinned to an
unambiguous key via `gguf-local/` and `mlx-local/` symlinks. `lms load` also
gained `-y`: without it an unresolvable key drops into an interactive picker and
the cell hangs rather than failing.

## Files

`results/` (16 cells), `report/`, `logs/run-mlx.log`, `logs/ollama-serve.log`
(carries the speculative-decode stats), `lmstudio-server-logs/`.
Figure: `../plots/mlx-ab.png`, points in `../plots/mlx-ab.csv`.
