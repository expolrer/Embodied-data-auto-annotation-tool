from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

CATALOG_SCHEMA = "embodied_annotation_system_catalog_v1"
PLAN_SCHEMA = "embodied_annotation_system_plan_v1"


@dataclass(frozen=True)
class SystemSpec:
    system_id: str
    name: str
    name_zh: str
    goal: str
    maturity: str
    dependencies: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    optional_capabilities: tuple[str, ...]
    outputs: tuple[str, ...]
    acceptance_metrics: tuple[str, ...]
    design_document: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CAPABILITIES: dict[str, str] = {
    "rgb": "Synchronized RGB frames for the required camera views.",
    "timestamps": "A shared monotonic timestamp or frame-index timeline.",
    "target_description": "A target object description with task-relevant attributes.",
    "task_instruction": "The episode-level natural-language instruction.",
    "robot_state": "Time-aligned joints, end-effector, gripper, or action state.",
    "depth_metric": "RGB-aligned depth in a documented metric scale.",
    "calibration_bundle": "Intrinsics plus static/dynamic camera extrinsics and FK inputs.",
    "dataset_version": "Immutable dataset and annotation version identifiers.",
    "human_review": "Named reviewers and an auditable correction workflow.",
    "policy_config": "A runnable ACT, pi0.5, or another VLA training configuration.",
    "split_manifest": "Frozen train/validation/test and untouched-gold splits.",
}


