# Benchmark data

Raw outputs of every exp-benchy campaign, collected from the machines that ran
them so they can be analysed together. One folder per campaign, named
`<YYYYMMDD>-<machine>[-qualifier]`. Inside each: `results/` (one llama-benchy
JSON per (server, model, pp, tg) cell, plus `*.server.log` for the servers the
runner starts itself: llamafile and llama.cpp), `report/` (the runner's
aggregated `.md`/`.json` per experiment), and where available `logs/` (the
runner's console log) and `host-info.txt` (hardware, OS, and the version of
every runtime involved).

Note: the repo's `.gitignore` matches `results/`, `report/` and `*.log` at any
depth, so most of this directory is untracked unless exceptions are added.

## Campaigns

### `20260912-m4max/`, `20260912-l40s/`, `20260912-steamdeck/` — new llamafile build 42ff11b (current)

A repeat of three older `2026091*` matrices with **two** things changed at once,
which is a deliberate exception to the one-variable rule and is why it is
written down here:

1. **llamafile `c73be59` → `42ff11b`** (still reports v0.10.6; sha256
   `779b9d7d3233c223...`). `42ff11b` is the merged CUDA-graphs build-script fix
   (#1051) from `20260911-l40s-cudagraphs/`, on top of `6719ace` (#1050, ggml
   objects compiled with `-DNDEBUG`).
2. **Ollama → 0.34.0 on all three machines.** The 2026-09-10/11 campaigns ran
   three different Ollama versions under one name (pod 0.33.1, Deck 0.33.0, Mac
   0.32.15); this aligns them, as the RUNBOOK asks. The consequence is that
   Ollama is **not** a replication control this time — only llama.cpp and LM
   Studio are. `compare_campaigns.py` against `20260910-*` should show those two
   within a few percent; an Ollama move is expected and not evidence about
   llamafile.

The `-lms` Ollama tags were recreated on 2026-09-12 under 0.34.0 and re-verified
(blob sha256 == GGUF sha256). This also fixed a drift: `qwen3.8:27b-lms-mtp`
had been carrying `draft_num_predict 4` on both the Mac and the pod, not the 2
the campaign rule requires, and `qwen3.8:27b-lms-mtp4` did not exist on either.
All five experiments ran on the Mac and the pod (including the optional
`qwen3.8-27b-mtp4`).

**Results.** On the L40S the CUDA-graphs build lifts llamafile decode by a
median of +6.5 % (max +19.4 %) while llama.cpp (+0.1 %), LM Studio (-0.7 %) and
Ollama (+0.0 %) reproduce the previous campaign — the fix, isolated. On the Mac
llamafile is unchanged (+0.0 % pp, -0.1 % tg), which is the control that
confirms the build change is CUDA-only. The MTP series moved by design (draft 2
now, 4 then): draft 2 beats draft 4 by +45..+69 % on Metal and loses by
-16..+4 % on the L40S, reproducing the platform dependence that motivated the
rule; the new `qwen3.8-27b-mtp4` experiment matches the 2026-09-10 draft-4 cells
within MTP's acceptance-rate noise.

**The Deck is a special case in this campaign.** Its 0.8B matrix was run twice:
once in the morning with the machine in its usual state (Baloo and Steam
running, as in every previous Deck campaign) and once in the evening with the
machine quiesced. The quiesced run is the campaign's 0.8B — it matches the
conditions the 9B was measured under — and the loaded run is preserved under
`20260912-steamdeck/loaded-0.8b/` as the background-load comparison. The reason
is in `20260912-steamdeck-warmab/README.md`: stopping Baloo and Steam raises
0.8B prefill by +10 % (pp8192) to +90 % (pp1024) depending on runtime, and
removes a start-of-run transient that had depressed the morning run's first
cells by 4-6 %. Deck campaigns before 2026-09-12 all ran loaded.

**How the GPU kernels were pinned.** `42ff11b` as built here is a *thin* binary:
it bundles no `ggml-cuda.so` / `ggml-vulkan.so` at all, and it reports the same
version string as `c73be59`, so both builds resolve to the same
`~/.llamafile/v/0.10.6/`. Left alone the new binary would have silently run the
old build's kernels, and on the pod a stray pre-graphs `~/llamafiles/ggml-cuda.so`
would have outranked even that (the loader prefers `<exe_dir>/`). Each machine
therefore has `~/llamafile-42ff11b/` holding the binary plus exactly the module
it must load:

