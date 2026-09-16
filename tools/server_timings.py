#!/usr/bin/env python3
"""Extract server-side timings for every benchmark cell and aggregate them with
the same rule run.py uses for the client-side numbers.

llama-benchy measures from the client: it timestamps the SSE chunks it receives.
Every server we benchmark embeds llama.cpp's server, which logs one
`print_timing` block per request -- prompt eval time and eval time as measured
inside the engine at the moment each token is sampled. This script attributes
those lines to the (server, model, pp, tg) cells of a results directory and
prints a table next to the client-side figures. Where a product batches its
HTTP output (LM Studio on macOS), the two disagree and the server-side one is
the decode speed.

Sources:
  * llamafile / llama.cpp: results/<server>_<model>_pp_<pp>_tg_<tg>.server.log,
    captured by run.py.
  * LM Studio: its server log(s) (~/.lmstudio/server-logs/YYYY-MM/*.log).
  * Ollama: a journal dump (`journalctl -u ollama -o short-iso` or `-o cat`) or
    the daemon log the runner redirects `ollama serve` to.

Attribution never relies on wall-clock time. A cell is one model load carrying
exactly `runs` requests whose eval token count equals the cell's tg and whose
prompt token count lies within [pp, pp + 200] (chat template overhead). Segments
are delimited by model-load lines. If more than one segment matches a cell
(the same cell run twice against the same log) the later one is used and a
warning is printed.

usage:
  tools/server_timings.py --results data/20260910-m4max/results \
      --lmstudio-log data/20260910-m4max/lmstudio-server-logs/2026-09-10.1.log \
      [--ollama-log data/20260910-l40s/ollama-journal.log] [--csv out.csv]
"""
import argparse, csv, glob, json, math, os, re, statistics, sys
from collections import defaultdict

# Same rule as run.py.
WARMUP_RUNS, TRIM_EACH_SIDE = 1, 2

RE_PROMPT = re.compile(r"prompt eval time = +([\d.]+) ms / +(\d+) tokens")
RE_EVAL = re.compile(r"(?<!prompt )eval time = +([\d.]+) ms / +(\d+) tokens")
RE_DRAFT = re.compile(r"draft acceptance = +([\d.]+) .*mean len = +([\d.]+)")
RE_LMS_LOAD = re.compile(r"Loading model: (\S+)")
RE_OLLAMA_START = re.compile(r"starting llama-server.*--model \S*sha256-([0-9a-f]{12})")
# experiment ids carry no underscore; model names do (Q4_K_M), so split on the
# first underscore and let the anchored suffix alternation find the model end.
RE_RESULT = re.compile(r"^(?P<exp>[^_]+)_(?P<model>.+)-(?P<suffix>llamafile-mtp4|llamacpp-mtp4|ollama-mtp4|llamafile-mtp|llamacpp-mtp|ollama-mtp|llamacpp-idot|llamafile|llamacpp|ollama|lmstudio)_pp(?P<pp>\d+)_tg(?P<tg>\d+)\.json$")

SUFFIX_TO_SERVER = {"llamafile": "llamafile", "llamacpp": "llama-cpp", "ollama": "ollama", "lmstudio": "lm-studio",
                    "llamafile-mtp": "llamafile-mtp", "llamacpp-mtp": "llama-cpp-mtp", "ollama-mtp": "ollama-mtp",
                    "llamafile-mtp4": "llamafile-mtp4", "llamacpp-mtp4": "llama-cpp-mtp4", "ollama-mtp4": "ollama-mtp4",
                    "llamacpp-idot": "llama-cpp-idot"}
# Ollama cells are matched to daemon-log segments by the draft length the runner
# passed (None = no speculative decoding). "ollama-mtp" accepts any draft length
# because campaigns before 2026-09-12 ran it with 4 and later ones with 2; when a
# log holds both, the -mtp4 cells take the 4s and -mtp gets what is left.
OLLAMA_DRAFT = {"ollama": None, "ollama-mtp": "any", "ollama-mtp4": 4}

# Ollama blob sha256 prefixes -> model name (the *-lms tags built from the LM
# Studio GGUFs, plus the library tags used in August).
DEFAULT_BLOBS = {"091d8deba394": "Qwen3.5-0.8B-Q8_0", "cd76ec205963": "Qwen3.5-9B-Q4_K_M", "e00082f779fa": "Qwen3.8-27B-Q4_K_M",
                 "afb707b6b8fa": "Qwen3.5-0.8B-Q8_0", "dec52a44569a": "Qwen3.5-9B-Q4_K_M", "f5f1dd8920d4": "Qwen3.8-27B-Q4_K_M"}


