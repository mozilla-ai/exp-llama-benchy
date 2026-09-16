#!/bin/sh
# Create the Ollama tags that serve the lmstudio-community GGUFs, so every
# runtime in experiments.yaml runs byte-identical weights.
#
#   usage: ollama/create-lms-models.sh [LMS_ROOT]
#   LMS_ROOT defaults to ~/.lmstudio/models/lmstudio-community
#
# Each Modelfile.* here carries a "# TAG <name>" line and a @LMS@ placeholder.
# After creating, the script verifies that the blob Ollama stored is the
# source file: Ollama names blobs by sha256, so the FROM line of the created
# tag must equal the digest of the GGUF we pointed it at.
set -eu
LMS="${1:-$HOME/.lmstudio/models/lmstudio-community}"
DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v shasum >/dev/null 2>&1; then digest() { shasum -a 256 "$1" | cut -d' ' -f1; }
else digest() { sha256sum "$1" | cut -d' ' -f1; }; fi

status=0
for mf in "$DIR"/Modelfile.*; do
  tag="$(sed -n 's/^# TAG *//p' "$mf" | head -1)"
  src="$(sed -n 's|^FROM *@LMS@/||p' "$mf" | head -1)"
  [ -n "$tag" ] && [ -n "$src" ] || { echo "skip $mf: no TAG/FROM"; continue; }
  gguf="$LMS/$src"
  [ -f "$gguf" ] || { echo "MISSING $gguf"; status=1; continue; }

  tmp="$(mktemp)"
  sed "s|@LMS@|$LMS|g" "$mf" > "$tmp"
  echo "==> ollama create $tag  (from $gguf)"
  ollama create "$tag" -f "$tmp"
  rm -f "$tmp"

  want="$(digest "$gguf")"
  got="$(ollama show --modelfile "$tag" | sed -n 's|^FROM .*/sha256-||p' | head -1)"
  if [ "$want" = "$got" ]; then echo "    OK  blob sha256 == source sha256 ($want)"
  else echo "    MISMATCH  source=$want  blob=$got"; status=1; fi
done
exit $status
