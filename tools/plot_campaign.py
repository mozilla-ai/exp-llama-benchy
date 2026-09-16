#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.8", "pyyaml>=6"]
# ///
"""Plot one benchmark campaign: prompt processing and token generation per
prompt length, one column per experiment, one line per server.

Reads the raw llama-benchy result files of a campaign (or, with --source
server, the per-request server-side timings written by tools/server_timings.py)
and aggregates them with exactly the rule run.py uses for the reports: first run
dropped as warm-up, 2 slowest + 2 fastest of the rest discarded, mean of what
remains; error bars are +-1 SD of all post-warm-up runs.

usage:
  uv run tools/plot_campaign.py data/20260910-l40s --title "Linux / NVIDIA L40S"
  uv run tools/plot_campaign.py data/20260910-m4max --pp-source client --tg-source server   # recommended
  uv run tools/plot_campaign.py data/20260910-steamdeck --experiments qwen3.5-0.8b-all-servers qwen3.5-9b-all-servers
  uv run tools/plot_campaign.py data/20260910-m4max --tg-source-for lm-studio=server \
      --experiments qwen3.5-0.8b-all-servers qwen3.5-9b-all-servers qwen3.8-27b-mtp --out data/plots/m4max.png --csv data/plots/m4max.csv

Output: <campaign>/plots/<campaign>-<sources>-tg<tg>.png (and .svg with --svg), or --out;
--csv also writes every plotted point (experiment, server, pp, metric, source, mean, sd, median, n).
"""
import argparse, csv, glob, json, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # run.py (aggregation rule)
sys.path.insert(0, HERE)                    # server_timings.py (file-name parsing)
import run as runner                        # noqa: E402
import server_timings as st                 # noqa: E402

import matplotlib                           # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt             # noqa: E402
from matplotlib.ticker import FuncFormatter # noqa: E402

# Series identity is fixed: same hue, marker and legend slot on every figure,
# whatever subset of servers a panel has. Palette validated (light surface):
# lightness band, chroma floor, CVD and normal-vision separation, 3:1 contrast.
SERIES = [  # (display name, colour, marker), in legend order
    ("llama.cpp", "#80380F", "o"),
    ("llamafile", "#D06A15", "s"),
    ("LM Studio", "#2F6DB5", "^"),
    ("Ollama",    "#9C7A1E", "D"),
]
STYLE = {name: (c, m) for name, c, m in SERIES}
BASE_SERVER = {"llama-cpp": "llama.cpp", "llama-cpp-mtp": "llama.cpp", "llama-cpp-mtp4": "llama.cpp",
               "llama-cpp-idot": "llama.cpp",
               "llamafile": "llamafile", "llamafile-mtp": "llamafile", "llamafile-mtp4": "llamafile",
               "lm-studio": "LM Studio", "ollama": "Ollama", "ollama-mtp": "Ollama", "ollama-mtp4": "Ollama"}

INK, INK2, GRID = "#1f1f1f", "#5a5a5a", "#e3e3e0"


def experiment_title(exp_id: str) -> str:
    m = re.match(r"qwen(\d\.\d)-(\d+(?:\.\d+)?b)(?:-(.*))?", exp_id)
    if not m:
        return exp_id
    title = f"Qwen{m.group(1)} {m.group(2).upper()}"
    if m.group(3) and "mtp" in m.group(3):
        title += "  ·  MTP on"
        n = re.search(r"mtp(\d+)", m.group(3))      # qwen3.8-27b-mtp4 -> draft length in the title
        if n:
            title += f", draft {n.group(1)}"
    return title


def experiment_order(exp_id: str):
    m = re.match(r"qwen(\d\.\d)-(\d+(?:\.\d+)?)b(?:-(.*))?", exp_id)
    size = float(m.group(2)) if m else 1e9
    return (size, 1 if (m and m.group(3) and "mtp" in m.group(3)) else 0, exp_id)