def model_key(name: str) -> str:
    """Normalise 'Qwen3.8-27B-Q4_K_M', 'qwen/qwen3.8-27b', 'Qwen3.8-27B-UD-Q4_K_XL' -> 'qwen3.8-27b'."""
    m = re.search(r"qwen(\d\.\d)[-_]?(\d+(?:\.\d+)?b)", name.lower())
    return f"qwen{m.group(1)}-{m.group(2)}" if m else name.lower()


def parse_requests(lines):
    """Pair prompt-eval / eval / draft lines into requests, in order."""
    reqs, cur = [], None
    for ln in lines:
        m = RE_PROMPT.search(ln)
        if m:
            cur = {"prompt_ms": float(m.group(1)), "prompt_tokens": int(m.group(2))}
            continue
        m = RE_EVAL.search(ln)
        if m and cur is not None and "eval_ms" not in cur:
            cur.update(eval_ms=float(m.group(1)), eval_tokens=int(m.group(2)))
            reqs.append(cur)
            continue
        m = RE_DRAFT.search(ln)
        if m and reqs and "acceptance" not in reqs[-1]:
            reqs[-1].update(acceptance=float(m.group(1)), draft_len=float(m.group(2)))
    return reqs


def segments_from_log(path, load_re, label_fn):
    """Split a server log into (label, requests) segments at model-load lines."""
    segs, label, buf = [], None, []
    for ln in open(path, errors="replace"):
        m = load_re.search(ln)
        if m:
            if label is not None:
                segs.append((label, parse_requests(buf)))
            label, buf = label_fn(m), []
        else:
            buf.append(ln)
    if label is not None:
        segs.append((label, parse_requests(buf)))
    return segs


def trimmed(values):
    sample = values[WARMUP_RUNS:]
    if len(sample) < 2 * TRIM_EACH_SIDE + 1:
        return None
    kept = sorted(sample)[TRIM_EACH_SIDE:len(sample) - TRIM_EACH_SIDE]
    return statistics.mean(kept), statistics.pstdev(sample), statistics.median(sample)


