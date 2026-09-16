# Runbook: re-running the full benchmark on all three machines

Everything here is repeatable without this repository's history: the configs
are `experiments.yaml` (Mac Studio), `experiments.linux.yaml` (L40S pod) and
`experiments.steamdeck.yaml` (Steam Deck); the rule is in `run.py`; the tools
are in `tools/`. A campaign = one invocation of `run.py` per machine.

Durations with `--runs 15`: Mac ≈ 5.5 h, pod ≈ 1.5 h, Deck ≈ 11 h; the optional
`qwen3.8-27b-mtp4` experiment adds ≈ 2 h on the Mac and ≈ 30 min on the pod
(comment it out in the config to skip it -- `run.py --experiment` selects one
experiment, it cannot exclude one). Start the Deck first.

## Rules that must not drift between campaigns

- **Speculative decoding (27B)**: draft length **2** for every runtime in
  `qwen3.8-27b-mtp` -- `--spec-draft-n-max 2` for llama.cpp and llamafile,
  `draft_num_predict 2` in the `qwen3.8:27b-lms-mtp` tag, and LM Studio's fixed
  2. It is the only value all four can share. The Ollama library default (4) is
  kept only in the optional `qwen3.8-27b-mtp4` experiment (three runtimes,
  `qwen3.8:27b-lms-mtp4` tag), which reproduces the 2026-09-10 draft-4 cells and
  documents the platform dependence (on the M4 Max n_max 1/2/3/4 → 26.2 / 22.8 /
  17.4 / ~14 tok/s against 23.4 without MTP; on the L40S 56 / 65 / 74 / 73 against
  ~37). Never pick the draft length per platform.
- **Everything else stays at each runtime's defaults** except what is
  equalised on purpose: one GGUF per model, context 16384, full offload. In
  particular llama.cpp and llamafile keep `-b 2048 -ub 512 -np 4` and the host
  prompt cache: Ollama's `-b 1024 -ub 1024 -np 1` is its own per-model heuristic
  (512 for the 9B on the Deck), not a setting to copy, and none of the measured
  prefill gaps were micro-batch (see `data/comparison.md`).
- **Change one thing per campaign.** A campaign that only swaps the llamafile
  binary keeps llama.cpp, LM Studio and Ollama as replication controls:
  `tools/compare_campaigns.py` should show them within a few percent of the
  previous campaign while llamafile moves. If a second thing must change
  (a runtime version, a rule), write it down in `data/README.md` before the run.
- **One Ollama version on all three machines.** On 2026-09-10/11 they differed
  (pod 0.33.1 with engine `0.3.0-dev d222767c7`, Deck 0.33.0 with the older
  `0.1.2-dev 9d77fa172`, Mac 0.32.15): three engines under one name. Update all
  three to the same release before the campaign and record it; recreate the
  `-lms` tags afterwards if Ollama's store format changed
  (`ollama/create-lms-models.sh`).

## 0. Before starting anything

On the laptop:

```bash
cd ~/workspace/exp-benchy && git pull --ff-only
```

On each machine, pull and make sure nothing else is using the GPU:

| machine | ssh | repo | pull + idle check |
|---|---|---|---|
| Mac Studio | `ssh studio` | `/Users/mala/workspace/exp-benchy` | `git pull --ff-only; pgrep -fl "llama-server\|llamafile\|llama-benchy"` (expect nothing) |
| L40S pod | `ssh 89.169.109.142` | `/home/mala/workspace/exp-benchy` | `git pull --ff-only; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv` (expect 0 %, 0 MiB) |
| Steam Deck | `ssh steamdeck` (LAN only) | `/home/deck/workspace/exp-benchy` | `git pull --ff-only; pgrep -fl "llama-server\|llamafile"; systemctl --user list-units --type=service --state=running` (only `lmstudio-benchy` expected); plugged in, desktop mode; **quiesced -- see below** |

The pod may be powered off between campaigns; the Deck is only reachable from
the local network. Remember the non-login ssh shells: on the Mac, Homebrew
tools need `PATH=/opt/homebrew/bin:/usr/local/bin:$HOME/.lmstudio/bin:$HOME/.local/bin:$PATH`;
on the Deck `PATH=$HOME/.local/bin:$HOME/.lmstudio/bin:$PATH`.

### Deck only: quiesce it first (mandatory since 2026-09-12)

