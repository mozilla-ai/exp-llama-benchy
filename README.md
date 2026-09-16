# exp-benchy

Benchmark runner for [llama-benchy](https://github.com/ggml-org/llama-benchy) across multiple inference servers (llamafile, llama.cpp, ollama, lm-studio) and parameter sweeps.

## Quick Start

```bash
# 1. Edit experiments.yaml to configure your servers, models, and parameter sweeps
# 2. Run all servers
uv run run.py

# 3. Check the report
cat report/qwen3.5-0.8b-all-servers.md
```

## Re-running a campaign

`RUNBOOK.md` is the step-by-step procedure for a full re-run on all three
machines (pre-checks, backup, launch commands that survive an ssh logout,
monitoring, restoring services, collecting the data with
`tools/collect_campaign.sh`, and checking reproducibility with
`tools/compare_campaigns.py`), plus every pitfall met so far.

## Architecture

```
exp-benchy/
├── experiments.yaml    # experiment configuration
├── run.py              # runner script
├── pyproject.toml      # uv project (pyyaml only)
├── results/            # per-run JSON output from llama-benchy
│   └── {exp}_{label}_pp{pp}_tg{tg}.json
└── report/             # aggregated reports (auto-generated)
    ├── {exp_id}.json   # machine-readable
    └── {exp_id}.md     # human-readable markdown tables
```

## Configuration

`experiments.yaml` defines:

- **servers** — inference server configs (start/stop commands, ports, ready checks)
- **models** — logical model names with per-server overrides (e.g., ollama registry IDs)
- **sweeps** — parameter matrices (pp, tg) referenced by experiments
- **experiments** — cross-products of servers × models × pp × tg

Each run is a `(server, model, pp, tg)` tuple. The server is fully restarted between runs for cache isolation.

### Model Resolution Cascade

Per `(model, server)` pair:
- `served_model_name` → explicit in `refs[server].served_model_name`, or defaults to `model.name`
- `model` → explicit in `refs[server].model`, or rendered from `server.model_template`

This means llamafile and llama-cpp often need no per-server overrides (both use the same `.gguf` path), while ollama and lm-studio only need their registry IDs.

## Usage

### Run all experiments

```bash
uv run run.py
```

### Run a single server

```bash
uv run run.py --server llamafile
```

### Run with resume (skip cached results)

```bash
uv run run.py --server ollama --resume
```

This loads all cached results from disk, skips any runs that already have result files, and runs only what's missing. **Reports are always regenerated from the full merged cache**, so incremental runs produce complete reports.

### Regenerate reports without re-running

```bash
uv run run.py --report-only
```

Useful when you've manually edited or deleted report files but want to regenerate them from cached per-run results.

### Dry run (preview expanded runs)

```bash
uv run run.py --dry-run
uv run run.py --dry-run -v   # show full commands
```

### Other options

```
--config FILE          Path to experiments YAML (default: experiments.yaml)
--experiment ID        Run only this experiment id
--server SERVER        Run only this server (e.g. llamafile)
--resume               Skip runs that already have a result file
--retries N            Retry failed runs N times (default: 0)
--report FORMAT        Report format: json, md, both (default: both)
--report-only          Skip server/benchmark runs; regenerate reports from cached results
-v, --verbose          Verbose logging
```

## Incremental Workflow

The typical workflow for running multiple servers one at a time:

```bash
# Run each server individually (reports merge across invocations)
uv run run.py --server llamafile
uv run run.py --server llama-cpp
uv run run.py --server ollama
uv run run.py --server lm-studio

# Or run all at once
uv run run.py

# After any run, the report always contains all cached results
cat report/qwen3.5-0.8b-all-servers.md
```

Reports are regenerated after **every** invocation using all cached results on disk, including servers not part of the current run. This means:
- Running `--server llamafile` produces a full report with all previously cached servers
- You can run servers in any order, any number of times
- `--report-only` regenerates reports without starting any servers

## Result Files

Each benchmark run produces a JSON file in `results/`:
```
qwen3.5-0.8b-all-servers_Qwen3.5-0.8B-Q8_0-llamafile_pp2048_tg32.json
```

These are the raw llama-benchy outputs. The runner aggregates them into:
- `report/{exp_id}.json` — structured summary with extracted metrics
- `report/{exp_id}.md` — human-readable markdown tables (per metric, per pp/tg combination)

### Metric extraction

One fixed rule, applied to every cell and metric (`MIN_RUNS`, `WARMUP_RUNS`,
`TRIM_EACH_SIDE` in `run.py`); `benchy_cmd` must ask for `--runs 15` or more,
and the runner refuses to start otherwise:

- a cell needs at least 15 values; fewer is no result (a result file with fewer
  runs is not reported, and at run time the cell counts as failed)
- `values[0]` is the warm-up run and is dropped
- of the remaining 14, the 2 slowest and the 2 fastest are dropped (symmetric
  trim: interference below and prompt-cache hits above are treated alike)
- **trimmed mean** and std of the 10 that remain; **median** and sd of all 14,
  so the ± in the tables is the raw spread and the median is an untuned check
- the discarded runs are listed in the report ("Trimmed runs") when they sit
  more than 5% from the trimmed mean -- that is the interference audit trail
- extracts `pp_throughput`, `tg_throughput`, and `ttfr` from the `concurrency=1` benchmark cell
- groups results by `(pp, tg)` for the markdown tables, with one row per server

### Server-side timings

llama-benchy measures from the client (SSE chunk arrival times). Every server
here embeds llama.cpp's server, which logs one `print_timing` block per request
measured inside the engine; `tools/server_timings.py` attributes those lines to
cells and aggregates them with the same rule, next to the client-side figures:

```bash
tools/server_timings.py --results results \
    --lmstudio-log ~/.lmstudio/server-logs/2026-09/2026-09-10.1.log \
    --ollama-log logs/ollama-serve.log            # Mac; on Linux: a journalctl -u ollama dump
    --csv results/server-timings.csv
```

Sources: llamafile/llama.cpp from the `*.server.log` the runner captures;
LM Studio from its server log; Ollama from the daemon log the Mac config
appends to (`logs/ollama-serve.log`) or the systemd journal on Linux. Cells are
matched by model, request count, tg and prompt-token range, never by wall clock.

Use the server-side number as the decode speed whenever the two disagree: LM
Studio on macOS releases its first tokens late and in bursts, which inflates the
client-side tg by ~15% at tg=32 and ~7% at tg=64 while its engine runs at
exactly llama.cpp's speed (see `data/20260912-m4max/lmstudio-client-vs-server.md`).
Client-side stays the right number for time-to-first-token.

### Plots

`tools/plot_campaign.py` draws one figure per campaign in the blog's layout:
title, shared legend, one column per experiment, prompt processing on top and
token generation below, prompt length on the x-axis, ±1 SD error bars. It reads
the raw result files and applies the same aggregation rule as the report, or
the server-side timings with `--source server`. Dependencies are declared
inline, so `uv run` fetches matplotlib on demand (see `tools/make_figures.sh`).

The blog figures are client-side throughout -- what a user of the endpoint
measures, per-request overhead included -- with one exception, applied only
where the client-side figure is demonstrably wrong: LM Studio's token
generation on macOS is taken from the engine's own timings
(`--tg-source-for lm-studio=server`, see above). The caption and the
file name record the exception. `--csv` writes every plotted point so numbers
can be quoted from the figure's own data; `data/comparison.md` is written from
those files. Output goes to `--out` or `<campaign>/plots/`. Series colours and
markers are fixed per server (llama.cpp, llamafile, LM Studio, Ollama) on
every figure; the palette passes colour-vision-deficiency and contrast checks,
and the markers carry the identity on their own in print.

### Run order

Cells run model → pp → tg → **server**, i.e. for each cell all servers run back
to back. The servers being compared therefore see the same machine state
minutes apart instead of hours apart (thermals, background load). The server is
restarted for every cell anyway, so this costs nothing.

## Host configs

Two configs are checked in; they differ only in paths, the llamafile binary and
how Ollama is (re)started:

- `experiments.yaml` — Mac Studio (M4 Max). Ollama is started by the runner
  with `OLLAMA_CONTEXT_LENGTH=16384`.
- `experiments.linux.yaml` — Linux pod (L40S). Ollama is a systemd service;
  the runner does `sudo -n systemctl restart/stop ollama`, and the context is
  pinned by `/etc/systemd/system/ollama.service.d/benchy.conf`
  (`Environment=OLLAMA_CONTEXT_LENGTH=16384`). The last Ollama cell leaves the
  service stopped: `sudo systemctl start ollama` afterwards.

- `experiments.steamdeck.yaml` — Steam Deck (Van Gogh APU, Vulkan/RADV). 0.8B
  and 9B only (no 27B in 16 GB, hence no MTP series). Ollama is the plain
  binary started by the runner with `OLLAMA_VULKAN=1 OLLAMA_IGPU_ENABLE=1`
  (without both it silently runs on the CPU) and `OLLAMA_CONTEXT_LENGTH=16384`.
  LM Studio is an AppImage: the runner launches it inside the desktop session
  with `systemd-run --user` when `lms` cannot reach it; its runtime is pinned
  with `lms runtime select llama.cpp-linux-x86_64-vulkan-avx2@2.28.2`.
  llama-server is built with `-DGGML_VULKAN=ON` inside the `devbuntu` distrobox
  and run on the host; llamafile is the same binary as the other machines with
  `--gpu vulkan`.

```bash
uv run run.py --config experiments.linux.yaml --experiment qwen3.8-27b-mtp
uv run run.py --config experiments.steamdeck.yaml
```

## One GGUF per model

Every runtime serves the same weights: the lmstudio-community GGUFs that LM
Studio already has on disk. llama.cpp and llamafile load them by path. Ollama
serves them through tags created from the very same files:

```bash
ollama/create-lms-models.sh [LMS_ROOT]    # default ~/.lmstudio/models/lmstudio-community
```

`ollama/Modelfile.*` carry the library tags' TEMPLATE/RENDERER/PARSER/PARAMETER
lines (minus the mmproj); `qwen3.8:27b-lms-mtp` additionally sets
`draft_num_predict 2` and `qwen3.8:27b-lms-mtp4` the library default of 4, which
make Ollama enable MTP speculative decoding with that draft length. Ollama names
blobs by sha256, so the script verifies blob == source file.

Speculative decoding is a separate experiment (`qwen3.8-27b-mtp`) with **draft
length 2 on every runtime** -- the only value all four can share, since LM
Studio drafts 2 and offers no setting; the plain 27B experiment excludes LM
Studio, which enables MTP whenever the GGUF carries the head and offers no
switch. The optional `qwen3.8-27b-mtp4` experiment runs the three configurable
runtimes at Ollama's library default of 4 (the setting of the 2026-09-10
campaigns), which loses to no-MTP on Apple Silicon and wins on CUDA -- the
draft length is platform-dependent and is therefore never chosen per platform.

## Dependencies

- `pyyaml` — parse experiments.yaml
- `llama-benchy` — invoked via `uvx` (not a project dependency)
- `uv` — Python package manager and runner