def load_client(results_dir: str) -> dict:
    """{(exp, server, pp, tg): {"pp": metric, "tg": metric}} from llama-benchy files."""
    cells = {}
    for f in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        m = st.RE_RESULT.match(os.path.basename(f))
        if not m:
            continue
        b = json.load(open(f))["benchmarks"][0]
        key = (m["exp"], st.SUFFIX_TO_SERVER[m["suffix"]], int(m["pp"]), int(m["tg"]))
        try:
            cells[key] = {"pp": runner.aggregate_values(b["pp_throughput"], f"{f} pp"),
                          "tg": runner.aggregate_values(b["tg_throughput"], f"{f} tg")}
        except runner.ShortSampleError as e:
            print(f"skip {os.path.basename(f)}: {e}", file=sys.stderr)
    return cells


def load_server(results_dir: str, csv_path: str) -> dict:
    """Same shape as load_client, from tools/server_timings.py's per-request CSV.
    The CSV has no experiment id, so cells are mapped back through the result
    files present in results_dir (which fixes which experiment a server+model
    cell belongs to)."""
    exp_of = {}
    for f in glob.glob(os.path.join(results_dir, "*.json")):
        m = st.RE_RESULT.match(os.path.basename(f))
        if m:
            exp_of[(st.SUFFIX_TO_SERVER[m["suffix"]], m["model"], int(m["pp"]), int(m["tg"]))] = m["exp"]
    runs = defaultdict(list)
    for r in csv.DictReader(open(csv_path)):
        runs[(r["server"], r["model"], int(r["pp"]), int(r["tg"]))].append(
            (int(r["run"]), float(r["server_pp_tps"]), float(r["server_tg_tps"])))
    cells = {}
    for k, rows in runs.items():
        exp = exp_of.get(k)
        if exp is None:
            continue
        rows.sort()
        try:
            cells[(exp, k[0], k[2], k[3])] = {
                "pp": runner.aggregate_values({"values": [r[1] for r in rows]}, f"{k} pp"),
                "tg": runner.aggregate_values({"values": [r[2] for r in rows]}, f"{k} tg")}
        except runner.ShortSampleError as e:
            print(f"skip {k}: {e}", file=sys.stderr)
    return cells


def default_title(campaign: str) -> str:
    info = os.path.join(campaign, "host-info.txt")
    if os.path.exists(info):
        txt = open(info).read()
        gpu = re.search(r"^gpu: ([^,\n]+)", txt, re.M)
        mach = re.search(r"^machine: .*?Chip: ([^;]+)", txt, re.M)
        osl = re.search(r"^os: (\S+)", txt, re.M)
        if gpu:
            return f"{osl.group(1) if osl else 'Linux'} / {gpu.group(1).strip()}"
        if mach:
            return f"macOS / {mach.group(1).strip()}"
    return os.path.basename(os.path.normpath(campaign))