def client_stats(bench):
    b = bench["benchmarks"][0]
    return trimmed(b["pp_throughput"]["values"]), trimmed(b["tg_throughput"]["values"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True, help="results directory of one campaign")
    ap.add_argument("--lmstudio-log", nargs="+", action="extend", default=[], help="LM Studio server log (repeatable)")
    ap.add_argument("--ollama-log", nargs="+", action="extend", default=[], help="Ollama journal dump or daemon log (repeatable)")
    ap.add_argument("--blob", action="append", default=[], help="extra Ollama blob mapping sha12=ModelName")
    ap.add_argument("--csv", help="write per-request rows here")
    args = ap.parse_args()

    blobs = dict(DEFAULT_BLOBS)
    for b in args.blob:
        k, v = b.split("=", 1)
        blobs[k[:12]] = v

    # ---- cells from the result files ----
    cells = []
    for f in sorted(glob.glob(os.path.join(args.results, "*.json"))):
        m = RE_RESULT.match(os.path.basename(f))
        if not m:
            continue
        bench = json.load(open(f))
        cells.append({"server": SUFFIX_TO_SERVER[m["suffix"]], "model": m["model"], "pp": int(m["pp"]), "tg": int(m["tg"]),
                      "runs": len(bench["benchmarks"][0]["tg_throughput"]["values"]), "client": client_stats(bench), "file": f})

    # ---- server-side requests per cell ----
    def cell_matches(reqs, cell):
        if len(reqs) != cell["runs"]:
            return False
        # A request may stop early on EOS (fewer tokens than tg); never more.
        exact = sum(r["eval_tokens"] == cell["tg"] for r in reqs)
        if exact < 0.8 * len(reqs) or any(r["eval_tokens"] > cell["tg"] for r in reqs):
            return False
        pt = statistics.median(r["prompt_tokens"] for r in reqs)
        return cell["pp"] <= pt <= cell["pp"] + 200

    # llamafile / llama.cpp: one captured log per cell
    server_reqs = {}
    for c in cells:
        if c["server"] in ("llamafile", "llama-cpp", "llamafile-mtp", "llama-cpp-mtp", "llamafile-mtp4", "llama-cpp-mtp4"):
            log = os.path.join(args.results, f"{c['server']}_{c['model']}_pp_{c['pp']}_tg_{c['tg']}.server.log")
            if os.path.exists(log):
                server_reqs[id(c)] = parse_requests(open(log, errors="replace"))

    # LM Studio: segments by "Loading model:", labelled by model
    lms_segs = []
    for path in args.lmstudio_log:
        lms_segs += segments_from_log(path, RE_LMS_LOAD, lambda m: model_key(m.group(1)))
    # Ollama: segments by "starting llama-server", labelled by (model, draft length or None)
    oll_segs = []
    for path in args.ollama_log:
        def lab(m, _blobs=blobs):
            n = re.search(r"--spec-draft-n-max (\d+)", m.string)
            draft = int(n.group(1)) if n else (0 if "--spec-type" in m.string else None)
            return (model_key(_blobs.get(m.group(1), m.group(1))), draft)
        oll_segs += segments_from_log(path, RE_OLLAMA_START, lab)
    has_mtp4_cells = any(c["server"] == "ollama-mtp4" for c in cells)

    for c in cells:
        if c["server"] == "lm-studio":
            cands = [r for lab, r in lms_segs if lab == model_key(c["model"]) and cell_matches(r, c)]
        elif c["server"] in OLLAMA_DRAFT:
            want = OLLAMA_DRAFT[c["server"]]
            def draft_ok(d, want=want):
                if want == "any":
                    return d is not None and not (has_mtp4_cells and d == 4)
                return d == want
            cands = [r for lab, r in oll_segs if lab[0] == model_key(c["model"]) and draft_ok(lab[1]) and cell_matches(r, c)]
        else:
            continue
        if not cands:
            continue
        if len(cands) > 1:
            print(f"warning: {len(cands)} log segments match {c['server']} {c['model']} pp={c['pp']} tg={c['tg']}; using the last",
                  file=sys.stderr)
        server_reqs[id(c)] = cands[-1]

    # ---- report ----
    rows = []
    by_model = defaultdict(list)
    for c in cells:
        reqs = server_reqs.get(id(c))
        s_pp = trimmed([r["prompt_tokens"] / r["prompt_ms"] * 1000 for r in reqs]) if reqs else None
        s_tg = trimmed([r["eval_tokens"] / r["eval_ms"] * 1000 for r in reqs]) if reqs else None
        acc = statistics.mean(r["acceptance"] for r in reqs if "acceptance" in r) if reqs and any("acceptance" in r for r in reqs) else None
        by_model[c["model"]].append((c, s_pp, s_tg, acc, len(reqs) if reqs else 0))
        for i, r in enumerate(reqs or []):
            rows.append({"server": c["server"], "model": c["model"], "pp": c["pp"], "tg": c["tg"], "run": i,
                         "server_pp_tps": round(r["prompt_tokens"] / r["prompt_ms"] * 1000, 1), "server_tg_tps": round(r["eval_tokens"] / r["eval_ms"] * 1000, 2),
                         "prompt_tokens": r["prompt_tokens"], "eval_tokens": r["eval_tokens"], "acceptance": r.get("acceptance", ""), "draft_len": r.get("draft_len", "")})

    fmt = lambda t: "—" if t is None else (f"{t[0]:.0f}" if t[0] >= 100 else f"{t[0]:.1f}")
    for model, items in by_model.items():
        print(f"\n## {model}   (trimmed means; client = llama-benchy, server = print_timing)\n")
        print("| server | pp | tg | client pp | server pp | client tg | server tg | tg client/server | n server reqs | acceptance |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        for c, s_pp, s_tg, acc, n in sorted(items, key=lambda x: (x[0]["pp"], x[0]["tg"], x[0]["server"])):
            c_pp, c_tg = c["client"]
            ratio = f"{c_tg[0] / s_tg[0]:.2f}" if (c_tg and s_tg) else "—"
            print(f"| {c['server']} | {c['pp']} | {c['tg']} | {fmt(c_pp)} | {fmt(s_pp)} | {fmt(c_tg)} | {fmt(s_tg)} | {ratio} | {n} | {'' if acc is None else f'{acc:.2f}'} |")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["server"])
            w.writeheader(); w.writerows(rows)
        print(f"\n{len(rows)} per-request rows -> {args.csv}")


if __name__ == "__main__":
    main()