| machine | module next to the binary | evidence |
|---|---|---|
| Mac Studio | none — Metal is compiled from the bundled source | n/a |
| L40S pod | `ggml-cuda.so`, 109,651,584 B, `CUDA graph` strings = 4 | the `graphs` module built for `20260911-l40s-cudagraphs/` |
| Steam Deck | `ggml-vulkan.so`, 56,734,160 B, `matmul_q4_k_q8_1` = 11 | the LunarG SDK 1.4.357.1 module from `~/vkab/sdk/` |

Module loading was verified from `/proc/<pid>/maps` of the live server, not
inferred. The new build's server defaults were also checked against
llama-server b10441 on the same GGUF and are identical (`n_batch` 2048,
`n_ubatch` 512, `n_parallel` 4, `kv_unified` true, `flash_attn` auto), so
"new build" hides no second variable there.

**Caveat that must travel with the Deck numbers.** Giving llamafile the SDK
Vulkan module breaks the shader-toolchain parity the 2026-09-11 campaign was
built on: llama-server (stock Ubuntu glslc 2023.8) and LM Studio's vulkan
2.28.2 both run `int dot: 0`, while llamafile (SDK module) and Ollama (its own
bundled module, which had them all along) run `int dot: 1`. That two-against-two
split alone is worth roughly **+22-24 % prefill on the 0.8B** and +58-61 % on the 9B.
This is the reason why we run `20260912-steamdeck-idot/` (see below) and enable
`int dot` for llama.cpp too.

### `20260912-steamdeck-idot/` — the set the published Deck figure is drawn from

**Composed, not a single run.** The 2026-09-12 campaign's llamafile / LM Studio /
Ollama cells plus the 2026-09-13 A/B's integer-dot arm standing in for
llama.cpp, which became the Deck default on 2026-09-14. Licensed by the A/B's
stock arm reproducing its campaign twin to −0.0 % median. `tools/make_figures.sh`
points the Deck figure here. With three of four runtimes now on integer-dot
shaders, LM Studio is the only one left without them and the 1.6x prefill spread
collapses onto it alone. See its README before citing any number from it.

### `20260914-m4max-mlx/` — Mac, each runtime on its own 27B artifact (side experiment)

The one experiment that deliberately breaks the shared-weights rule: Ollama and
LM Studio on their own MLX builds of the 27B instead of the common GGUF, since
that is what each serves by default on Apple silicon. Prefill +6-11 % for both;
decode +146 % (Ollama) against +24 % (LM Studio) — a gap that is mostly
speculative decoding, which Ollama's MLX runner enables by itself and
LM Studio's does not. Read its README before quoting either decode number.

### `20260913-steamdeck-idot-ab/` — Deck, integer-dot shaders on a fixed engine (side experiment)

Settles what `20260912-steamdeck/` could only assert. Two builds of the **same**
llama.cpp commit (b10441, 0177dcc73) — ours from the distrobox (glslc 2023.8,
which rejects `GL_EXT_integer_dot_product` outright) and the official release
(396 `matmul_*_q8_1` pipelines) — interleaved per cell with identical flags and
weights. Prefill +25.9 % (0.8B) and +63.3 % (9B); decode +18.2 % on the 9B and
−0.6 % on the 0.8B, the split that the int-dot mat-vec path's k >= 2048 K-quant
rule predicts. With shaders equalised, llama.cpp matches llamafile on the 9B to
−0.1 % prefill / −0.3 % decode: the Deck gap was never the engine. llamafile's
+7.8 % decode lead on the 0.8B does survive and is real.

### `20260912-steamdeck-warmab/` — Deck, background load vs quiesced (side experiment)

Two identical 0.8B matrices back to back on a quiesced Deck, 40 minutes apart,
to test whether the morning campaign's start-of-run dip was thermal. It was not:
pass 1 started 13 C colder than pass 2 (42 C vs 55 C) and their first four cells
— the position where the dip appeared — agree to +0.2 % prefill and +0.5 %
decode, with identical thermal profiles and both reaching the 1600 MHz top clock
state. The dip was contention from Baloo and Steam, and quiescing turned out to
matter far more than the anomaly that prompted the investigation. Full tables,
the telemetry summary and the effect on cross-runtime ratios are in its README.
`pass2/` is also the campaign's 0.8B (see above).