Baloo and Steam are not background noise on this machine, they are a first-order
term. Stopping them raised 0.8B prefill by **+50 % at pp1024 and +10 % at pp8192
for llama-server**, and by **+90 % / +31 % for llamafile** -- the gain shrinks with
prompt size, which is the signature of a fixed per-request cost being removed.
Leaving them running also produces a start-of-run transient that depresses the
first few cells by 4-6 % and decays over ~15 minutes, which is what
`20260912-steamdeck/`'s first pass showed. Every Deck campaign before 2026-09-12
ran loaded; their absolute numbers are depressed and their small-prompt prefill
and large-prompt decode ratios are shifted (see
`data/20260912-steamdeck-warmab/README.md`).

```bash
systemctl --user stop kde-baloo.service; balooctl6 suspend || balooctl suspend
systemctl --user stop app-steam@autostart.service
ps -eo pcpu,comm --sort=-pcpu | head -6        # nothing above ~1 % except the benchmark
systemctl --user is-active lmstudio-benchy      # must stay active -- the benchmark needs it
```

Log the machine's state alongside every Deck run, so a suspicious cell is checked
against what the hardware was doing rather than guessed at:

```bash
systemd-run --user --unit=deck-telemetry --collect --working-directory=$PWD \
  --setenv=PATH=/usr/local/bin:/usr/bin:/bin \
  bash -c "tools/deck-telemetry.sh 2 > logs/telemetry-$(date +%Y%m%d).csv"
```

It writes GPU edge temp, CPU temp, battery temp, fan rpm, GPU busy %, sclk state,
peak CPU MHz and load1 every 2 s, timestamped ISO-8601 UTC to match the
`timestamp` field in llama-benchy's result JSON, so rows join to cells directly.
**Restore both services when the campaign ends:**

```bash
systemctl --user start app-steam@autostart.service
balooctl6 resume || balooctl resume; systemctl --user start kde-baloo.service
systemctl --user stop deck-telemetry
```

Reading the telemetry: throttling looks like sclk falling while temp climbs. On
2026-09-12 two back-to-back passes starting 13 C apart (42 C vs 55 C) produced
identical numbers, both reaching the 1600 MHz top state at a 79 C peak -- so a
dip that is *not* accompanied by suppressed clocks is contention, not heat.

### Version and setup checks (once per machine, before each campaign)

These must all match what the config expects; if any differ, fix before
running or the campaign is not comparable with the previous one.

```bash
# llama-server: build 10441 (commit 0177dcc73) on all three
<llama-server> --version                  # Mac: /Users/mala/workspace/llama.cpp/build/bin/llama-server
                                          # pod: /home/mala/workspace/llama.cpp/build/bin/llama-server
                                          # Deck: /home/deck/workspace/llama.cpp/build/bin/llama-server

# llamafile: the same binary everywhere, sha256 648cd658ea642218..., reports v0.10.6
sha256sum <llamafile>                     # Mac: /Users/mala/llamafiles/llamafile-0.10.6-c73be59 (shasum -a 256)
                                          # pod: /home/mala/llamafiles/llamafile-0.10.6-c73be59
                                          # Deck: /home/deck/Downloads/llamafile-0.10.6-c73be59

# GGUFs: 091d8deb... (0.8B), cd76ec20... (9B), e00082f7... (27B; not on the Deck)
sha256sum ~/.lmstudio/models/lmstudio-community/Qwen3.*/Qwen3.*.gguf     # shasum -a 256 on the Mac

# Ollama tags built from those files (blob sha256 == file sha256)
for t in qwen3.5:0.8b-lms qwen3.5:9b-lms qwen3.8:27b-lms qwen3.8:27b-lms-mtp qwen3.8:27b-lms-mtp4; do
  echo "$t $(ollama show --modelfile $t | sed -n 's|^FROM .*/sha256-||p' | head -1 | cut -c1-12)"; done
# missing? -> ollama/create-lms-models.sh [LMS_ROOT]   (Deck: only the 0.8B/9B exist; the 27B lines say MISSING)
# draft lengths baked into the -mtp tags: 2 and 4 respectively
ollama show --parameters qwen3.8:27b-lms-mtp  | grep draft_num_predict     # 2
ollama show --parameters qwen3.8:27b-lms-mtp4 | grep draft_num_predict     # 4
grep -c "spec-draft-n-max 2" experiments.yaml experiments.linux.yaml       # 2 each (llamafile-mtp, llama-cpp-mtp)

# Deck only: from 2026-09-12 the comparison is NO LONGER "as shipped" for llamafile.
# It runs the LunarG-SDK 1.4.357.1 ggml-vulkan.so from ~/vkab/sdk/ (integer-dot
# shaders) while llama-server and LM Studio's vulkan 2.28.2 stay on stock-glslc
# builds without them. That asymmetry is worth roughly +22-24 % prefill on the 0.8B
# by toolchain alone (data/20260911-steamdeck-vulkan-sdk/), so the Deck's llamafile
# prefill column is NOT an engine result and must be reported with that caveat.
# This supersedes the 2026-09-11 "as shipped" decision; revisit once llama-server
# is rebuilt with an SDK glslc, which is what would restore parity at int dot: 1.
strings /home/deck/workspace/llama.cpp/build/bin/llama-server | grep -c matmul_q4_k_q8_1   # 0 (stock)
strings /home/deck/llamafile-42ff11b/ggml-vulkan.so | grep -c matmul_q4_k_q8_1             # 11 (SDK)
ls /home/deck/Downloads/ggml-vulkan.so 2>/dev/null                                          # must NOT exist (stale override next to the OLD binary)

# LM Studio runtime pinned to 2.28.2 -- LM Studio downloads newer runtimes on its own
lms runtime ls                            # the ✓ must be on ...-2.28.2 (metal on the Mac, cuda12 on the pod, vulkan on the Deck)
lms runtime select llama.cpp-<platform>-2.28.2   # if not

# Ollama context and GPU
# Mac:  the runner starts `ollama serve` itself with OLLAMA_CONTEXT_LENGTH=16384 (experiments.yaml); Ollama.app may stay open
# pod:  systemctl show ollama -p Environment | tr ' ' '\n' | grep OLLAMA_CONTEXT_LENGTH   -> 16384 (drop-in benchy.conf)
# Deck: the runner starts it with OLLAMA_VULKAN=1 OLLAMA_IGPU_ENABLE=1 OLLAMA_CONTEXT_LENGTH=16384 (experiments.steamdeck.yaml)
```

