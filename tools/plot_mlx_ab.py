#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.8", "pyyaml>=6"]
# ///
"""Plot the GGUF-vs-MLX comparison for the runtimes that ship both.

One column per runtime, prompt processing on top and token generation below,
two lines per panel: the shared GGUF the main campaign uses, and that runtime's
own MLX build. llama.cpp and llamafile are absent by design -- neither has an
MLX path, so putting them on the same axes would invite a comparison the figure
cannot support.

Aggregation is the campaign's: first run dropped as warm-up, 2 fastest and 2
slowest of the rest discarded, mean of the remaining; error bars are +-1 SD over
all post-warm-up runs.

usage:
  uv run tools/plot_mlx_ab.py --gguf data/20260912-m4max --mlx data/20260914-m4max-mlx \
      --title "Apple M4 Max: shared GGUF vs each runtime's own MLX build" \
      --out data/plots/mlx-ab.png --csv data/plots/mlx-ab.csv
"""
import argparse, csv, glob, json, os, re, sys, textwrap
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import run as runner                                    # noqa: E402
import matplotlib                                       # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                         # noqa: E402
from matplotlib.ticker import FuncFormatter             # noqa: E402

INK, INK2, GRID = "#1f1f1f", "#5a5a5a", "#e3e3e0"
# The comparison here is weights, not runtime, so the two hues encode GGUF vs MLX
# and stay clear of the four runtime colours the other figures use.
STYLE = {"GGUF": ("#5a5a5a", "o", "-", True), "MLX": ("#4a3aa7", "s", "--", False)}
RUNTIMES = [("ollama", "Ollama"), ("lmstudio", "LM Studio")]

RE = re.compile(r"_pp(?P<pp>\d+)_tg(?P<tg>\d+)\.json$")