def thousands(x, _pos):
    """Thousands separators without forcing integers: 23,500 / 105 / 36.5."""
    return f"{x:,.10g}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campaign", help="campaign directory (with results/) or a results directory")
    ap.add_argument("--title", help="figure title (default: from host-info.txt or the directory name)")
    ap.add_argument("--tg", type=int, default=64, help="tg size for the token-generation row (default 64)")
    ap.add_argument("--source", choices=["client", "server"], default="client",
                    help="default source for both rows: client = llama-benchy measurements; "
                         "server = engine print_timing via server-timings.csv")
    ap.add_argument("--pp-source", choices=["client", "server"], help="source for the prompt-processing row (default: --source)")
    ap.add_argument("--tg-source", choices=["client", "server"],
                    help="source for the token-generation row (default: --source). Recommended: --pp-source client "
                         "--tg-source server -- what the user waits for on top, what the engine produces below")
    ap.add_argument("--pp-source-for", action="append", default=[], metavar="SERVER=SOURCE",
                    help="override the prompt-processing source for one server (e.g. lm-studio=server); repeatable")
    ap.add_argument("--tg-source-for", action="append", default=[], metavar="SERVER=SOURCE",
                    help="override the token-generation source for one server (e.g. lm-studio=server); repeatable. "
                         "For the case where one server's client-side measurement is known to be wrong "
                         "(LM Studio on macOS releases the stream in bursts, inflating client-side decode)")
    ap.add_argument("--experiments", nargs="*", help="experiment ids to plot, in this order (default: all, by model size)")
    ap.add_argument("--csv", help="also write the plotted points (mean, sd, median, n per cell and metric) to this CSV")
    ap.add_argument("--direct-labels", action="store_true", help="label each line at its right end (legend is always drawn)")
    ap.add_argument("--out", help="output path (default <campaign>/plots/<name>.png)")
    ap.add_argument("--svg", action="store_true", help="also write an .svg next to the .png")
    args = ap.parse_args()

    campaign = args.campaign.rstrip("/")
    results_dir = campaign if glob.glob(os.path.join(campaign, "*.json")) else os.path.join(campaign, "results")
    src = {"pp": args.pp_source or args.source, "tg": args.tg_source or args.source}
    overrides = {"pp": {}, "tg": {}}
    for metric, specs in (("pp", args.pp_source_for), ("tg", args.tg_source_for)):
        for spec in specs:
            server, _, source = spec.partition("=")
            if source not in ("client", "server") or server not in BASE_SERVER:
                sys.exit(f"--{metric}-source-for expects <server>=client|server with server in {sorted(BASE_SERVER)}; got {spec!r}")
            overrides[metric][server] = source

    def source_of(metric, server):
        return overrides[metric].get(server, src[metric])

    loaded = {}
    for which in set(src.values()) | {v for o in overrides.values() for v in o.values()}:
        if which == "client":
            loaded[which] = load_client(results_dir)
        else:
            csv_path = os.path.join(campaign, "server-timings.csv")
            if not os.path.exists(csv_path):
                sys.exit(f"server-side data needs {csv_path} (run tools/server_timings.py first)")
            loaded[which] = load_server(results_dir, csv_path)
    # per-metric view: cells[(exp, server, pp, tg)] -> {"pp": ..., "tg": ...} taken from the row's source,
    # or from that server's override
    cells = {}
    for which, d in loaded.items():
        for k, v in d.items():
            for metric in ("pp", "tg"):
                if source_of(metric, k[1]) == which:
                    cells.setdefault(k, {})[metric] = v[metric]
    if not cells:
        sys.exit("no complete cells found")

    exps = args.experiments or sorted({k[0] for k in cells}, key=experiment_order)
    pps = sorted({k[2] for k in cells})
    title = args.title or default_title(campaign)
    n_all = max(m["n_all"] for v in cells.values() for m in v.values())
    n_kept = max(m["n"] for v in cells.values() for m in v.values())

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titleweight": "bold",
                         "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})
    ncol = len(exps)
    # Never narrower than two columns: the legend row and the caption need the width.
    fig_w = max(4.4 * ncol + 0.6, 9.4)
    fig, axes = plt.subplots(2, ncol, figsize=(fig_w, 7.6), squeeze=False)

    points = []   # rows for --csv
    for ci, exp in enumerate(exps):
        for ri, metric in enumerate(("pp", "tg")):
            ax = axes[ri][ci]
            servers = sorted({k[1] for k in cells if k[0] == exp}, key=lambda s: [n for n, _, _ in SERIES].index(BASE_SERVER[s]))
            for srv in servers:
                base = BASE_SERVER[srv]
                colour, marker = STYLE[base]
                xs, ys, es = [], [], []
                for xi, pp in enumerate(pps):
                    tgs = [args.tg] if metric == "tg" else sorted({k[3] for k in cells if k[:3] == (exp, srv, pp)})
                    if metric == "pp":
                        # prefill is pooled over the tg cells, as in the report
                        pooled = runner.pool_stats([cells.get((exp, srv, pp, tg), {}).get("pp") for tg in tgs])
                        m = pooled
                    else:
                        m = cells.get((exp, srv, pp, args.tg), {}).get("tg")
                    if m:
                        xs.append(xi); ys.append(m["mean"]); es.append(m["sd"])
                        points.append((exp, srv, pp, metric, source_of(metric, srv), m["mean"], m["sd"], m["median"], m["n"]))
                if not xs:
                    continue
                ax.errorbar(xs, ys, yerr=es, color=colour, marker=marker, markersize=7.5, linewidth=2,
                            markeredgecolor="white", markeredgewidth=1.2, capsize=3, elinewidth=1.2,
                            label=base, zorder=3)
                if args.direct_labels:
                    ax.annotate(base, (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                                fontsize=8.5, color=INK2, va="center")
            ax.set_xticks(range(len(pps)))
            ax.set_xticklabels([f"{pp:,}" for pp in pps])
            ax.set_xlim(-0.35, len(pps) - 0.65 + (0.9 if args.direct_labels else 0))
            ax.yaxis.set_major_formatter(FuncFormatter(thousands))
            ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
            ax.set_axisbelow(True)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            ax.margins(y=0.12)
            if ri == 0:
                ax.set_title(experiment_title(exp), pad=10)
            if ri == 1:
                ax.set_xlabel("Prompt length (tokens)")
            if ci == 0:
                ax.set_ylabel("Prompt processing (tokens/s)" if metric == "pp" else "Token generation (tokens/s)")

    # one shared legend, fixed order and identity regardless of which panels have which servers
    handles = {}
    for ax in axes.flat:
        for h, l in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(l, h)
    order = [n for n, _, _ in SERIES if n in handles]
    fig.legend([handles[n] for n in order], order, loc="upper center", ncol=len(order), frameon=False,
               bbox_to_anchor=(0.5, 0.94), fontsize=10.5, handlelength=2.2)
    fig.suptitle(title, fontsize=15, fontweight="bold", y=0.985)

    desc = {"client": "client-side (llama-benchy: prompt tokens over time to first token; streamed tokens over stream time)",
            "server": "server-side (the engine's own print_timing, via tools/server_timings.py)"}
    if src["pp"] == src["tg"]:
        source_txt = f"Source: {desc[src['pp']]}."
    else:
        source_txt = f"Sources: prompt processing {desc[src['pp']]}; token generation {desc[src['tg']]}."
    label = {"pp": "prompt processing", "tg": "token generation"}
    for metric in ("pp", "tg"):
        for server, source in overrides[metric].items():
            source_txt += f" Exception: {label[metric]} for {BASE_SERVER[server]} is {desc[source]}."
    caption = (f"Higher is better. Top row: prompt processing (pooled over tg runs). Bottom row: token generation at "
               f"{args.tg}-token output. Points are trimmed means of {n_all + 1} runs per cell (first run dropped as warm-up, "
               f"2 slowest and 2 fastest of the rest discarded, mean of the remaining {n_kept}); error bars are ±1 SD of all "
               f"{n_all} post-warm-up runs. {source_txt} y-axes scaled per panel, not from zero.")
    # Wrap the caption to the figure width and reserve exactly the room it needs.
    import textwrap
    wrapped = textwrap.fill(caption, width=int(fig_w * 12.5))   # ~12.5 chars/inch at 8.6 pt
    n_lines = wrapped.count("\n") + 1
    fig.text(0.5, 0.012, wrapped, ha="center", va="bottom", fontsize=8.6, color=INK2, linespacing=1.4)
    bottom = 0.012 + 0.0185 * n_lines + 0.02
    fig.tight_layout(rect=(0, bottom, 1, 0.9))

    tag = src["pp"] if src["pp"] == src["tg"] else f"pp{src['pp']}-tg{src['tg']}"
    for metric in ("pp", "tg"):
        for server, source in sorted(overrides[metric].items()):
            tag += f"-{server.replace('-', '')}-{metric}{source}"
    name = f"{os.path.basename(os.path.normpath(campaign))}-{tag}-tg{args.tg}"
    out = args.out or os.path.join(campaign, "plots", name + ".png")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    fig.savefig(out, dpi=200, facecolor="white")
    if args.svg:
        fig.savefig(os.path.splitext(out)[0] + ".svg", facecolor="white")
    print(out)
    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["experiment", "server", "pp", "metric", "source", "mean", "sd", "median", "n"])
            for row in points:
                w.writerow([*row[:5], f"{row[5]:.3f}", f"{row[6]:.3f}", f"{row[7]:.3f}", row[8]])
        print(args.csv)


if __name__ == "__main__":
    main()
