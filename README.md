# Embodied Data Auto Annotation Tool

面向机器人 RGB-D 视频与 LeRobot 数据集的多视角、时序化自动标注系统。当前主版本为 V3，
仓库同时保留 V1/V2 作为可复现的基础模块；V3 直接复用它们完成候选检测、交互实例判断、
双向跟踪和人工复核。

> 本仓库是自动标注工具后续开发的唯一主仓库。`depth-process` 中的旧副本只作为历史快照，
> 不再接收该工具的新功能。

## 系统结构

```text
ROS bag / LeRobot / extracted RGB-D
  -> V1: GroundingDINO + RGB-D/关节/夹爪排序 + SAM2 + 人工抽检
  -> V2: 目标描述 + 全场实例盘点 + 接触帧 + 跨视角关联 + 风险帧复核
  -> V3: 统一事件图 + 分层边界/语言 + 质量校准 + 三维几何 + 训练闭环
```

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

默认从 `/ssd/hhw/openpi-hzh/.venv` 读取 PyTorch/Transformers/PyArrow，从
`/ssd/hhw/depth-processing/.venv` 读取 ROS bag 与 OpenCV 依赖。可分别通过
`AUTO_LABELER_MODEL_PYTHON` 和 `AUTO_LABELER_DATA_PYTHON` 覆盖来源。

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
