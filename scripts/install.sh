#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ -n "${UV_BIN:-}" ]]; then
  uv_bin=$UV_BIN
elif command -v uv >/dev/null 2>&1; then
  uv_bin="$(command -v uv)"
elif [[ -x /root/.local/bin/uv ]]; then
  uv_bin=/root/.local/bin/uv
else
  echo "uv is required. Install it explicitly before running this script." >&2
  exit 1
fi

"$uv_bin" venv --python "${AUTO_LABELER_PYTHON_VERSION:-3.10}" .venv
"$uv_bin" pip install --python .venv/bin/python \
  -e './interaction-labeler-v1[rosbag,lerobot,models]' \
  -e './interaction-auto-labeler-v2[grounded-sam2]' \
  -e './interaction-auto-labeler-v3[models,parquet]'

echo "Installed. Run: ./scripts/auto-labeler-v3 --help"
