#!/usr/bin/env python3
"""exp-benchy runner — executes llama-benchy across a server/model/pp/tg matrix."""

import argparse
import json
import logging
import math
import re
import statistics
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("benchy")


# ===================== DATA CLASSES =====================


@dataclass
class Run:
    experiment_id: str
    server_key: str
    server_config: dict
    model_name: str
    model_tokenizer: str
    model: str              # resolved model path/id
    model_source: str       # which config key produced `model`, for error messages
    served_model_name: str
    label: str              # model_name + server.label_suffix
    pp: int
    tg: int
    base_url: str
    result_file: Path       # under results_dir (relative if results_dir is relative)


# ===================== YAML LOADING + RESOLUTION =====================


def load_config(path: Path) -> dict:
    """Load and return the experiments YAML as a dict."""
    with open(path) as f:
        return yaml.safe_load(f)


def resolve_sweep_ref(value: Any, sweeps: dict) -> Any:
    """Expand $sweeps.<key> references in config values."""
    if isinstance(value, str) and value.startswith("$sweeps."):
        key = value[len("$sweeps."):]
        return sweeps[key]
    return value


def _expand_template(template: str, vars: dict, **kwargs) -> str:
    """Expand a template string, resolving {vars.<key>} and named placeholders."""
    def replace_vars(match: re.Match) -> str:
        key = match.group(1)
        return str(vars.get(key, match.group(0)))
    # First resolve {vars.<key>} references
    expanded = re.sub(r"\{vars\.([^}]+)\}", replace_vars, template)
    # Then resolve remaining named placeholders
    return expanded.format(**kwargs)


def resolve_model_for_server(model: dict, server_key: str,
                              server_cfg: dict, vars: dict) -> dict:
    """Resolve served_model_name and model path for a (model, server) pair.

    Cascade:
        served_model_name → refs[server].served_model_name or model.name
        model             → refs[server].model or rendered server.model_template
    """
    name = model["name"]
    tokenizer = model["tokenizer"]
    label_suffix = server_cfg["label_suffix"]

    refs = model.get("refs", {}).get(server_key, {})

    # served_model_name: explicit override or default to model name
    served_model_name = refs.get("served_model_name", name)

    # model path: explicit override or render server template. Both go through
    # the same expansion, so an override can use {vars.*} and
    # {served_model_name} exactly like a model_template can.
    if "model" in refs:
        template = refs["model"]
        model_source = f"refs[{server_key}].model: {template}"
    else:
        template = server_cfg["model_template"]
        model_source = f"server.model_template: {template}"
    model_path = _expand_template(
        template, vars, served_model_name=served_model_name
    )

    label = f"{name}{label_suffix}"

    return {
        "model_name": name,
        "model_tokenizer": tokenizer,
        "served_model_name": served_model_name,
        "model": model_path,
        "model_source": model_source,
        "label": label,
    }


def expand_experiments(config: dict, results_dir: Path) -> list[Run]:
    """Expand all experiments into a flat list of Run objects."""
    sweeps = config.get("sweeps", {})
    vars = config.get("vars", {})
    servers = config["servers"]
    models = config["models"]
    experiments = config["experiments"]

    runs: list[Run] = []
    for exp in experiments:
        exp_id = exp["id"]

        server_keys = resolve_sweep_ref(exp["servers"], sweeps)
        model_names = resolve_sweep_ref(exp["models"], sweeps)
        pp_values = resolve_sweep_ref(exp["pp"], sweeps)
        tg_values = resolve_sweep_ref(exp["tg"], sweeps)

        # Resolve models by name
        model_map = {m["name"]: m for m in models}

        # Cell-major order: for each (model, pp, tg) every server runs back to
        # back, so the servers being compared see the same machine state
        # (thermals, background load) minutes apart rather than hours apart.
        # Costs nothing extra: the server is restarted for every cell anyway.
        for model_name in model_names:
            model = model_map[model_name]
            resolved_by_server = {
                server_key: resolve_model_for_server(model, server_key, servers[server_key], vars)
                for server_key in server_keys
            }
            for pp in pp_values:
                for tg in tg_values:
                    for server_key in server_keys:
                        server_cfg = servers[server_key]
                        resolved = resolved_by_server[server_key]
                        result_file = results_dir / f"{exp_id}_{resolved['label']}_pp{pp}_tg{tg}.json"
                        runs.append(Run(
                            experiment_id=exp_id,
                            server_key=server_key,
                            server_config=server_cfg,
                            model_name=resolved["model_name"],
                            model_tokenizer=resolved["model_tokenizer"],
                            model=resolved["model"],
                            model_source=resolved["model_source"],
                            served_model_name=resolved["served_model_name"],
                            label=resolved["label"],
                            pp=pp,
                            tg=tg,
                            base_url=server_cfg["base_url"],
                            result_file=result_file,
                        ))
    return runs


# ===================== PREFLIGHT =====================
#
# Both checks run once, before the first server is touched. They exist because
# the per-run lifecycle cannot report either problem usefully: a busy port is
# silently resolved by stop_cmd killing the stranger, and a missing model file
# only ever surfaces as a generic ready_check timeout.


def port_for_base_url(base_url: str) -> int | None:
    """Extract the TCP port from a base_url, applying the scheme default."""
    parts = urllib.parse.urlsplit(base_url)
    if parts.port is not None:
        return parts.port
    return {"http": 80, "https": 443}.get(parts.scheme)


def port_listeners(port: int) -> list[tuple[str, str]]:
    """Return [(pid, command)] for processes LISTENing on a TCP port.

    Filtered to LISTEN sockets so inbound client connections to some other
    service don't read as a conflict. An lsof miss exits non-zero with no
    output, which is simply "nothing there".
    """
    found = subprocess.run(
        ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
        capture_output=True, text=True,
    )
    pids = [line.strip() for line in found.stdout.splitlines() if line.strip()]

    listeners = []
    for pid in pids:
        described = subprocess.run(
            ["ps", "-o", "command=", "-p", pid],
            capture_output=True, text=True,
        )
        listeners.append((pid, described.stdout.strip() or "<unknown>"))
    return listeners