SYSTEMS: tuple[SystemSpec, ...] = (
    SystemSpec(
        system_id="target_instance_2d",
        name="Target Instance and Video Track System",
        name_zh="目标实例与二维视频跟踪系统",
        goal="Identify the actually manipulated instance and track it across task-relevant views.",
        maturity="beta",
        dependencies=(),
        required_capabilities=("rgb", "timestamps", "target_description"),
        optional_capabilities=("robot_state", "depth_metric", "task_instruction"),
        outputs=(
            "entity inventory",
            "per-frame boxes and masks",
            "track and cross-view identity",
            "visibility, occlusion, and confidence evidence",
        ),
        acceptance_metrics=(
            "active-instance accuracy",
            "box AP / mask IoU",
            "track success and ID switches",
            "review minutes per interaction",
        ),
        design_document="docs/systems/01-target-instance-2d.md",
    ),
    SystemSpec(
        system_id="interaction_temporal",
        name="Interaction Event and Temporal Boundary System",
        name_zh="交互事件与时序边界系统",
        goal="Split episodes into task, subtask, event, and manipulation phases.",
        maturity="beta",
        dependencies=("target_instance_2d",),
        required_capabilities=("timestamps", "robot_state"),
        optional_capabilities=("rgb", "depth_metric", "task_instruction"),
        outputs=(
            "task/subtask/event spans",
            "approach/contact/grasp/transport/place/release phases",
            "active arm and interaction relations",
            "boundary uncertainty",
        ),
        acceptance_metrics=(
            "tolerance-window boundary F1",
            "mean absolute boundary error",
            "segment mIoU",
            "phase and active-arm accuracy",
        ),
        design_document="docs/systems/02-interaction-temporal.md",
    ),
    SystemSpec(
        system_id="grounded_language",
        name="Grounded Hierarchical Language System",
        name_zh="实体约束的分层语言系统",
        goal="Generate task, subtask, and event language grounded to entities and time spans.",
        maturity="beta",
        dependencies=("target_instance_2d", "interaction_temporal"),
        required_capabilities=("task_instruction",),
        optional_capabilities=("rgb", "depth_metric", "robot_state"),
        outputs=(
            "task/subtask/event descriptions",
            "referring expressions",
            "preconditions and postconditions",
            "entity and event references with provenance",
        ),
        acceptance_metrics=(
            "entity grounding accuracy",
            "temporal entailment accuracy",
            "hallucination rate",
            "human edit distance and review time",
        ),
        design_document="docs/systems/03-grounded-language.md",
    ),
    SystemSpec(
        system_id="geometry_3d",
        name="Cross-view RGB-D Geometry System",
        name_zh="跨视角 RGB-D 三维几何系统",
        goal="Lift target tracks into calibrated 3D trajectories and cross-view associations.",
        maturity="alpha_requires_calibration",
        dependencies=("target_instance_2d",),
        required_capabilities=("depth_metric", "calibration_bundle"),
        optional_capabilities=("robot_state", "rgb"),
        outputs=(
            "metric point clouds and target centroids",
            "dynamic wrist-camera trajectory",
            "cross-view reprojection evidence",
            "3D trajectory and optional 6D pose",
        ),
        acceptance_metrics=(
            "reprojection pixel error and IoU",
            "cross-view centroid disagreement",
            "trajectory jitter and dropout rate",
            "ADD/ADD-S when valid CAD pose labels exist",
        ),
        design_document="docs/systems/04-geometry-3d.md",
    ),
    SystemSpec(
        system_id="quality_outcome",
        name="Outcome and Data Quality System",
        name_zh="任务结果与数据质量系统",
        goal="Label success/failure and quarantine multimodal, geometric, and semantic anomalies.",
        maturity="alpha",
        dependencies=("interaction_temporal",),
        required_capabilities=("timestamps", "dataset_version"),
        optional_capabilities=("robot_state", "depth_metric", "rgb", "task_instruction"),
        outputs=(
            "success/failure and failure taxonomy",
            "modality and synchronization anomalies",
            "progress and consistency evidence",
            "quality gate decision with reasons",
        ),
        acceptance_metrics=(
            "success/failure macro F1",
            "anomaly precision and recall",
            "bad-sample escape rate",
            "retained-data coverage",
        ),
        design_document="docs/systems/05-quality-outcome.md",
    ),
    SystemSpec(
        system_id="gold_active_learning",
        name="Gold Set and Active Learning System",
        name_zh="金标集与主动学习闭环系统",
        goal=(
            "Spend human review on uncertain samples and convert corrections into calibrated "
            "models."
        ),
        maturity="alpha",
        dependencies=("target_instance_2d", "interaction_temporal", "quality_outcome"),
        required_capabilities=("dataset_version", "human_review"),
        optional_capabilities=("rgb", "depth_metric", "robot_state", "task_instruction"),
        outputs=(
            "stratified gold and untouched holdout sets",
            "low-confidence review queues",
            "adjudicated corrections and provenance",
            "calibrators and distillation datasets",
        ),
        acceptance_metrics=(
            "inter-annotator agreement",
            "calibration error and Brier score",
            "precision-coverage / risk-coverage curve",
            "quality gain per reviewer hour",
        ),
        design_document="docs/systems/06-gold-active-learning.md",
    ),
    SystemSpec(
        system_id="vla_training_evaluation",
        name="VLA Training Export and Evaluation System",
        name_zh="VLA 训练导出与标注价值评估系统",
        goal="Export causal annotation targets and prove their value with paired policy ablations.",
        maturity="alpha_unvalidated",
        dependencies=("grounded_language", "gold_active_learning"),
        required_capabilities=("dataset_version", "policy_config", "split_manifest"),
        optional_capabilities=("depth_metric", "calibration_bundle", "robot_state"),
        outputs=(
            "LeRobot/event-graph sidecars",
            "ACT and pi0.5 auxiliary-label adapters",
            "paired ablation run bundles",
            "offline and robot evaluation reports",
        ),
        acceptance_metrics=(
            "action loss and action MAE",
            "grounding and phase auxiliary metrics",
            "task success and intervention rate",
            "paired confidence interval / bootstrap improvement",
        ),
        design_document="docs/systems/07-vla-training-evaluation.md",
    ),
)

SYSTEM_BY_ID = {item.system_id: item for item in SYSTEMS}

PROFILES: dict[str, tuple[str, ...]] = {
    "target_tracking": ("target_instance_2d",),
    "semantic_events": ("grounded_language",),
    "rgbd_geometry": ("geometry_3d",),
    "quality_loop": ("gold_active_learning",),
    "training_2d": ("vla_training_evaluation",),
    "training_rgbd": ("vla_training_evaluation", "geometry_3d"),
    "full": tuple(item.system_id for item in SYSTEMS),
}

SHARED_FOUNDATION = (
    "ROS bag / LeRobot ingestion and synchronized modality index",
    "Embodied event graph and immutable dataset/annotation versions",
    "Stable shards, idempotent job queue, lineage, and model registry",
    "Role-based review UI, audit trail, and export contracts",
)


