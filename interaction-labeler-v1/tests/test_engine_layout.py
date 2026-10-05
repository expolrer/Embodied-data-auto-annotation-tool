import sys

import pytest

from interaction_labeler.pipeline import default_engine_root, vlm_python


def test_default_engine_is_self_contained() -> None:
    root = default_engine_root()
    for name in (
        "extract_rgbd.py",
        "align_depth_to_rgb.py",
        "extract_robot_timeline.py",
        "detect_grounded_candidates.py",
        "rank_interaction_candidates.py",
        "resolve_ambiguity_with_vlm.py",
        "track_required_views_sam2.py",
        "track_targets_sam2.py",
    ):
        assert (root / "scripts" / name).is_file(), name
    for name in ("geometry.py", "rosbag_extract.py"):
        assert (root / "depth_pipeline" / name).is_file(), name


def test_vlm_uses_separate_python_when_configured(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("AUTO_LABELER_VLM_PYTHON", raising=False)
    assert vlm_python() == sys.executable
    python = tmp_path / "python"
    python.touch()
    monkeypatch.setenv("AUTO_LABELER_VLM_PYTHON", str(python))
    assert vlm_python() == str(python)
    monkeypatch.setenv("AUTO_LABELER_VLM_PYTHON", str(tmp_path / "missing"))
    with pytest.raises(FileNotFoundError):
        vlm_python()