def is_registry_backed(run: Run) -> bool:
    """Whether this run's `model` is a registry id rather than a file path.

    A server declares itself registry-backed by providing `list_models_cmd`
    (ollama, lm-studio). Everything else resolves `model` to a file, so a bare
    filename there is a relative path -- not an opaque id -- and can be checked.
    An absolute path is always treated as a file, whatever the server.
    """
    if Path(run.model).expanduser().is_absolute():
        return False
    return bool(run.server_config.get("list_models_cmd"))


def preflight_model_files(runs: list[Run]) -> list[str]:
    """Check every model that resolves to a file on disk exists."""
    seen: set[tuple[str, str]] = set()
    problems = []
    for run in runs:
        if is_registry_backed(run):
            continue  # checked by preflight_registry_models

        key = (run.server_key, run.model)
        if key in seen:
            continue
        seen.add(key)

        raw = Path(run.model).expanduser()
        path = raw if raw.is_absolute() else Path.cwd() / raw
        if path.is_file():
            continue

        detail = [
            f"model for '{run.server_key}' / '{run.model_name}' "
            f"{'is not a file' if path.exists() else 'does not exist'}:",
            f"      {path}",
        ]
        if not raw.is_absolute():
            detail.append(
                f"      ('{run.model}' is relative, so it resolves against the "
                f"current directory -- use an absolute path or a {{vars.*}} "
                f"reference)"
            )
        detail.append(f"      from {run.model_source}")
        problems.append("\n".join(detail))
    return problems


def preflight_registry_models(runs: list[Run]) -> list[str]:
    """Check registry-backed models are installed, via the server's list_models_cmd.

    Servers like ollama and lm-studio resolve `model` to a registry id rather
    than a path, so there is no file to stat. Each such server declares a
    command that lists what it has installed (`ollama list`, `lms ls`); the
    served id is matched as a substring of that output, which tolerates the
    namespacing and column layout those tools use. Servers with no
    `list_models_cmd` are file-backed, and handled by preflight_model_files.
    """
    # One list command per server, however many runs reference it.
    by_server: dict[str, dict] = {}
    for run in runs:
        if not is_registry_backed(run):
            continue  # file-backed, checked by preflight_model_files
        list_cmd = run.server_config["list_models_cmd"]
        entry = by_server.setdefault(run.server_key, {"cmd": list_cmd, "models": {}})
        entry["models"][run.served_model_name] = run.model_name

    problems = []
    for server_key, entry in sorted(by_server.items()):
        shown = entry["cmd"].strip()
        listed = execute_cmd(entry["cmd"], f"preflight {server_key}")
        if listed.returncode != 0:
            output = (listed.stderr.strip() or listed.stdout.strip() or "<no output>")
            problems.append(
                f"could not list installed models for '{server_key}' "
                f"(`{shown}` exited {listed.returncode}):\n      {output}"
            )
            continue

        for served, model_name in sorted(entry["models"].items()):
            if served not in listed.stdout:
                problems.append(
                    f"model for '{server_key}' / '{model_name}' is not installed:\n"
                    f"      '{served}' does not appear in the output of `{shown}`"
                )
    return problems


def busy_ports(runs: list[Run]) -> list[tuple[int, Run, list[tuple[str, str]]]]:
    """Find matrix ports that already have a listener.

    Returns [(port, representative run, listeners)]. The run comes along so the
    caller can reach that server's own stop_cmd, which knows how to shut its
    server down properly.
    """
    ports: dict[int, Run] = {}
    for run in runs:
        port = port_for_base_url(run.base_url)
        if port is None:
            continue
        ports.setdefault(port, run)

    busy = []
    for port in sorted(ports):
        listeners = port_listeners(port)
        if listeners:
            busy.append((port, ports[port], listeners))
    return busy