### Benchmarking a new llamafile build

Copy the one binary to all three machines into **its own directory** named for
its commit (`~/llamafile-<sha>/llamafile-<version>-<sha>`), change the path in
all three configs -- never point a config at a checkout's `o/llamafile/llamafile`,
which is rebuilt by other work.

**The binary alone does not pin the GPU kernels.** A thin build bundles no GPU
module (`python3 -c "import zipfile,sys;print([n for n in zipfile.ZipFile(sys.argv[1]).namelist() if n.endswith('.so')])" <llamafile>`
prints `[]`), and the loader searches, in order:

1. `<exe_dir>/ggml-*.so`  ← the only location you control per build
2. `/zip/ggml-*.so` (bundled; absent in a thin build)
3. `~/.llamafile/v/<version>/ggml-*.so`
4. `~/ggml-*.so`

Two traps follow, both silent:

- **The version string is not the build.** 0.10.6 c73be59 and 0.10.6 42ff11b
  share `~/.llamafile/v/0.10.6/`, so a new binary with an empty exe_dir runs the
  *previous* build's kernels and the campaign measures nothing new.
- **A stray module wins.** `~/llamafiles/ggml-cuda.so` on the pod (Aug 2026,
  pre-graphs) sat exactly where the binary used to live and outranks everything.

So: one directory per build, the intended module copied in next to it, and
verify what actually loaded from the server log rather than assuming.

```bash
# identity: the same file everywhere, and what it says it is
sha256sum <llamafile>; <llamafile> --version

# the module next to it -- capability, not just a hash
strings <exe_dir>/ggml-cuda.so   | grep -ci "cuda graph"          # >0: built with CUDA graphs (0 in 0.10.6 c73be59)
strings <exe_dir>/ggml-vulkan.so | grep -c matmul_q4_k_q8_1       # >0: integer-dot shaders (0 in the shipped module)

# PROOF of what loaded, from the run's own *.server.log (llamafile_info at INFO level):
grep -E "probing library|loaded library" results/*-llamafile*.server.log | head
```

Decide before running: build llama-server with a LunarG-SDK glslc too, or keep
stock and say so in the post. (2026-09-12 chose the third option: get pre-built
llama-server release which has been compiled with recend shaders. LM Studio
remains the only engine with no `int dot`, caveat carried in the writeup.)