def load(results_dir, suffixes):
    """{(runtime, pp, tg): {"pp": metric, "tg": metric}} for the given label suffixes."""
    out = {}
    for f in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        n = os.path.basename(f)
        if "no-metrics" in n or "collided" in n:
            continue
        m = RE.search(n)
        if not m:
            continue
        for suf, rt in suffixes.items():
            if f"-{suf}_" in n:
                break
        else:
            continue
        b = json.load(open(f))["benchmarks"][0]
        try:
            out[(rt, int(m["pp"]), int(m["tg"]))] = {
                "pp": runner.aggregate_values(b["pp_throughput"], f"{f} pp"),
                "tg": runner.aggregate_values(b["tg_throughput"], f"{f} tg")}
        except runner.ShortSampleError as e:
            print(f"skip {n}: {e}", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gguf", required=True, help="campaign dir holding the shared-GGUF 27B cells")
    ap.add_argument("--mlx", required=True, help="campaign dir holding the MLX cells")
    ap.add_argument("--tg", type=int, default=64)
    ap.add_argument("--title", default="Shared GGUF vs each runtime's own MLX build")
    ap.add_argument("--note", action="append", default=[], help="extra caption sentence (repeatable)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv")
    a = ap.parse_args()

    gguf = load(os.path.join(a.gguf, "results"), {"ollama-mtp": "ollama", "lmstudio": "lmstudio"})
    mlx  = load(os.path.join(a.mlx,  "results"), {"ollama": "ollama", "lmstudio": "lmstudio"})
    if not gguf or not mlx:
        sys.exit(f"missing cells: gguf={len(gguf)} mlx={len(mlx)}")
    pps = sorted({k[1] for k in gguf} & {k[1] for k in mlx})

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titleweight": "bold",
                         "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})
    fig, axes = plt.subplots(2, len(RUNTIMES), figsize=(9.8, 7.6), squeeze=False)
    rows = []
    for ci, (rt, rtlabel) in enumerate(RUNTIMES):
        for ri, metric in enumerate(("pp", "tg")):
            ax = axes[ri][ci]
            for wlabel, src in (("GGUF", gguf), ("MLX", mlx)):
                colour, marker, ls, filled = STYLE[wlabel]
                xs, ys, es = [], [], []
                for xi, pp in enumerate(pps):
                    if metric == "pp":
                        tgs = sorted({k[2] for k in src if k[0] == rt and k[1] == pp})
                        m = runner.pool_stats([src.get((rt, pp, tg), {}).get("pp") for tg in tgs])
                    else:
                        m = src.get((rt, pp, a.tg), {}).get("tg")
                    if m:
                        xs.append(xi); ys.append(m["mean"]); es.append(m["sd"])
                        rows.append((rtlabel, wlabel, pp, metric, m["mean"], m["sd"], m["median"], m["n"]))
                if not xs:
                    continue
                ax.errorbar(xs, ys, yerr=es, color=colour, marker=marker, markersize=7.5, linewidth=2,
                            linestyle=ls, markerfacecolor=(colour if filled else "white"),
                            markeredgecolor=colour, markeredgewidth=1.6, capsize=3, elinewidth=1.2,
                            label=wlabel, zorder=3)
            # per-panel gain annotation: MLX vs GGUF at the shortest prompt
            g = [r for r in rows if r[0] == rtlabel and r[3] == metric and r[2] == pps[0]]
            if len(g) == 2:
                by = {r[1]: r[4] for r in g}
                d = 100 * (by["MLX"] - by["GGUF"]) / by["GGUF"]
                ax.annotate(f"{d:+.0f}% at {pps[0]:,}", xy=(0.03, 0.94), xycoords="axes fraction",
                            fontsize=9, color=INK2, va="top")
            ax.set_xticks(range(len(pps))); ax.set_xticklabels([f"{p:,}" for p in pps])
            ax.set_xlim(-0.35, len(pps) - 0.65)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _p: f"{x:,.10g}"))
            ax.grid(True, color=GRID, linewidth=0.8, zorder=0); ax.set_axisbelow(True)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            ax.margins(y=0.16)
            if ri == 0: ax.set_title(rtlabel, pad=10)
            if ri == 1: ax.set_xlabel("Prompt length (tokens)")
            if ci == 0: ax.set_ylabel("Prompt processing (tokens/s)" if metric == "pp"
                                      else "Token generation (tokens/s)")

    handles = {}
    for ax in axes.flat:
        for h, l in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(l, h)
    order = [w for w in ("GGUF", "MLX") if w in handles]
    fig.legend([handles[w] for w in order], order, loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 0.94), fontsize=10.5, handlelength=2.6)
    fig.suptitle(a.title, fontsize=14, fontweight="bold", y=0.985)

    n_all = max(m["n_all"] for v in list(gguf.values()) + list(mlx.values()) for m in v.values())
    n_kept = max(m["n"] for v in list(gguf.values()) + list(mlx.values()) for m in v.values())
    caption = (f"Higher is better. Top row: prompt processing (pooled over tg runs). Bottom row: token generation at "
               f"{a.tg}-token output. Points are trimmed means of {n_all + 1} runs per cell (first run dropped as "
               f"warm-up, 2 slowest and 2 fastest of the rest discarded, mean of the remaining {n_kept}); error bars "
               f"are ±1 SD of all {n_all} post-warm-up runs. y-axes scaled per panel and per runtime, not from zero — "
               f"the two columns are NOT on a common scale and should not be read against each other.")
    for n in a.note:
        caption += " " + n.rstrip(".") + "."
    wrapped = textwrap.fill(caption, width=int(9.8 * 12.5))
    fig.text(0.5, 0.012, wrapped, ha="center", va="bottom", fontsize=8.6, color=INK2, linespacing=1.4)
    fig.tight_layout(rect=(0, 0.012 + 0.0185 * (wrapped.count("\n") + 1) + 0.02, 1, 0.9))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    fig.savefig(a.out, dpi=200, facecolor="white")
    print(a.out)
    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["runtime", "weights", "pp", "metric", "mean", "sd", "median", "n"])
            w.writerows(sorted(set(rows)))
        print(a.csv)


if __name__ == "__main__":
    main()