def resolve_busy_ports(runs: list[Run], vars: dict) -> None:
    """Offer to free any matrix port that is already occupied.

    The runner restarts every server between runs -- that is what keeps weights
    and KV cache cold -- so it cannot tell its own leftovers from a server
    someone is deliberately using. Rather than deciding for you, it asks once,
    here, before any benchmarking starts.

    Shutdown goes through the owning server's own stop_cmd rather than a raw
    kill, because those commands already handle the awkward cases (Ollama.app
    respawning its daemon, `lms server stop`).
    """
    busy = busy_ports(runs)
    if not busy:
        return

    logger.warning("Ports needed by this matrix are already in use:")
    for port, run, listeners in busy:
        logger.warning("  port %d (needed by '%s'):", port, run.server_key)
        for pid, cmd in listeners:
            logger.warning("      PID %s  %s", pid, cmd)

    if not sys.stdin.isatty():
        logger.error("Cannot ask which to stop: stdin is not a terminal. "
                     "Free the ports above and re-run.")
        sys.exit(1)

    try:
        answer = input("\nStop these and start the matrix? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        logger.error("Aborted; nothing was stopped.")
        sys.exit(1)

    if answer not in ("y", "yes"):
        logger.error("Aborted; nothing was stopped.")
        sys.exit(1)

    for port, run, _ in busy:
        logger.info("Stopping port %d via the '%s' stop_cmd...", port, run.server_key)
        stop_cmd = _expand_template(
            run.server_config["stop_cmd"], vars,
            model=run.model,
            served_model_name=run.served_model_name,
        )
        execute_cmd(stop_cmd, f"preflight {run.server_key}")

    time.sleep(2)
    still = busy_ports(runs)
    if still:
        logger.error("Still in use after stopping -- giving up:")
        for port, run, listeners in still:
            for pid, cmd in listeners:
                logger.error("  port %d: PID %s  %s", port, pid, cmd)
        sys.exit(1)

    logger.info("Ports are free.")


def run_preflight(runs: list[Run], vars: dict) -> None:
    """Check models, then settle any port conflicts, before anything starts."""
    logger.info("Preflight: %d runs, checking models and ports...", len(runs))

    # Missing models first: nothing about a port conflict is worth resolving
    # if the matrix cannot run anyway, and this costs no side effects.
    problems = preflight_model_files(runs) + preflight_registry_models(runs)
    if problems:
        logger.error("Preflight failed -- not starting any servers:")
        for problem in problems:
            logger.error("  - %s", problem)
        sys.exit(1)

    resolve_busy_ports(runs, vars)
    logger.info("Preflight OK")


# ===================== SERVER LIFECYCLE =====================


def execute_cmd(cmd: str, label: str) -> subprocess.CompletedProcess:
    """Run a shell command to completion (foreground). Returns the CompletedProcess."""
    logger.debug("[%s] Executing:\n%s", label, cmd)
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def start_server(cmd: str, label: str, results_dir: Path) -> tuple[subprocess.Popen, Path]:
    """Start a server command in the background, returning (Popen handle, log file path).

    stdout/stderr go to a log file alongside the run results. The parent-side
    file handle is closed immediately after Popen launches — the child has its
    own duped fd and writes through that.
    """
    log_file = results_dir / f"{label.replace(' ', '_').replace('=', '_')}.server.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info("[%s] Server log: %s", label, log_file)
    with open(log_file, "w") as f:
        proc = subprocess.Popen(
            cmd, shell=True,
            stdout=f, stderr=subprocess.STDOUT,
        )
    return proc, log_file


def log_tail(log_file: Path | None, lines: int = 20) -> str:
    """Format the tail of a server log for inclusion in an error message."""
    if log_file is None or not log_file.exists():
        return ""
    try:
        content = log_file.read_text(errors="replace").splitlines()
    except OSError as e:
        return f"\n  (could not read {log_file}: {e})"
    if not content:
        return f"\n  (server log {log_file} is empty)"
    tail = content[-lines:]
    body = "\n".join(f"    {line}" for line in tail)
    return f"\n  last {len(tail)} line(s) of {log_file}:\n{body}"


def advertised_models(body: bytes) -> set[str]:
    """Collect the model identifiers a /models payload advertises.

    Covers both shapes seen in practice: the OpenAI-style `data[].id` (plus
    `aliases`) used by llama.cpp and llamafile, and the Ollama-style
    `models[].name`.
    """
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return set()
    if not isinstance(payload, dict):
        return set()

    found: set[str] = set()
    for entry in payload.get("data", []):
        if not isinstance(entry, dict):
            continue
        if isinstance(entry.get("id"), str):
            found.add(entry["id"])
        for alias in entry.get("aliases", []) or []:
            if isinstance(alias, str):
                found.add(alias)
    for entry in payload.get("models", []):
        if not isinstance(entry, dict):
            continue
        for key in ("name", "model"):
            if isinstance(entry.get(key), str):
                found.add(entry[key])
    return found


def serves_model(advertised: set[str], served_model_name: str) -> bool:
    """Whether an advertised identifier refers to served_model_name.

    Exact match is the rule, because that is what an OpenAI-style `model` field
    has to match for a request to reach the instance we started. The one
    allowance is llama.cpp and llamafile, which advertise the GGUF's absolute
    path where we ask for the bare name.

    Deliberately does NOT strip a `namespace/` prefix: `qwen3.5-0.8b` must not
    be accepted for an advertised `qwen/qwen3.5-0.8b`, since LM Studio treats
    those as different models and will silently load a second, default-configured
    instance to serve the mismatched name.
    """
    model_suffixes = (".gguf", ".safetensors")
    for entry in advertised:
        if entry == served_model_name:
            return True
        # Absolute path to a weights file -> compare its bare filename.
        if entry.startswith("/") and entry.endswith(model_suffixes):
            name = entry.rsplit("/", 1)[-1]
            for suffix in model_suffixes:
                if name.endswith(suffix):
                    name = name[: -len(suffix)]
                    break
            if name == served_model_name:
                return True
    return False


def wait_for_ready(base_url: str, path: str, timeout_s: int,
                   proc: subprocess.Popen | None = None,
                   served_model_name: str | None = None) -> tuple[bool, str]:
    """Poll base_url + path until the server is ready. Returns (ok, reason).

    Three ways to stop early or fail informatively:
      - `proc` died  → return immediately rather than polling a dead port for
        the full timeout, which is what a bad model path looks like.
      - HTTP 200 but `served_model_name` absent from the payload → accept,
        with a warning. Only a warning: the identifier a server advertises does
        not reliably equal the name we ask for, and the up-front port preflight
        is what actually keeps foreign servers out.
      - timeout → report the last transport error seen.
    """
    url = f"{base_url}{path}"
    deadline = time.time() + timeout_s
    started = time.time()
    attempt = 0
    last_reason = "no response before timeout"

    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            return False, (f"server process exited with code {proc.returncode} "
                           f"after {time.time() - started:.1f}s")
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            if resp.status == 200:
                if served_model_name is not None:
                    advertised = advertised_models(resp.read())
                    if advertised and not serves_model(advertised, served_model_name):
                        logger.warning(
                            "  %s is up but advertises %s, expected '%s' — "
                            "continuing anyway",
                            url, sorted(advertised), served_model_name,
                        )
                logger.debug("  ready in %.1fs (%d attempts)", time.time() - started, attempt)
                return True, ""
            else:
                last_reason = f"{url} returned HTTP {resp.status}"
        except Exception as e:
            last_reason = f"{url}: {e}"
            if attempt < 2 or attempt % 10 == 0:
                logger.debug("  ready check attempt %d: %s", attempt, e)
        attempt += 1
        time.sleep(0.5)

    if proc is not None and proc.poll() is not None:
        return False, (f"server process exited with code {proc.returncode} "
                       f"after {time.time() - started:.1f}s")
    return False, last_reason


def run_server_lifecycle(run: Run, benchy_template: str, vars: dict,
                         results_dir: Path) -> dict:
    """Full lifecycle: start → ready → bench → stop.

    Every run stops its own server in a finally, and the matrix-level preflight
    guarantees a free port before the first one -- so there is normally nothing
    to clean up on the way in. The port is still checked, because a leftover
    would otherwise be silently benchmarked with a warm cache, but stop_cmd only
    runs if something is actually there.

    Returns the parsed benchmark result dict.
    Raises RuntimeError on lifecycle failure (after best-effort cleanup).
    """
    cfg = run.server_config
    label = f"{run.server_key} {run.model_name} pp={run.pp} tg={run.tg}"

    # Render start_cmd / stop_cmd with vars + model + served_model_name
    # (see experiments.yaml header for the documented contract).
    start_cmd = _expand_template(
        cfg["start_cmd"], vars,
        model=run.model,
        served_model_name=run.served_model_name,
    )
    stop_cmd = _expand_template(
        cfg["stop_cmd"], vars,
        model=run.model,
        served_model_name=run.served_model_name,
    )

    # 1. Only clean up if something actually survived the previous run. Doing
    #    this unconditionally doubled the stop_cmd calls per run and reported
    #    failures for work that wasn't needed ("No models to unload").
    port = port_for_base_url(run.base_url)
    leftover = port_listeners(port) if port is not None else []
    if leftover:
        for pid, cmd in leftover:
            logger.warning("[%s] Port %d still held by PID %s (%s) — stopping it",
                           label, port, pid, cmd)
        stop_result = execute_cmd(stop_cmd, label)
        if stop_result.returncode != 0:
            logger.warning("[%s] stop_cmd exited %d: %s", label,
                           stop_result.returncode, stop_result.stderr.strip())
        time.sleep(1)  # let the port release before rebinding

    # 2. Start server
    logger.info("[%s] Starting server...", label)
    server_proc = None
    server_log = None
    if cfg.get("foreground", False):
        # Foreground servers (llamafile, llama-cpp) must be backgrounded by us.
        server_proc, server_log = start_server(start_cmd, label, results_dir)
    else:
        # Self-contained start scripts (ollama, lm-studio) daemonize themselves
        # and return once the server is up; we just run them to completion.
        start_result = execute_cmd(start_cmd, label)
        if start_result.returncode != 0:
            output = (start_result.stderr.strip() or start_result.stdout.strip()
                      or "<no output>")
            logger.error("[%s] start_cmd exited %d: %s", label,
                          start_result.returncode, output)
            raise RuntimeError(
                f"start_cmd exited {start_result.returncode} for {label}: {output}"
            )

    # Give the server a moment to initialize before ready polling
    time.sleep(1)

    # 3. Wait for ready
    rc = cfg["ready_check"]
    logger.info("[%s] Waiting for server ready (timeout=%ds)...", label, rc["timeout_s"])
    ready, reason = wait_for_ready(
        run.base_url, rc["path"], rc["timeout_s"],
        proc=server_proc,
        served_model_name=run.served_model_name,
    )
    if not ready:
        # Best-effort cleanup: kill background process + stop_cmd
        if server_proc is not None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
        execute_cmd(stop_cmd, label)
        raise RuntimeError(
            f"Server not ready for {label}: {reason}{log_tail(server_log)}"
        )

    logger.info("[%s] Server ready!", label)

    try:
        # 4. Run benchmark
        result = execute_benchmark(run, benchy_template)
        return result
    finally:
        # 5. Stop server (always, even on benchmark failure)
        logger.info("[%s] Stopping server...", label)
        stop_result = execute_cmd(stop_cmd, label)
        if stop_result.returncode != 0:
            logger.warning("[%s] final stop_cmd exited %d: %s", label,
                           stop_result.returncode, stop_result.stderr.strip())
        # Also terminate the background process if it was started
        if server_proc is not None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()


# ===================== BENCHMARK EXECUTION =====================


def render_benchy_cmd(benchy_template: str, run: Run) -> str:
    """Render the benchy_cmd template with Run fields."""
    return benchy_template.format(
        base_url=run.base_url,
        label=run.label,
        served_model_name=run.served_model_name,
        tokenizer=run.model_tokenizer,
        pp=run.pp,
        tg=run.tg,
        result_file=str(run.result_file),
    )


def execute_benchmark(run: Run, benchy_template: str) -> dict:
    """Render and execute llama-benchy, return parsed JSON result."""
    cmd = render_benchy_cmd(benchy_template, run)
    logger.info("[%s] Running benchmark:\n%s", run.label, cmd)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"llama-benchy exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # Validate result file exists and is valid JSON
    if not run.result_file.exists():
        raise FileNotFoundError(f"Result file not created: {run.result_file}")

    with open(run.result_file) as f:
        return json.load(f)


# ===================== AGGREGATION =====================


# Metrics without which a cell has no measurement at all. `ttfr` is reported
# too, but its absence doesn't invalidate the throughput numbers.
CORE_METRICS = ("pp_throughput", "tg_throughput")
REPORTED_METRICS = ("pp_throughput", "tg_throughput", "ttfr")


def clear_quarantine(result_file: Path) -> None:
    """Drop a previous run's *.no-metrics.json once the cell has a real result.

    Otherwise a superseded failure keeps sitting in the results directory,
    reading as if this cell still had no measurement.
    """
    void_file = result_file.with_suffix(".no-metrics.json")
    if not void_file.exists():
        return
    try:
        void_file.unlink()
        logger.debug("  removed superseded %s", void_file.name)
    except OSError as e:
        logger.warning("  could not remove %s: %s", void_file, e)


def quarantine_result(result_file: Path) -> Path | None:
    """Move a result file holding no measurement out of the results namespace.

    The raw llama-benchy output is worth keeping, but not under a name that
    reads as a finished cell: both --resume and the report loader key off the
    result file existing, so leaving it would make a void run look done.
    """
    if not result_file.exists():
        return None
    void_file = result_file.with_suffix(".no-metrics.json")
    try:
        result_file.replace(void_file)
    except OSError as e:
        logger.warning("  could not set aside %s: %s", result_file, e)
        return None
    logger.warning("  no result recorded for this cell; raw output kept at %s", void_file)
    return void_file


class NoMetricsError(RuntimeError):
    """llama-benchy wrote a result file that contains no usable measurement.

    Distinct from a crash: the benchmark ran and exited 0, it just produced
    nulls. That is a configuration problem (context too small for the prompt,
    wrong model served, ...) and therefore deterministic -- retrying re-runs an
    expensive benchmark to fail identically, so it isn't retried, and the
    remaining cells for the same server+model are skipped.
    """


# One aggregation rule, applied identically to every cell and every metric.
# It is fixed in advance and never adapts to the data it is given:
#   * a cell needs at least MIN_RUNS values -- fewer is not a smaller sample,
#     it is no result (the runner also refuses a benchy_cmd asking for fewer);
#   * values[0] is the warm-up run and is dropped;
#   * of the remaining runs the TRIM_EACH_SIDE slowest and fastest are dropped,
#     symmetrically, so interference (slow) and prompt-cache hits (fast) are
#     treated alike and nobody chooses which tail to keep;
#   * mean/std describe what is left ("trimmed"); median/sd describe the whole
#     post-warm-up sample, so the ± in the tables is the raw spread and the
#     median is an untuned check on the trimmed mean.
# With --runs 15 that is 1 + (2 + 10 + 2).
MIN_RUNS = 15
WARMUP_RUNS = 1
TRIM_EACH_SIDE = 2


class ShortSampleError(RuntimeError):
    """A result file carries fewer than MIN_RUNS values for a metric.

    At run time this means llama-benchy dropped requests (a transient failure,
    so it is retried like any other failure); for cached files it means the
    file predates the rule and is simply not reported.
    """


def _pop_mean_std(values: list[float]) -> tuple[float, float]:
    """Population mean and std (divide by N), matching llama-benchy."""
    n = len(values)
    mean = sum(values) / n
    return mean, math.sqrt(sum((v - mean) ** 2 for v in values) / n)


def aggregate_values(metric: dict, what: str) -> dict:
    """Apply the aggregation rule above to one metric's per-run values."""
    values = metric.get("values") or []
    if len(values) < MIN_RUNS:
        raise ShortSampleError(
            f"{what}: {len(values)} runs, the aggregation rule needs at least "
            f"{MIN_RUNS} (benchy_cmd --runs)"
        )
    sample = values[WARMUP_RUNS:]
    ordered = sorted(sample)
    kept = ordered[TRIM_EACH_SIDE:len(ordered) - TRIM_EACH_SIDE]
    mean, std = _pop_mean_std(kept)
    _, sd = _pop_mean_std(sample)
    return {
        "mean": mean, "std": std, "n": len(kept),
        "median": statistics.median(sample), "sd": sd, "n_all": len(sample),
        "trimmed_low": ordered[:TRIM_EACH_SIDE],
        "trimmed_high": ordered[len(ordered) - TRIM_EACH_SIDE:],
        "kept": kept, "sample": sample,
    }


def extract_run_metrics(bench_result: dict, pp: int, tg: int) -> dict:
    """Extract metrics for the matching (pp, tg) cell of a llama-benchy result.

    Raises NoMetricsError when the cell is absent or carries no measurement.
    """
    target = None
    for bench in bench_result.get("benchmarks", []):
        if (bench["concurrency"] == 1
                and bench["prompt_size"] == pp
                and bench["response_size"] == tg):
            target = bench
            break

    if target is None:
        raise NoMetricsError(
            f"result file has no concurrency=1 benchmark for pp={pp} tg={tg}"
        )

    # A key present with a null value is the common shape here, so `in` is not
    # enough -- that check is what previously produced a TypeError instead of
    # the server's actual complaint.
    null_metrics = [k for k in REPORTED_METRICS if target.get(k) is None]
    if any(target.get(k) is None for k in CORE_METRICS):
        raise NoMetricsError(
            f"llama-benchy returned no measurement for pp={pp} tg={tg} "
            f"(null: {', '.join(null_metrics)}) -- the server accepted the run "
            f"but produced no data; check the server log for this cell"
        )

    metrics = {}
    for key in REPORTED_METRICS:
        value = target.get(key)
        if value is None:
            logger.warning("  no %s for pp=%d tg=%d; reporting the rest", key, pp, tg)
            continue
        metrics[key] = aggregate_values(value, f"{key} pp={pp} tg={tg}")
    return metrics


# ===================== REPORTING =====================


def generate_json_report(runs: list[dict], config: dict, out_path: Path) -> None:
    """Write the machine-readable JSON report."""
    successful = sum(1 for r in runs if r["status"] == "success")
    failed = sum(1 for r in runs if r["status"] != "success")
    exp_id = runs[0]["experiment_id"] if runs else ""

    report = {
        "experiment_id": exp_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "runs": runs,
        "summary": {
            "total_runs": len(runs),
            "successful": successful,
            "failed": failed,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("JSON report: %s", out_path)


def _fmt_num(x: float) -> str:
    return f"{x:.0f}" if abs(x) >= 100 else f"{x:.1f}"


def _fmt_stat(metric: dict | None) -> str:
    """Render one metric as `trimmed mean ± sd of the whole sample`."""
    if not metric or metric.get("mean") is None:
        return "—"
    sd = metric.get("sd")
    if sd is None:
        return _fmt_num(metric["mean"])
    return f"{_fmt_num(metric['mean'])} ± {sd:.1f}" if sd < 10 else f"{_fmt_num(metric['mean'])} ± {sd:.0f}"


def _fmt_median(metric: dict | None) -> str:
    if not metric or metric.get("median") is None:
        return "—"
    return _fmt_num(metric["median"])


def pool_stats(stats: list[dict | None]) -> dict | None:
    """Combine cells into one figure by concatenating their samples.

    Used to report one prefill figure per prompt size instead of one per tg:
    prefill happens before any token is generated, so tg cannot affect it, and
    pooling the two cells just doubles the sample.

    Each cell has already been trimmed on its own, so the pooled trimmed mean is
    the mean of both cells' kept runs and a noisy cell cannot shed its outliers
    into the other cell's tail. Median and sd come from both cells' full
    post-warm-up samples, exactly as for a single cell.
    """
    usable = [x for x in stats if x and x.get("mean") is not None]
    if not usable:
        return None
    if len(usable) == 1:
        return usable[0]
    kept = [v for x in usable for v in x["kept"]]
    sample = [v for x in usable for v in x["sample"]]
    mean, std = _pop_mean_std(kept)
    _, sd = _pop_mean_std(sample)
    return {
        "mean": mean, "std": std, "n": len(kept),
        "median": statistics.median(sample), "sd": sd, "n_all": len(sample),
        "trimmed_low": sorted(v for x in usable for v in x["trimmed_low"]),
        "trimmed_high": sorted(v for x in usable for v in x["trimmed_high"]),
        "kept": kept, "sample": sample,
    }


def generate_summary_tables(runs: list[dict]) -> list[str]:
    """One table per prompt size: pooled prefill, then generation per tg.

    Every figure is shown twice: the trimmed mean ± sd, and the median of the
    same sample next to it. The two agree on a clean cell; where they don't,
    the "Trimmed runs" section says which runs pulled them apart.

    Both tg columns are kept deliberately: with speculative decoding, generation
    speed depends on how many tokens the draft can amortise over, so tg=32 and
    tg=64 are different measurements.
    """
    pps = sorted({r["pp"] for r in runs})
    tgs = sorted({r["tg"] for r in runs})
    if not pps or not tgs:
        return []

    servers = sorted({r["server"] for r in runs})
    cells = {(r["server"], r["pp"], r["tg"]): (r.get("metrics") or {}) for r in runs}

    lines = [
        "\n## Results by prompt size\n",
        "Throughput in tokens/s. Each cell is the **trimmed mean ± sd**: per cell "
        f"the first run is dropped as warm-up, then the {TRIM_EACH_SIDE} slowest "
        f"and {TRIM_EACH_SIDE} fastest of the rest; the mean is of the runs that "
        "remain, the ± is the standard deviation of *all* post-warm-up runs, so "
        "it shows the raw spread. **med** is the median of the same runs -- an "
        "untuned check that should match the trimmed mean within about a percent. "
        "**PP** is pooled across the tg runs (prefill completes before generation "
        "starts, so tg cannot affect it). **TG** is listed per tg because "
        "speculative decoding makes it depend on output length.\n",
    ]

    tg_headers = " | ".join(f"TG tg={tg} | med" for tg in tgs)
    tg_rule = "|".join(["--------|-----"] * len(tgs))

    for pp in pps:
        lines.append(f"\n### pp={pp}\n")
        lines.append(f"| Server | PP | med | {tg_headers} |")
        lines.append(f"|--------|----|-----|{tg_rule}|")
        for server in servers:
            pp_pooled = pool_stats([cells.get((server, pp, tg), {}).get("pp_throughput")
                                    for tg in tgs])
            row = [server, _fmt_stat(pp_pooled), _fmt_median(pp_pooled)]
            for tg in tgs:
                m = cells.get((server, pp, tg), {}).get("tg_throughput")
                row += [_fmt_stat(m), _fmt_median(m)]
            lines.append("| " + " | ".join(row) + " |")

    return lines


# Discarded runs are listed when they sit further than this from their cell's
# trimmed mean: closer than that they are ordinary spread, not interference.
TRIM_REPORT_PCT = 5.0


def generate_trim_table(runs: list[dict]) -> list[str]:
    """List the runs the symmetric trim discarded, where they were far off.

    A large negative deviation is interference (something else had the machine
    while that run was measured); a large positive one on PP is typically a
    prompt-cache hit. Lopsided counts across servers mean the machine, not the
    servers, is being compared -- fix that before publishing.
    """
    rows = []
    for run in runs:
        if run["status"] != "success":
            continue
        for key in CORE_METRICS:
            m = (run.get("metrics") or {}).get(key)
            if not m or not m.get("mean"):
                continue
            devs_low = [(v / m["mean"] - 1) * 100 for v in m.get("trimmed_low", [])]
            devs_high = [(v / m["mean"] - 1) * 100 for v in m.get("trimmed_high", [])]
            worst = max((abs(d) for d in devs_low + devs_high), default=0.0)
            if worst > TRIM_REPORT_PCT:
                rows.append((-worst, run["server"], run["pp"], run["tg"], key, devs_low, devs_high))

    lines = [
        "\n## Trimmed runs\n",
        f"Runs discarded by the symmetric trim, as % deviation from the cell's "
        f"trimmed mean; only cells where a discarded run is more than "
        f"{TRIM_REPORT_PCT:.0f}% off are listed.\n",
    ]
    if not rows:
        lines.append(f"All discarded runs were within {TRIM_REPORT_PCT:.0f}% of "
                     "their cell's trimmed mean.\n")
        return lines
    lines.append("| Server | pp | tg | Metric | Slowest discarded | Fastest discarded |")
    lines.append("|--------|----|----|--------|-------------------|-------------------|")
    for _, server, pp, tg, key, lows, highs in sorted(rows):
        fmt = lambda ds: ", ".join(f"{d:+.1f}%" for d in ds)
        lines.append(f"| {server} | {pp} | {tg} | {key} | {fmt(lows)} | {fmt(highs)} |")
    return lines


DETAIL_METRICS = {
    "pp_throughput": "PP Throughput (tokens/s)",
    "tg_throughput": "TG Throughput (tokens/s)",
    "ttfr": "TTFR (ms)",
}


def generate_detail_tables(runs: list[dict]) -> list[str]:
    """One table per (pp, tg) per metric -- nothing pooled, nothing dropped.

    Verbose (metrics × pp × tg tables) but it is the only view that reports
    every cell separately and the only one covering TTFR.
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for run in runs:
        if run["status"] == "success":
            groups[(run["pp"], run["tg"])].append(run)

    lines = []
    for (pp, tg), group in sorted(groups.items()):
        servers = sorted(set(r["server"] for r in group))
        for metric_key, metric_label in DETAIL_METRICS.items():
            lines.append(f"\n## {metric_label} — pp={pp}, tg={tg}\n")
            lines.append("| Server | Trimmed mean | Std (trimmed) | Median | Sd (all) | n kept / all |")
            lines.append("|--------|--------------|---------------|--------|----------|--------------|")
            server_runs = sorted(group, key=lambda r: servers.index(r["server"]))
            for run in server_runs:
                m = (run.get("metrics") or {}).get(metric_key)
                if m and m.get("mean") is not None:
                    lines.append(f"| {run['server']} | {m['mean']:.1f} | {m['std']:.2f} | "
                                 f"{m['median']:.1f} | {m['sd']:.2f} | {m['n']} / {m['n_all']} |")
                else:
                    lines.append(f"| {run['server']} | N/A | N/A | N/A | N/A | N/A |")
    return lines


def generate_md_report(runs: list[dict], out_path: Path,
                       tables: str = "aggregated") -> None:
    """Write the human-readable markdown report.

    `tables` selects the view: "aggregated" (one table per prompt size, prefill
    pooled across tg), "granular" (every pp/tg cell and metric separately, incl.
    TTFR), or "both".
    """
    if not runs:
        return

    exp_id = runs[0]["experiment_id"]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"# Benchmark Report: {exp_id}\n"]
    successful = [r for r in runs if r["status"] == "success"]
    if tables in ("aggregated", "both"):
        lines += generate_summary_tables(successful)
    if tables in ("granular", "both"):
        lines += generate_detail_tables(runs)
    # Always: the discarded runs are the audit trail for the trimmed means.
    lines += generate_trim_table(successful)

    # A table of successes alone can't be read safely -- a missing row looks
    # identical to a row that was never attempted. Spell out everything that
    # did not produce a measurement.
    problems = [r for r in runs if r["status"] != "success"]
    if problems:
        lines.append(f"\n## Runs without a measurement ({len(problems)})\n")
        lines.append("These cells have no result and must be re-run after fixing the cause.\n")
        lines.append("| Server | pp | tg | Status | Detail |")
        lines.append("|--------|----|----|--------|--------|")
        for r in sorted(problems, key=lambda r: (r["server"], r["pp"], r["tg"])):
            detail = (r.get("error") or "").replace("\n", " ").replace("|", "\\|")
            if len(detail) > 160:
                detail = detail[:157] + "..."
            lines.append(f"| {r['server']} | {r['pp']} | {r['tg']} | "
                         f"{r['status']} | {detail} |")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    logger.info("Markdown report: %s", out_path)


# ===================== MAIN =====================


def main():
    parser = argparse.ArgumentParser(description="exp-benchy runner")
    parser.add_argument("--config", type=Path, default=Path("experiments.yaml"),
                        help="Path to experiments YAML")
    parser.add_argument("--experiment", type=str, default=None,
                        help="Run only this experiment id (default: all)")
    parser.add_argument("--server", type=str, default=None,
                        help="Run only this server (e.g. llamafile)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print expanded run list without executing")
    parser.add_argument("--resume", action="store_true",
                        help="Skip runs that already have a result file")
    parser.add_argument("--retries", type=int, default=0,
                        help="Retry failed runs N times (default: 0)")
    parser.add_argument("--report", type=str, default="both", choices=["json", "md", "both"],
                        help="Report format (default: both)")
    parser.add_argument("--tables", type=str, default="aggregated",
                        choices=["aggregated", "granular", "both"],
                        help="Markdown table style: 'aggregated' = one table per "
                             "prompt size with prefill pooled across tg (default); "
                             "'granular' = every pp/tg cell and metric separately, "
                             "including TTFR; 'both' = one after the other")
    parser.add_argument("--report-only", action="store_true",
                        help="Skip server/benchmark runs; regenerate reports from cached results")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    config = load_config(args.config)
    results_dir = Path(config.get("results_dir", "./results"))
    benchy_template = config["benchy_cmd"]
    vars = config.get("vars", {})

    # The aggregation rule needs MIN_RUNS values per cell. Refuse a matrix that
    # cannot produce them, before it spends hours producing cells with no result.
    runs_flag = re.search(r"--runs\s+(\d+)", benchy_template)
    if not runs_flag or int(runs_flag.group(1)) < MIN_RUNS:
        logger.error("benchy_cmd must pass --runs N with N >= %d (found %s): the "
                     "aggregation drops %d warm-up run and %d+%d trimmed runs per cell.",
                     MIN_RUNS, runs_flag.group(1) if runs_flag else "none",
                     WARMUP_RUNS, TRIM_EACH_SIDE, TRIM_EACH_SIDE)
        sys.exit(1)

    # Expand all runs
    runs = expand_experiments(config, results_dir)

    # Filter by experiment id
    if args.experiment:
        runs = [r for r in runs if r.experiment_id == args.experiment]
    # Filter by server
    if args.server:
        runs = [r for r in runs if r.server_key == args.server]

    # In report-only mode an empty filter is fine — we still walk the full
    # config expansion below and report on whichever expected runs are cached.
    if not runs and not args.report_only:
        logger.error("No runs to execute!")
        sys.exit(1)

    # Dry-run mode
    if args.dry_run:
        for i, run in enumerate(runs, 1):
            print(f"[{i}/{len(runs)}] {run.server_key} {run.model_name} "
                  f"pp={run.pp} tg={run.tg} → {run.result_file}")
            print(f"  model={run.model}")
            print(f"  served_model_name={run.served_model_name}")
            print(f"  label={run.label}")
            start_cmd = _expand_template(
                run.server_config["start_cmd"], vars,
                model=run.model, served_model_name=run.served_model_name,
            )
            if args.verbose:
                print(f"  START:\n{start_cmd}")
            else:
                print(f"  START: {start_cmd.splitlines()[0]} ...")
            cmd = render_benchy_cmd(benchy_template, run)
            if args.verbose:
                print(f"  BENCH:\n{cmd}")
            else:
                print(f"  BENCH: {cmd.splitlines()[0]} ...")
        print(f"\nTotal: {len(runs)} runs")
        return

    # Create results dir
    results_dir.mkdir(parents=True, exist_ok=True)

    # Preflight the whole matrix before touching any server. Skipped for
    # --report-only, which starts nothing. Runs already cached under --resume
    # are excluded too: their ports and model files are irrelevant because
    # they will never be started.
    if not args.report_only:
        to_check = [r for r in runs if not (args.resume and r.result_file.exists())]
        if to_check:
            run_preflight(to_check, vars)

    # Group runs by experiment
    exp_groups: dict[str, list[Run]] = defaultdict(list)
    for run in runs:
        exp_groups[run.experiment_id].append(run)

    # ---- Load all cached results (from ALL runs, even outside --server filter) ----
    # This is key: reports always aggregate everything cached on disk.
    all_cached: dict[str, dict] = {}
    for run in expand_experiments(config, results_dir):  # full unfiltered set
        if run.result_file.exists():
            try:
                with open(run.result_file) as f:
                    bench_result = json.load(f)
                metrics = extract_run_metrics(bench_result, run.pp, run.tg)
                all_cached[str(run.result_file)] = {
                    "experiment_id": run.experiment_id,
                    "server": run.server_key,
                    "model": run.model_name,
                    "label": run.label,
                    "pp": run.pp,
                    "tg": run.tg,
                    "status": "success",
                    "result_file": str(run.result_file),
                    "metrics": metrics,
                }
            except Exception as e:
                logger.warning("[cached] Failed to load %s: %s", run.result_file, e)

    # Report-only mode: regenerate reports from cached results without running anything
    if args.report_only:
        all_results = sorted(all_cached.values(),
                             key=lambda r: (r["experiment_id"], r["server"], r["pp"], r["tg"]))
        _generate_reports(all_results, args, config)
        successful = sum(1 for r in all_results if r["status"] == "success")
        logger.info("=" * 60)
        logger.info("Done! %d cached runs reported (report-only mode)", successful)
        return

    # ---- Execute runs ----
    all_results: list[dict] = []
    total_count = 0
    # (server, model) pairs whose remaining cells are abandoned because a cell
    # came back with no measurement. Scoped this way -- not to the whole
    # invocation -- because the shared configuration is per server+model, while
    # other servers in the matrix are unaffected and expensive to redo.
    abandoned: dict[tuple[str, str], str] = {}

    def record(run: Run, status: str, **extra) -> dict:
        entry = {
            "experiment_id": run.experiment_id,
            "server": run.server_key,
            "model": run.model_name,
            "label": run.label,
            "pp": run.pp,
            "tg": run.tg,
            "status": status,
            "result_file": str(run.result_file),
            "metrics": {},
            **extra,
        }
        all_results.append(entry)
        return entry

    for exp_id, group in exp_groups.items():
        logger.info("=" * 60)
        logger.info("Experiment: %s (%d runs)", exp_id, len(group))
        logger.info("=" * 60)

        for run in group:
            total_count += 1
            label = f"{run.server_key} {run.model_name} pp={run.pp} tg={run.tg}"
            cached_key = str(run.result_file)
            scope = (run.server_key, run.model_name)

            if scope in abandoned:
                logger.warning("[%d/%d] %s — SKIPPED (%s)",
                               total_count, len(runs), label, abandoned[scope])
                record(run, "skipped", error=f"not attempted: {abandoned[scope]}")
                continue

            if args.resume and cached_key in all_cached:
                logger.info("[%d/%d] %s — SKIP (resumed)", total_count, len(runs), label)
                all_results.append(all_cached[cached_key])
                continue

            # Run with retries. NoMetricsError is deliberately outside that loop:
            # it is deterministic, so a retry only burns time.
            success = False
            error_msg = ""
            max_attempts = 1 + args.retries
            for attempt in range(max_attempts):
                if attempt > 0:
                    logger.info("[%s] Retry %d/%d", label, attempt, args.retries)
                try:
                    bench_result = run_server_lifecycle(
                        run, benchy_template, vars, results_dir)
                    metrics = extract_run_metrics(bench_result, run.pp, run.tg)
                    run_dict = record(run, "success", metrics=metrics)
                    all_cached[cached_key] = run_dict
                    clear_quarantine(run.result_file)
                    logger.info("[%d/%d] %s ✓", total_count, len(runs), label)
                    success = True
                    break
                except NoMetricsError as e:
                    error_msg = str(e)
                    logger.error("[%d/%d] %s ✗ NO METRICS: %s",
                                 total_count, len(runs), label, error_msg)
                    # Keep the raw output for inspection, but not under a name
                    # that reads as a result -- so nothing mistakes this cell
                    # for done, here or on a later --resume.
                    void_file = quarantine_result(run.result_file)
                    record(run, "no_metrics", error=error_msg,
                           void_result_file=str(void_file) if void_file else None)
                    abandoned[scope] = (
                        f"'{run.server_key}' produced no metrics at pp={run.pp} "
                        f"tg={run.tg}; remaining cells for this server+model skipped"
                    )
                    logger.error("[%s] Abandoning remaining cells for %s / %s",
                                 label, run.server_key, run.model_name)
                    success = True  # recorded already; skip the generic path
                    break
                except Exception as e:
                    error_msg = str(e)
                    logger.error("[%d/%d] %s ✗ %s", total_count, len(runs), label, error_msg)

            if not success:
                record(run, "failed", error=error_msg)

    # ---- Merge: include cached results from servers NOT in this invocation ----
    # (so reports are always complete even when using --server filter)
    for key, cached_run in all_cached.items():
        if key not in [r["result_file"] for r in all_results]:
            all_results.append(cached_run)

    # ---- Generate reports (always after ALL runs complete) ----
    _generate_reports(all_results, args, config)

    # Final summary
    by_status: dict[str, int] = defaultdict(int)
    for r in all_results:
        by_status[r["status"]] += 1
    successful = by_status["success"]
    incomplete = len(all_results) - successful

    logger.info("=" * 60)
    logger.info("Done! %d/%d successful", successful, len(all_results))
    if incomplete:
        for status in sorted(k for k in by_status if k != "success"):
            logger.error("  %s: %d", status, by_status[status])
        logger.error("EXPERIMENT INCOMPLETE — %d of %d cells have no result. "
                     "Fix the cause above and re-run (--resume keeps the good cells).",
                     incomplete, len(all_results))
        sys.exit(1)


def _generate_reports(all_results: list[dict], args, config: dict) -> None:
    """Generate reports for each experiment from a list of run result dicts."""
    report_dir = Path("report")
    exp_ids = sorted(set(r["experiment_id"] for r in all_results))
    for exp_id in exp_ids:
        exp_results = [r for r in all_results if r["experiment_id"] == exp_id]
        if args.report in ("json", "both"):
            generate_json_report(exp_results, config, report_dir / f"{exp_id}.json")
        if args.report in ("md", "both"):
            generate_md_report(exp_results, report_dir / f"{exp_id}.md", args.tables)


if __name__ == "__main__":
    main()

