# Embodied Data Auto Annotation Tool

面向机器人 RGB-D 视频与 LeRobot 数据集的多视角、时序化自动标注系统。当前主版本为 V3，
仓库同时保留 V1/V2 作为可复现的基础模块；V3 直接复用它们完成候选检测、交互实例判断、
双向跟踪和人工复核。

> 本仓库是自动标注工具的唯一开发仓库。原 `depth-process-model` 中的标注运行脚本
> 已迁至此处；深度处理与注意力指标仍由原项目维护。模型权重和数据不纳入 Git。

## 系统结构

```text
ROS bag / LeRobot / extracted RGB-D
  -> V1: GroundingDINO + RGB-D/关节/夹爪排序 + SAM2 + 人工抽检
  -> V2: 目标描述 + 全场实例盘点 + 接触帧 + 跨视角关联 + 风险帧复核
  -> V3: 统一事件图 + 分层边界/语言 + 质量校准 + 三维几何 + 训练闭环
```

V3 内部进一步拆成一个共享数据底座和七个可独立运行、复核及验收的系统：

| 系统 | 负责的问题 | 当前成熟度 |
| --- | --- | --- |
| 目标实例与二维跟踪 | 实际操作的是哪个实例，逐帧在哪里 | Beta |
| 交互事件与时序边界 | 何时接触、抓取、搬运、放置和释放 | Beta |
| 实体约束分层语言 | 如何按 task/subtask/event 准确描述 | Beta |
| 跨视角 RGB-D 三维几何 | 目标在物理空间哪里、三视角是否一致 | Alpha，依赖真实标定 |
| 任务结果与数据质量 | 是否成功、为何失败、数据是否可用 | Alpha |
| 金标集与主动学习 | 哪些样本值得人工、如何校准与回流纠错 | Alpha |
| VLA 训练导出与评估 | 标签如何用于 ACT/π0.5，是否真正提升策略 | Alpha，真实 A/B 待完成 |

完整的模块边界、输入输出、审核点、VLA 接法和验收指标见
[`SYSTEM-PORTFOLIO.md`](interaction-auto-labeler-v3/docs/SYSTEM-PORTFOLIO.md)。

| 模块 | 状态 | 已交付内容 | 生产数据前置条件 |
| --- | --- | --- | --- |
| P0 数据底座 | 代码完成 | 统一事件图、LeRobot v3 校验/转换、版本清单、稳定分片、任务队列、金标抽样 | 发布数据需生成 full hash 版本并完成双人金标 |
| P1 时序与语言 | 代码完成 | task/subtask/event 三级边界、Transformer refiner、实体约束三级语言 | learned refiner 需用金标边界训练 |
| P2 质量体系 | 代码完成 | isotonic 可靠度校准、GVL 进度评估、异常检测、自动质量门控 | 自动接收前需拟合校准器并提供 GVL 响应 |
| P3 三维几何 | 代码完成 | 动态腕部 FK、点云融合、6D proxy/轨迹、跨视角重投影 | 需相机内参、手眼标定、URDF 和逐帧关节角 |
| P4 训练闭环 | 工具完成 | 纠错蒸馏、LeRobot sidecar、ACT/π0.5 配对消融和 bootstrap | 真实结论需固定 split、V3 sidecar、untouched gold set 和训练结果 |

代码完成不代表模型效果已经被验证。当前尚未执行 ACT/π0.5 的真实 A/B 训练，因此仓库不会把
注意力图、dry-run 或未校准分数写成“标注能提高真机成功率”的结论。

## 目录

| 目录 | 作用 |
| --- | --- |
| `interaction-labeler-v1/` | 基础多视角互动标注器 |
| `interaction-auto-labeler-v2/` | 任务目标实例自动判定与跟踪 |
| `interaction-auto-labeler-v3/` | 大规模数据治理、质量、几何和训练闭环 |
| `scripts/` | V1/V2 标注引擎、数据提取、复核工具及统一入口 |
| `depth_pipeline/` | ROS bag 解码与深度对齐所需的共享基础模块 |
| `scripts/auto-labeler-v3` | 始终运行当前仓库源码的统一入口 |
| `scripts/install.sh` | 创建环境并安装三层模块 |
| `scripts/bootstrap_server_env.sh` | 无复制地组合服务器现有模型与数据依赖 |

## 安装

推荐 Python 3.10，以兼容 ROS bag、Grounded-SAM2 与现有模型依赖：

