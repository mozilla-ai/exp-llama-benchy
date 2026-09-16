#!/bin/sh
# Copy a finished campaign from a benchmark host into data/<name>/ on this
# machine: results/, report/, logs/ (runner log, Ollama daemon log), the LM
# Studio server logs for the given months, a host/version snapshot, and -- on a
# host where Ollama is a systemd service -- a journal dump.
#
#   usage: tools/collect_campaign.sh HOST REMOTE_REPO DEST [YYYY-MM ...]
#   e.g.   tools/collect_campaign.sh studio /Users/mala/workspace/exp-benchy data/20260925-m4max 2026-09
#          tools/collect_campaign.sh 89.169.109.142 /home/mala/workspace/exp-benchy data/20260925-l40s 2026-09
#          tools/collect_campaign.sh steamdeck /home/deck/workspace/exp-benchy data/20260925-steamdeck 2026-09
#
# Then: tools/server_timings.py --results DEST/results --lmstudio-log DEST/lmstudio-server-logs/*.log \
#           --ollama-log DEST/logs/ollama-serve.log|DEST/ollama-journal.log --csv DEST/server-timings.csv
set -eu
HOST="$1"; REPO="$2"; DEST="$3"; shift 3
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
mkdir -p "$DEST/lmstudio-server-logs"
rsync -az -e "$SSH" "$HOST:$REPO/results/" "$DEST/results/"
rsync -az -e "$SSH" "$HOST:$REPO/report/"  "$DEST/report/"
rsync -az -e "$SSH" "$HOST:$REPO/logs/"    "$DEST/logs/" 2>/dev/null || true
for m in "$@"; do
  rsync -az -e "$SSH" "$HOST:.lmstudio/server-logs/$m/" "$DEST/lmstudio-server-logs/" 2>/dev/null || true
done
# Ollama journal (systemd hosts only; passwordless sudo assumed there)
$SSH "$HOST" 'systemctl is-active ollama >/dev/null 2>&1 && sudo -n journalctl -u ollama --since "-30 days" --no-pager -o short-iso 2>/dev/null' \
  > "$DEST/ollama-journal.log" 2>/dev/null || true
[ -s "$DEST/ollama-journal.log" ] || rm -f "$DEST/ollama-journal.log"
# host / version snapshot.
# Piped to `sh -s` rather than run through the login shell: on the Mac that is
# zsh, where an unmatched glob aborts the whole command and an unquoted $VAR does
# not word-split -- both of which silently truncated this file. The heredoc is
# quoted so nothing expands locally; $1 is the remote repo path.
$SSH "$HOST" sh -s "$REPO" <<'EOSH' > "$DEST/host-info.txt" 2>/dev/null || true
PATH=$PATH:/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:$HOME/.lmstudio/bin
cd "$1" || exit 0
# portable helpers: GNU vs BSD userland
hash_of() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -c1-16; }
size_of() { wc -c < "$1" | tr -d ' '; }

echo "host: $(uname -n)  date: $(date -u +%Y-%m-%dT%H:%MZ)"
echo "exp-benchy commit: $(git rev-parse --short HEAD 2>/dev/null)"
echo "os: $(uname -sr)"
command -v nvidia-smi >/dev/null 2>&1 && echo "gpu: $(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader)"
command -v system_profiler >/dev/null 2>&1 && echo "machine: $(system_profiler SPHardwareDataType 2>/dev/null | grep -E 'Chip|Memory' | sed 's/^ *//' | tr '\n' ';')"

for b in /Users/mala/workspace/llama.cpp/build/bin/llama-server \
         /home/mala/workspace/llama.cpp/build/bin/llama-server \
         /home/deck/workspace/llama.cpp/build/bin/llama-server; do
  [ -x "$b" ] || continue
  echo "llama-server: $($b --version 2>&1 | head -1)"
  echo "llama-server int-dot: $(strings "$b" | grep -c matmul_q4_k_q8_1)"
done

# The campaign binary, de-duplicated (find may reach the same file by two paths).
find "$HOME" /Users/mala/llamafiles /home/mala/llamafiles /home/deck/Downloads \
     -maxdepth 2 -name 'llamafile-0.10.*' -type f 2>/dev/null | sort -u | while read -r b; do
  [ -x "$b" ] || continue
  echo "llamafile: $b: $($b --version 2>&1 | head -1) (sha256 $(hash_of "$b"))"
done

# llamafile is a thin build: the GPU module it loads is <exe_dir>/ggml-*, and which
# one is in play is the campaign variable. Record identity AND capability, so a
# reader can tell a CUDA-graphs module from a pre-graphs one and an integer-dot
# Vulkan module from a stock-glslc one without going back to the machine.
find "$HOME/.llamafile" "$HOME" -maxdepth 3 -name 'ggml-*' -type f 2>/dev/null | sort -u | while read -r m; do
  case "$m" in *.so|*.dylib) ;; *) continue ;; esac
  echo "llamafile module: $m (sha256 $(hash_of "$m"), $(size_of "$m") B, cuda-graphs=$(strings "$m" | grep -ci 'cuda graph'), int-dot=$(strings "$m" | grep -c matmul_q4_k_q8_1))"
done

echo "ollama: $(ollama --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
echo "lm studio runtime: $(lms runtime ls 2>/dev/null | grep '✓' | awk '{print $1}' | tr '\n' ' ')"
printf 'ollama -lms blobs: '
for t in qwen3.5:0.8b-lms qwen3.5:9b-lms qwen3.8:27b-lms qwen3.8:27b-lms-mtp qwen3.8:27b-lms-mtp4; do
  printf '%s=%s ' "$t" "$(ollama show --modelfile "$t" 2>/dev/null | sed -n 's|^FROM .*/sha256-||p' | head -1 | cut -c1-12)"
done; echo
printf 'ollama draft lengths: '
for t in qwen3.8:27b-lms-mtp qwen3.8:27b-lms-mtp4; do
  printf '%s=%s ' "$t" "$(ollama show --parameters "$t" 2>/dev/null | awk '/draft_num_predict/{print $2}')"
done; echo
EOSH
echo "collected into $DEST:"
echo "  results: $(ls "$DEST"/results/*.json 2>/dev/null | wc -l | tr -d ' ') json; report: $(ls "$DEST"/report 2>/dev/null | wc -l | tr -d ' ') files; lmstudio logs: $(ls "$DEST"/lmstudio-server-logs 2>/dev/null | wc -l | tr -d ' '); ollama journal: $([ -f "$DEST/ollama-journal.log" ] && echo yes || echo no)"
cat "$DEST/host-info.txt"
