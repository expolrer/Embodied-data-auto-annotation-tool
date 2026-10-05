#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
model_python="${AUTO_LABELER_MODEL_PYTHON:-/ssd/openpi/.venv/bin/python}"
data_python="${AUTO_LABELER_DATA_PYTHON:-/ssd/hhw/depth-processing/.venv/bin/python}"
sam2_source="${AUTO_LABELER_SAM2_SOURCE:-/ssd/hhw/depth-processing/models/sam2}"

if [[ -n "${UV_BIN:-}" ]]; then
  uv_bin=$UV_BIN
elif command -v uv >/dev/null 2>&1; then
  uv_bin="$(command -v uv)"
elif [[ -x /root/.local/bin/uv ]]; then
  uv_bin=/root/.local/bin/uv
else
  echo "uv was not found; set UV_BIN explicitly." >&2
  exit 1
fi

for python_bin in "$model_python" "$data_python"; do
  if [[ ! -x "$python_bin" ]]; then
    echo "Python environment does not exist: $python_bin" >&2
    exit 1
  fi
done

model_version="$($model_python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
data_version="$($data_python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$model_version" != "$data_version" ]]; then
  echo "Runtime Python versions differ: model=$model_version data=$data_version" >&2
  exit 1
fi

base_python="$($model_python -c 'import sys; print(sys._base_executable)')"
if [[ ! -x "$repo_root/.venv/bin/python" ]]; then
  "$uv_bin" venv --python "$base_python" "$repo_root/.venv"
fi

overlay_site="$($repo_root/.venv/bin/python -c 'import site; print(site.getsitepackages()[0])')"
model_site="$($model_python -c 'import site; print(site.getsitepackages()[0])')"
data_site="$($data_python -c 'import site; print(site.getsitepackages()[0])')"
{
  printf '%s\n' \
    "$repo_root/interaction-auto-labeler-v3/src" \
    "$repo_root/interaction-auto-labeler-v2/src" \
    "$repo_root/interaction-labeler-v1/src" \
    "$model_site" \
    "$data_site"
  if [[ -f "$sam2_source/sam2/build_sam.py" ]]; then
    printf '%s\n' "$sam2_source"
  fi
} > "$overlay_site/embodied_auto_labeler_runtime.pth"

"$repo_root/.venv/bin/python" -c \
  'import cv2, numpy, PIL, pyarrow, rosbags, torch, transformers, yaml; print("runtime dependencies: ready")'
module_path="$($repo_root/.venv/bin/python -c 'import interaction_auto_labeler_v3; print(interaction_auto_labeler_v3.__file__)')"
if [[ "$module_path" != "$repo_root/"* ]]; then
  echo "V3 resolved outside the canonical repository: $module_path" >&2
  exit 1
fi
"$repo_root/scripts/auto-labeler-v3" --help >/dev/null

echo "Server overlay environment is ready at $repo_root/.venv"
echo "V3 source:      $module_path"
echo "Model packages: $model_site"
echo "Data packages:  $data_site"
