# Steam Deck — integer-dot shaders on a fixed engine (2026-09-13)

**Complete: 32/32 cells, no failures.** Started 21:47Z 2026-09-13, finished
01:45Z 2026-09-14. Deck quiesced (Baloo + Steam stopped) and telemetry logged,
matching `../20260912-steamdeck/` conditions.

Answers the question `../20260912-steamdeck/notes.md` left open: the Deck's
prefill spread looked like a shader-toolchain effect, but every previous test
compared *different binaries from different projects*. This one holds the
engine fixed and moves only the shaders.

## The two arms

Both are llama.cpp **b10441, commit 0177dcc73** — the same commit llamafile
42ff11b also vendors — started with identical flags (`--ctx-size 16384`) on the
same GGUFs, interleaved per cell.

| arm | binary | Vulkan shaders | `matmul_*_q8_1` | `mul_mat_vec_*_q8_1` |
|---|---|---|---|---|
| `llama-cpp` | `~/workspace/llama.cpp/build/bin/llama-server`, built in the `devbuntu` distrobox | static, Ubuntu 24.04 glslc 2023.8 | 0 | 0 |
| `llama-cpp-idot` | `~/Downloads/llama-b10441/llama-server`, official release | `libggml-vulkan.so` beside it | 396 | 364 |

The distrobox toolchain does not merely lack the pipelines, it rejects the
extension: `glslc -fshader-stage=compute --target-env=vulkan1.3` on a shader
with `#extension GL_EXT_integer_dot_product : require` returns
`error: extension not supported: GL_EXT_integer_dot_product`. SteamOS's own
`/usr/bin/glslc` (2025.3, headers 1.4.321) compiles it, so a rebuild pointed at
`-DVulkan_GLSLC_EXECUTABLE=/run/host/usr/bin/glslc` would be an alternative to
using this release binary.

## Result

| model | metric | stock | int-dot | Δ | module-swap A/B predicted |
|---|---|---|---|---|---|
| Qwen3.5 0.8B Q8_0 | prefill | 674 | 852 | **+25.9 %** | +22-24 % |
| | decode | 59.9 | 60.3 | **−0.6 %** | +0.1 % |
| Qwen3.5 9B Q4_K_M | prefill | 66.5 | 109.3 | **+63.3 %** | +58-61 % |
| | decode | 11.48 | 13.67 | **+18.2 %** | +18 % |

(medians over 8 cells each; `../20260911-steamdeck-vulkan-sdk/` is the earlier
A/B that swapped only a `ggml-vulkan.so` under one llamafile binary.)

Every number reproduces that earlier A/B, from a completely different binary
pair and a different toolchain. **The decode split is the mechanism showing
through**: +18 % on the 9B and nothing on the 0.8B, because the integer-dot
mat-vec path is only taken for K-quants at k >= 2048 — the 9B's Q4_K_M
qualifies, the 0.8B's Q8_0 does not. A confound would not know that rule.

## Where the arms land against the campaign runtimes

Qwen3.5 9B, tok/s (campaign figures from `../20260912-steamdeck/`, same machine
state — the A/B's stock arm reproduces its campaign twin to **−0.0 % median,
max 0.2 %**, which is what licenses putting them in one table):

| runtime | shaders | prefill @1024 | decode @1024 |
|---|---|---|---|
| **llama-cpp-idot** | int-dot (release) | **109** | **13.7** |
| llamafile | int-dot (SDK) | 109 | 13.7 |
| ollama | int-dot (own module) | 107 | 12.8 |
| llama-cpp | stock glslc 2023.8 | 67 | 11.6 |
| lm-studio | stock (vulkan 2.28.2) | 66 | 11.0 |

**On the 9B, llama.cpp with integer-dot shaders is indistinguishable from
llamafile — −0.1 % prefill, −0.3 % decode.** The entire gap between those two
runtimes on this model was the shader toolchain. That is the cleanest possible
statement of the caveat `../20260912-steamdeck/notes.md` carries: llamafile's
Deck lead was never an engine result.

Two things survive the equalisation and are worth reporting as real:

- **On the 0.8B, llamafile still leads decode** — 65.0 against llama-cpp-idot's
  60.3 (+7.8 %) — while prefill is level (861 vs 852). Shaders move 0.8B decode
  by −0.6 %, so this one is not toolchain. It is model-specific: it appears on
  Q8_0 and vanishes on the 9B's Q4_K_M.
- **Ollama sits just below the other two int-dot builds** (107 vs 109 prefill,
  12.8 vs 13.7 decode). Its module carries 252/196 pipelines against the
  release's 396/364, so it is plausibly a narrower set of specialisations
  rather than an engine difference — untested.

## Consequence

Rebuilding or replacing llama-server takes the Deck from two-against-two to
three-against-one: llamafile, llama.cpp and Ollama at shader parity with
LM Studio alone on the old toolchain (its runtime is a prebuilt download and
cannot follow). That is a **new baseline, not a correction** — the campaign in
`../20260912-steamdeck/` stands as run, and its caveat stands with it. A future
Deck campaign should decide deliberately which toolchain all four runtimes are
held to, and say so.

## Files

- `results/` — 32 cells (`idot-ab-0.8b_*`, `idot-ab-9b_*`) + per-cell server logs.
- `report/` — the runner's tables per experiment.
- `logs/` — runner logs, driver log, `telemetry-20260913-idot.csv` (14,449 rows).
