#!/usr/bin/env python3
"""Compare two campaigns cell by cell to check that results reproduce.

For every (experiment, server, pp, tg) cell present in both campaigns, prints
the trimmed means (run.py's rule), the relative difference B vs A, and whether
the difference is within the combined run-to-run spread:

    |B - A|  <=  k * sqrt(SE_A^2 + SE_B^2),   SE = sd / sqrt(n_all)

with k = 3 by default. A cell outside that band is not automatically wrong --
the machine may have been warmer, or a runtime updated itself -- but it is
where to look. Cells for which one campaign lacks a result are listed at the end.

usage:
  tools/compare_campaigns.py data/20260910-l40s data/20260925-l40s [--source server] [--k 3] [--metric tg|pp|both]
"""
import argparse, csv, glob, json, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import run as runner          # noqa: E402
import server_timings as st   # noqa: E402


def load(campaign: str, source: str) -> dict:
    """{(exp, server, pp, tg): {"pp": metric, "tg": metric}}"""
    results_dir = campaign if glob.glob(os.path.join(campaign, "*.json")) else os.path.join(campaign, "results")
    cells = {}
    if source == "client":
        for f in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
            m = st.RE_RESULT.match(os.path.basename(f))
            if not m:
                continue
            b = json.load(open(f))["benchmarks"][0]
            try:
                cells[(m["exp"], st.SUFFIX_TO_SERVER[m["suffix"]], int(m["pp"]), int(m["tg"]))] = {
                    "pp": runner.aggregate_values(b["pp_throughput"], f), "tg": runner.aggregate_values(b["tg_throughput"], f)}
            except runner.ShortSampleError as e:
                print(f"skip {os.path.basename(f)}: {e}", file=sys.stderr)
        return cells
    csv_path = os.path.join(campaign, "server-timings.csv")
    if not os.path.exists(csv_path):
        sys.exit(f"{csv_path} missing (run tools/server_timings.py first)")
    exp_of = {}
    for f in glob.glob(os.path.join(results_dir, "*.json")):
        m = st.RE_RESULT.match(os.path.basename(f))
        if m:
            exp_of[(st.SUFFIX_TO_SERVER[m["suffix"]], m["model"], int(m["pp"]), int(m["tg"]))] = m["exp"]
    runs = defaultdict(list)
    for r in csv.DictReader(open(csv_path)):
        runs[(r["server"], r["model"], int(r["pp"]), int(r["tg"]))].append((int(r["run"]), float(r["server_pp_tps"]), float(r["server_tg_tps"])))
    for k, rows in runs.items():
        if k not in exp_of:
            continue
        rows.sort()
        try:
            cells[(exp_of[k], k[0], k[2], k[3])] = {"pp": runner.aggregate_values({"values": [r[1] for r in rows]}, str(k)),
                                                     "tg": runner.aggregate_values({"values": [r[2] for r in rows]}, str(k))}
        except runner.ShortSampleError as e:
            print(f"skip {k}: {e}", file=sys.stderr)
    return cells


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--source", choices=["client", "server"], default="client")
    ap.add_argument("--metric", choices=["pp", "tg", "both"], default="both")
    ap.add_argument("--k", type=float, default=3.0, help="band width in combined standard errors (default 3)")
    args = ap.parse_args()

    A, B = load(args.a, args.source), load(args.b, args.source)
    common = sorted(set(A) & set(B), key=lambda k: (k[0], k[2], k[3], k[1]))
    metrics = ["pp", "tg"] if args.metric == "both" else [args.metric]
    na, nb = os.path.basename(os.path.normpath(args.a)), os.path.basename(os.path.normpath(args.b))

    print(f"\n{len(common)} common cells, source={args.source}, band = ±{args.k:g} combined SE\n")
    print(f"| experiment | server | pp | tg | metric | {na} | {nb} | Δ | band | verdict |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    flagged, deltas = [], defaultdict(list)
    for key in common:
        for met in metrics:
            a, b = A[key][met], B[key][met]
            d = (b["mean"] / a["mean"] - 1) * 100
            se = math.sqrt((a["sd"] ** 2) / a["n_all"] + (b["sd"] ** 2) / b["n_all"])
            band = args.k * se / a["mean"] * 100
            ok = abs(b["mean"] - a["mean"]) <= args.k * se
            deltas[(key[1], met)].append(d)
            if not ok:
                flagged.append((key, met, d, band))
            fmt = lambda x: f"{x:,.0f}" if x >= 100 else f"{x:.1f}"
            print(f"| {key[0]} | {key[1]} | {key[2]} | {key[3]} | {met} | {fmt(a['mean'])} | {fmt(b['mean'])} | "
                  f"{d:+.1f}% | ±{band:.1f}% | {'ok' if ok else '**outside**'} |")

    print("\n## Summary: median and max |Δ| per server and metric\n")
    print("| server | metric | median Δ | max |Δ| | cells |")
    print("|---|---|---|---|---|")
    for (srv, met), ds in sorted(deltas.items()):
        print(f"| {srv} | {met} | {sorted(ds)[len(ds)//2]:+.1f}% | {max(abs(x) for x in ds):.1f}% | {len(ds)} |")
    print(f"\n{len(flagged)} of {len(common) * len(metrics)} comparisons outside the band"
          + (":" if flagged else "."))
    for key, met, d, band in flagged:
        print(f"  {key[0]} {key[1]} pp={key[2]} tg={key[3]} {met}: {d:+.1f}% (band ±{band:.1f}%)")
    only_a, only_b = sorted(set(A) - set(B)), sorted(set(B) - set(A))
    if only_a or only_b:
        print(f"\nonly in {na}: {len(only_a)} cells; only in {nb}: {len(only_b)} cells")


if __name__ == "__main__":
    main()