```bash
# server defaults unchanged vs llama-server: compare the parameter dump of a first request
# (both print n_ctx, n_batch, n_ubatch, n_parallel/n_slots, flash_attn, cache-ram, spec settings)
<llamafile> -m <gguf> --server --ctx-size 16384 -v 2>&1 | grep -E "n_batch|n_ubatch|n_slots|flash|cache|ctx" | head
<llama-server> -m <gguf> --ctx-size 16384 -v       2>&1 | grep -E "n_batch|n_ubatch|n_slots|flash|cache|ctx" | head
```

A changed default in the new build is a second variable hiding inside "new
build"; either revert it for the campaign or record it.

Machine-specific preconditions:

- **Mac**: Ollama.app should be running (the preflight runs `ollama ls` against
  it; the runner then stops it and starts its own daemon per cell and you will
  be asked to confirm freeing port 11434 -- answer `y`). `lms` works headless.
- **pod**: `systemctl is-active ollama` must be `active` for the preflight;
  the runner restarts/stops the service per cell and leaves it **stopped** at
  the end. LM Studio's service wakes up on `lms` use.
- **Deck**: the LM Studio AppImage must be alive for `lms` to work; the config
  launches it in the desktop session if it isn't (`systemd-run --user --unit=lmstudio-benchy --collect ~/Downloads/LM-Studio-*.AppImage`).
  No Ollama daemon should be running (`pgrep -x ollama` empty); the preflight
  reads the tags from the manifest store, no daemon needed.

## 1. Back up the previous campaign

The runner merges into whatever `results/` holds and would overwrite cells with
the same name. On each machine:

```bash
cd <repo> && D=old_$(date +%Y%m%d) && mkdir $D && mv results report logs $D/ 2>/dev/null; mkdir -p logs
```

## 2. Launch

Interactive is fine (`uv run run.py [--config ...]` in a terminal, answer `y`
to the port prompt on the Mac), but for an unattended run use what survives an
ssh logout on each system:

**Mac Studio** (tmux; Homebrew tmux is not on the non-login PATH):

```bash
export PATH=/Users/mala/.local/bin:/Users/mala/.lmstudio/bin:/usr/local/bin:/opt/homebrew/bin:$PATH
cd /Users/mala/workspace/exp-benchy
tmux new-session -d -s benchy-all -c $PWD "export PATH=$PATH; uv run run.py 2>&1 | tee logs/run-all.log"
# within ~5 s the preflight asks to stop Ollama.app on port 11434:
tmux send-keys -t benchy-all y Enter
```

**L40S pod** (tmux; no port prompt -- `lsof` cannot see the ollama-owned socket):

```bash
export PATH=/home/mala/.local/bin:/home/mala/.lmstudio/bin:/usr/local/bin:$PATH
cd /home/mala/workspace/exp-benchy
tmux new-session -d -s benchy-all -c $PWD "export PATH=$PATH; uv run run.py --config experiments.linux.yaml 2>&1 | tee logs/run-all.log"
```

**Steam Deck** (systemd user unit -- SteamOS has `KillUserProcesses=True`, so
tmux/nohup started from ssh die on logout):

```bash
cd /home/deck/workspace/exp-benchy
systemd-run --user --unit=benchy-all --collect --working-directory=$PWD \
  --setenv=PATH=/home/deck/.local/bin:/home/deck/.lmstudio/bin:/usr/local/bin:/usr/bin:/bin --setenv=HOME=/home/deck \
  bash -c "uv run run.py --config experiments.steamdeck.yaml > logs/run-all.log 2>&1"
```

Sanity-check within a minute: `logs/run-all.log` shows `Preflight OK`,
`Experiment: ...`, and the first `Starting server...`. If it shows `Preflight
failed`, read the reason (missing model, busy port, `ollama ls` without a
daemon) -- nothing has been started.

## 3. Monitor

```bash
grep -c "✓" logs/run-all.log                                   # cells done (of 120 / 120 / 64)
grep -E "✗|NO METRICS|Server not ready|Traceback" logs/run-all.log   # should stay empty
tail -3 logs/run-all.log
tmux attach -t benchy-all              # Mac/pod;  systemctl --user status benchy-all   # Deck
```

A cell that returns no measurement is quarantined as `*.no-metrics.json` and
the remaining cells for that server+model are skipped; the final summary lists
them. Fix the cause and re-run with `--resume` to fill only the missing cells.

## 4. After the run

- Mac: `open -a Ollama` (the runner killed the app).
- pod: `sudo systemctl start ollama` (the last Ollama cell left the service stopped).
- Deck: nothing required; the LM Studio window can stay open.
- `report/*.md` holds the tables; check the "Trimmed runs" section -- rows far
  below the mean are interference, rows far above on PP are prompt-cache hits.