```bash
cd /ssd/hhw/Embodied-data-auto-annotation-tool
./scripts/install.sh
```

脚本只安装 Python 包，不下载 GroundingDINO、SAM2、SAM3 或 VLM 权重。模型路径必须在运行命令中
显式提供。

服务器已经存在 OpenPI 模型环境和深度数据环境时，可建立独立的只读 overlay。该方式不会向两个
来源环境安装或删除任何包：

```bash
cd /ssd/hhw/Embodied-data-auto-annotation-tool
./scripts/bootstrap_server_env.sh
```

默认从 `/ssd/openpi/.venv` 读取 PyTorch/Transformers/PyArrow，从
`/ssd/hhw/depth-processing/.venv` 读取 ROS bag 与 OpenCV 依赖。可分别通过
`AUTO_LABELER_MODEL_PYTHON` 和 `AUTO_LABELER_DATA_PYTHON` 覆盖来源。
已有 SAM2 源码默认读取 `/ssd/hhw/depth-processing/models/sam2`，可通过
`AUTO_LABELER_SAM2_SOURCE` 改写。Qwen3.5 消歧可使用独立解释器：

```bash
export AUTO_LABELER_VLM_PYTHON=/root/miniconda3/envs/qwen35vl/bin/python
export AUTO_LABELER_SAM2_PYTHON=/root/miniconda3/envs/cosmos311/bin/python
export AUTO_LABELER_SAM2_SOURCE=/ssd/hhw/depth-processing/models/sam2
```

两个独立解释器分别只影响 VLM 消歧和 SAM2 跟踪；检测与 ROS bag 解码仍在本仓库
的 `.venv` 中运行。
overlay 会把本仓库 V3/V2/V1 的 `src` 路径放在两个来源环境之前，并在配置时检查实际导入路径，
因此依赖来自既有环境，自动标注源码始终来自本仓库。
V1/V2 默认从本仓库的 `scripts/` 运行检测、排序、VLM 和 SAM2；无须另行检出
`depth-process-model`。`--engine-root` 仅用于显式选择其他兼容脚本目录。

## 启动 V3

```bash
cd /ssd/hhw/Embodied-data-auto-annotation-tool
./scripts/auto-labeler-v3 run \
  --data /ssd/hhw/zhuomian/lerobot \
  --format lerobot \
  --workspace /ssd/hhw/annotations/zhuomian_v3 \
  --task interaction-auto-labeler-v3/configs/example_task.yaml \
  --concept-model /path/to/grounding-dino \
  --sam2-checkpoint /path/to/sam2.1_hiera_large.pt \
  --vlm-model /path/to/local-vlm \
  --port 8773
```

重新打开已有工作区：

```bash
./scripts/auto-labeler-v3 serve \
  --workspace /ssd/hhw/annotations/zhuomian_v3 \
  --port 8773
```

查看全部系统或按当前数据条件生成实施计划：

```bash
./scripts/auto-labeler-v3 list-systems
./scripts/auto-labeler-v3 plan-systems \
  --profile semantic_events \
  --available rgb,timestamps,target_description,task_instruction,robot_state \
  --strict --output /ssd/hhw/annotations/semantic_events.plan.json
```

内置 profile 包括 `target_tracking`、`semantic_events`、`rgbd_geometry`、`quality_loop`、
`training_2d`、`training_rgbd` 和 `full`。计划器会自动展开依赖并列出缺失的数据、标定、人工
审核或训练配置能力；`--strict` 适合在提交大规模任务前阻止不完整配置。

统一入口会优先使用仓库自身 `.venv/bin/python`。也可设置 `AUTO_LABELER_PYTHON` 指向已经配置好
Grounded-SAM2/VLM 的 Python；无论使用哪个解释器，入口都会把当前仓库源码置于 `PYTHONPATH`
最前面，确保更新后不会误用旧 wheel。

## 验证

```bash
./scripts/auto-labeler-v3 --help
.venv/bin/python -m pytest -q interaction-labeler-v1/tests
.venv/bin/python -m pytest -q interaction-auto-labeler-v2/tests
.venv/bin/python -m pytest -q interaction-auto-labeler-v3/tests
```

V3 的完整命令、输出契约和 P0-P4 验收边界见
[`interaction-auto-labeler-v3/README.md`](interaction-auto-labeler-v3/README.md)。
