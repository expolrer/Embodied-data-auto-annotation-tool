from pathlib import Path

import pytest

from interaction_auto_labeler_v3.system_catalog import (
    CAPABILITIES,
    SYSTEMS,
    build_system_plan,
    catalog_payload,
    resolve_systems,
)


def test_catalog_has_unique_systems_and_valid_dependencies() -> None:
    payload = catalog_payload()
    system_ids = [item.system_id for item in SYSTEMS]
    project_root = Path(__file__).parents[1]
    assert payload["schema"] == "embodied_annotation_system_catalog_v1"
    assert len(system_ids) == len(set(system_ids)) == 7
    for item in SYSTEMS:
        assert set(item.dependencies) <= set(system_ids)
        assert set(item.required_capabilities) <= CAPABILITIES.keys()
        assert item.design_document.startswith("docs/systems/")
        assert (project_root / item.design_document).is_file()


def test_training_rgbd_profile_is_dependency_ordered() -> None:
    plan = build_system_plan(profile="training_rgbd", available_capabilities=CAPABILITIES.keys())
    system_ids = [item["system_id"] for item in plan["systems"]]
    assert system_ids.index("target_instance_2d") < system_ids.index("interaction_temporal")
    assert system_ids.index("interaction_temporal") < system_ids.index("grounded_language")
    assert system_ids.index("grounded_language") < system_ids.index("vla_training_evaluation")
    assert "geometry_3d" in system_ids
    assert plan["summary"] == {"systems": 7, "ready": 7, "blocked": 0}


def test_plan_reports_capability_and_transitive_dependency_blocks() -> None:
    plan = build_system_plan(profile="semantic_events", available_capabilities={"rgb"})
    states = {item["system_id"]: item for item in plan["systems"]}
    assert states["target_instance_2d"]["state"] == "blocked_by_capability"
    assert states["interaction_temporal"]["state"] == "blocked_by_capability"
    assert states["grounded_language"]["state"] == "blocked_by_capability"
    assert {item["capability"] for item in plan["capability_gaps"]} == {
        "robot_state",
        "target_description",
        "task_instruction",
        "timestamps",
    }


def test_no_dependencies_exposes_missing_system_dependencies() -> None:
    plan = build_system_plan(
        requested=("grounded_language",),
        available_capabilities=CAPABILITIES.keys(),
        include_dependencies=False,
    )
    assert plan["systems"][0]["state"] == "blocked_by_unplanned_dependency"
    assert plan["systems"][0]["missing_dependencies"] == [
        "target_instance_2d",
        "interaction_temporal",
    ]


def test_unknown_system_or_capability_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown annotation system"):
        resolve_systems(("missing",))
    with pytest.raises(ValueError, match="unknown capabilities"):
        build_system_plan(requested=("target_instance_2d",), available_capabilities={"lidar"})
