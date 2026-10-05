#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
PY="${AUTO_LABELER_PYTHON:-$repo_root/.venv/bin/python}"
SAM2_SOURCE="${SAM2_SOURCE:-$repo_root/models/sam2}"
SAM2_CHECKPOINT="${SAM2_CHECKPOINT:-$SAM2_SOURCE/checkpoints/sam2.1_hiera_large.pt}"
HEAD_GPU="${HEAD_GPU:-2}"
WRIST_GPU="${WRIST_GPU:-3}"
export PYTHONPATH="$SAM2_SOURCE${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p outputs/target_tracks_required

CUDA_VISIBLE_DEVICES="$HEAD_GPU" "$PY" scripts/track_required_views_sam2.py --role head --device cuda:0 --checkpoint "$SAM2_CHECKPOINT" > outputs/target_tracks_required/head.log 2>&1 &
head_pid=$!
CUDA_VISIBLE_DEVICES="$WRIST_GPU" "$PY" scripts/track_required_views_sam2.py --role wrist --device cuda:0 --checkpoint "$SAM2_CHECKPOINT" > outputs/target_tracks_required/wrist.log 2>&1 &
wrist_pid=$!

wait "$head_pid"
wait "$wrist_pid"
"$PY" scripts/merge_required_view_tracks.py