def catalog_payload() -> dict[str, Any]:
    return {
        "schema": CATALOG_SCHEMA,
        "shared_foundation": list(SHARED_FOUNDATION),
        "capabilities": CAPABILITIES,
        "profiles": {name: list(system_ids) for name, system_ids in PROFILES.items()},
        "systems": [item.to_dict() for item in SYSTEMS],
    }


def resolve_systems(
    requested: Iterable[str], *, include_dependencies: bool = True
) -> tuple[SystemSpec, ...]:
    requested_ids = tuple(dict.fromkeys(requested))
    if not requested_ids:
        raise ValueError("at least one annotation system must be requested")

    ordered: list[SystemSpec] = []
    complete: set[str] = set()
    visiting: set[str] = set()

    def visit(system_id: str) -> None:
        spec = SYSTEM_BY_ID.get(system_id)
        if spec is None:
            raise ValueError(f"unknown annotation system: {system_id}")
        if system_id in complete:
            return
        if system_id in visiting:
            raise ValueError(f"cyclic annotation system dependency: {system_id}")
        visiting.add(system_id)
        if include_dependencies:
            for dependency in spec.dependencies:
                visit(dependency)
        visiting.remove(system_id)
        complete.add(system_id)
        ordered.append(spec)

    for system_id in requested_ids:
        visit(system_id)
    return tuple(ordered)


def build_system_plan(
    *,
    requested: Iterable[str] | None = None,
    profile: str | None = None,
    available_capabilities: Iterable[str] = (),
    include_dependencies: bool = True,
) -> dict[str, Any]:
    if requested is not None and profile is not None:
        raise ValueError("requested systems and profile are mutually exclusive")
    if profile is not None:
        if profile not in PROFILES:
            raise ValueError(f"unknown annotation system profile: {profile}")
        selected = PROFILES[profile]
    else:
        selected = tuple(requested or PROFILES["full"])

    available = set(available_capabilities)
    unknown_capabilities = available - CAPABILITIES.keys()
    if unknown_capabilities:
        raise ValueError(f"unknown capabilities: {sorted(unknown_capabilities)}")
    systems = resolve_systems(selected, include_dependencies=include_dependencies)
    included = {item.system_id for item in systems}
    states: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    gaps: dict[str, list[str]] = {}

    for phase, spec in enumerate(systems, start=1):
        missing_capabilities = sorted(set(spec.required_capabilities) - available)
        missing_dependencies = [
            dependency for dependency in spec.dependencies if dependency not in included
        ]
        blocked_dependencies = [
            dependency
            for dependency in spec.dependencies
            if states.get(dependency, "ready") != "ready"
        ]
        if missing_dependencies:
            state = "blocked_by_unplanned_dependency"
        elif missing_capabilities:
            state = "blocked_by_capability"
        elif blocked_dependencies:
            state = "blocked_by_dependency"
        else:
            state = "ready"
        states[spec.system_id] = state
        for capability in missing_capabilities:
            gaps.setdefault(capability, []).append(spec.system_id)
        rows.append(
            {
                "phase": phase,
                "system_id": spec.system_id,
                "name_zh": spec.name_zh,
                "state": state,
                "maturity": spec.maturity,
                "dependencies": list(spec.dependencies),
                "missing_dependencies": missing_dependencies,
                "blocked_dependencies": blocked_dependencies,
                "missing_capabilities": missing_capabilities,
                "outputs": list(spec.outputs),
                "acceptance_metrics": list(spec.acceptance_metrics),
                "design_document": spec.design_document,
            }
        )

    return {
        "schema": PLAN_SCHEMA,
        "profile": profile,
        "requested_systems": list(selected),
        "include_dependencies": include_dependencies,
        "available_capabilities": sorted(available),
        "summary": {
            "systems": len(rows),
            "ready": sum(row["state"] == "ready" for row in rows),
            "blocked": sum(row["state"] != "ready" for row in rows),
        },
        "capability_gaps": [
            {
                "capability": capability,
                "description": CAPABILITIES[capability],
                "blocks": system_ids,
            }
            for capability, system_ids in sorted(gaps.items())
        ],
        "systems": rows,
    }