## 5. Collect to the laptop

```bash
tools/collect_campaign.sh studio        /Users/mala/workspace/exp-benchy data/<date>-m4max     2026-09 2026-10
tools/collect_campaign.sh 89.169.109.142 /home/mala/workspace/exp-benchy  data/<date>-l40s      2026-09 2026-10
tools/collect_campaign.sh steamdeck     /home/deck/workspace/exp-benchy  data/<date>-steamdeck 2026-09 2026-10
```

(The trailing arguments are the LM Studio server-log months to fetch.) Then add
a paragraph to `data/README.md`.

## 6. Analyse

```bash
# server-side timings (engine print_timing) attributed to cells, per campaign
tools/server_timings.py --results data/<c>/results \
    --lmstudio-log data/<c>/lmstudio-server-logs/*.log \
    --ollama-log data/<c>/logs/ollama-serve.log \        # Mac, Deck
    --ollama-log data/<c>/ollama-journal.log \           # pod
    --csv data/<c>/server-timings.csv

# the three blog figures (MTP 27B column; LM Studio's macOS decode server-side) -> data/plots/
tools/make_figures.sh                     # edit the campaign dirs inside when a repeat replaces them

# any other view of one campaign, e.g. everything server-side
uv run tools/plot_campaign.py data/<c> --title "..." --source server

# consistency with a previous campaign on the same machine
tools/compare_campaigns.py data/2026xxxx-l40s data/<c>            # client-side
tools/compare_campaigns.py data/2026xxxx-l40s data/<c> --source server
```

`compare_campaigns.py` flags cells whose difference exceeds ±3 combined
standard errors. Expect the MTP cells to have wide bands (acceptance-rate
variance) and everything else to reproduce within a few percent; a whole
server drifting in one direction means a runtime updated itself (check
`host-info.txt` of both campaigns) or the machine ran hotter. Against the
2026-09-10 campaigns the `qwen3.8-27b-mtp` cells differ by design (draft 2 now,
4 then): the like-for-like check for those is the new `qwen3.8-27b-mtp4`
experiment against the old `qwen3.8-27b-mtp` (same servers, same draft),
compared by hand from the report tables or `plots/*.csv`.

## 7. Pitfalls seen so far

- **SteamOS kills ssh-session processes on logout** (`KillUserProcesses=True`):
  use `systemd-run --user`, never tmux/nohup from ssh, for anything long.
- **`pkill -f "ollama serve"` kills the shell running it** (the pattern matches
  the `sh -c` command line): use `pkill -x ollama`.
- **The runner's port prompt needs a TTY**: on the Mac Ollama.app holds 11434,
  so run in tmux and send `y`, or start the run from an interactive terminal.
- **Preflight needs `ollama ls` to work**: a running daemon on Mac/pod; on the
  Deck the config reads the manifest store instead.
- **LM Studio auto-downloads newer runtimes**: re-check `lms runtime ls` before
  every campaign and re-select 2.28.2.
- **LM Studio's client-side decode on macOS is inflated** (~15 % at tg=32,
  ~7 % at tg=64) by stream batching; report its server-side timings
  (`tools/server_timings.py`), see `data/20260912-m4max/lmstudio-client-vs-server.md`.
- **LM Studio ignores `cache_prompt: false`**: rare prompt-cache hits inflate
  a PP cell; the symmetric trim removes single hits, the "Trimmed runs" table
  shows them.
- **Ollama on the Deck is CPU-only unless `OLLAMA_VULKAN=1 OLLAMA_IGPU_ENABLE=1`**
  and truncates prompts without `OLLAMA_CONTEXT_LENGTH` -- both set in its config.
- **Braces in yaml commands**: `start_cmd`/`stop_cmd` go through `str.format`,
  so shell `{ ... }` blocks break them -- use `if ...; then ...; fi`.
- **The Mac's `git pull` fails if an untracked file shadows a new tracked one**:
  move it aside first.
- **Other benchmarks share these machines**: on 2026-09-11 a Vulkan-toolchain
  A/B (`vkab-bench.service`, `~/vkab/` on the Deck) started 73 s after the
  campaign's last cell and collided with a follow-up A/B for ten minutes, spoiling
  both. Before starting anything that touches the GPU, list running user units
  (Deck), tmux sessions (Mac/pod) and `pgrep -fl "llamafile|llama-server|ollama"`;
  a benchmark that ran alongside another one is not data.
