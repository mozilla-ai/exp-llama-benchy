#!/bin/sh
# Rebuild the three comparison figures (and the CSV of every plotted point)
# from the campaigns the blog post compares. One picture per machine, three
# model columns (two on the Deck, which cannot hold the 27B); the 27B column is
# the MTP experiment, i.e. speculative decoding on for all four runtimes, which
# is what Ollama and LM Studio do by default.
#
# Sources: client-side llama-benchy measurements everywhere, with one
# exception -- LM Studio's token generation on macOS is taken from the engine's
# own print_timing, because LM Studio on macOS releases the SSE stream in
# bursts and the client-side figure comes out 4-9 % (tg=64) / 10-15 % (tg=32)
# ABOVE what the engine produced, which is not possible for a real measurement
# (data/20260912-m4max/lmstudio-client-vs-server.md). On the L40S and the Deck
# LM Studio's client-side decode is 2-3 % below the server-side one, like every
# other runtime's, so it is left as measured.
#
#   usage: tools/make_figures.sh [data-dir]      (default: data)
set -eu
cd "$(dirname "$0")/.."
DATA="${1:-data}"
OUT="$DATA/plots"
mkdir -p "$OUT"
ALL3="qwen3.5-0.8b-all-servers qwen3.5-9b-all-servers qwen3.8-27b-mtp"

uv run tools/plot_campaign.py "$DATA/20260912-l40s" --title "Linux / NVIDIA L40S (CUDA)" \
    --experiments $ALL3 --out "$OUT/l40s.png" --csv "$OUT/l40s.csv"

uv run tools/plot_campaign.py "$DATA/20260912-m4max" --title "macOS / Apple M4 Max (Metal)" \
    --tg-source-for lm-studio=server \
    --experiments $ALL3 --out "$OUT/m4max.png" --csv "$OUT/m4max.csv"

# Deck: llama.cpp is the official b10441 release build (integer-dot Vulkan
# shaders), adopted as the default on 2026-09-14. Its cells come from the
# 2026-09-13 A/B arm; llamafile, LM Studio and Ollama are the 2026-09-12
# campaign's, same machine state (the A/B's stock arm reproduced its campaign
# twin to -0.0 % median). Composition and provenance: the folder's README.
# LM Studio is now the only runtime without integer-dot shaders -- its runtime
# is a prebuilt download and cannot follow.
uv run tools/plot_campaign.py "$DATA/20260912-steamdeck-idot" --title "Steam Deck / AMD Van Gogh (Vulkan)" \
    --experiments qwen3.5-0.8b-all-servers qwen3.5-9b-all-servers --out "$OUT/steamdeck.png" --csv "$OUT/steamdeck.csv"
