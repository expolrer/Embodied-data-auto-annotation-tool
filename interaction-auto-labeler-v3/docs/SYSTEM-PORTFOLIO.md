# 自动标注系统组合设计

## 设计结论

V3 不再被视为一条必须全部运行的超长流水线，而是由一个共享数据底座和七个可独立部署、
独立复核、独立验收的系统组成。系统之间只通过版本化事件图和 sidecar 交换结果；任何模型输出
都必须保留来源、模型版本、置信度和人工修订记录。

```text
                         +---------------------------+
                         | 共享数据底座              |
                         | ingestion/event graph     |
                         | versions/shards/jobs/audit|
                         +-------------+-------------+
                                       |
                 +---------------------+--------------------+
                 |                                          |
        S1 目标实例与跟踪                          S4 RGB-D 三维几何
                 |                                          |
        S2 交互事件与边界 <------------------------ cross-view evidence
                 |
        +--------+------------------+
        |                           |
 S3 分层语言                 S5 结果与数据质量
        |                           |
        +-------------+-------------+
                      |
              S6 金标与主动学习
                      |
              S7 VLA 训练与评估
```

## 共享数据底座

共享底座不是第八个标注模型，它负责所有系统都需要的工程契约：

1. 将 ROS bag、LeRobot 和已解帧数据映射到统一 episode/frame/camera 时间轴。
2. 用 `embodied_event_graph_v1` 保存实体、观测、事件、语言和证据引用。
3. 分别版本化原始数据、自动标注、人工修订、模型和阈值；发布版本使用内容哈希。
4. 使用稳定分片和幂等任务队列支撑断点续跑、并行计算和失败重试。
5. 记录模型来源、配置、输入数据版本、生成时间、审核人和覆盖原因。
6. 审核页面只显示需要决策的证据，所有修改以追加式 correction 保存。

建议物理存储分层为 `raw/`、`normalized/`、`features/`、`annotations/`、`gold/`、
`exports/`，而不是由每个系统复制一份视频。

## 七个系统

| ID | 系统 | 核心交付 | 当前成熟度 | 设计文档 |
| --- | --- | --- | --- | --- |
| S1 | 目标实例与二维视频跟踪 | 活跃物体、框、mask、track ID、跨视角 ID | Beta，V1/V2 已有主链路 | [S1](systems/01-target-instance-2d.md) |
| S2 | 交互事件与时序边界 | task/subtask/event 与六阶段边界 | Beta，启发式可用，学习边界待金标 | [S2](systems/02-interaction-temporal.md) |
| S3 | 实体约束的分层语言 | 三级描述、指代表达、前后置状态 | Beta，模板/VLM 接口可用 | [S3](systems/03-grounded-language.md) |
| S4 | 跨视角 RGB-D 三维几何 | 动态外参、点云、3D 轨迹、重投影 | Alpha，依赖真实标定 | [S4](systems/04-geometry-3d.md) |
| S5 | 任务结果与数据质量 | 成败、失败类型、异常、质量门控 | Alpha，异常与校准已实现，结果模型待训练 | [S5](systems/05-quality-outcome.md) |
| S6 | 金标集与主动学习闭环 | 金标、低分队列、裁决、纠错蒸馏 | Alpha，抽样/校准/纠错可用 | [S6](systems/06-gold-active-learning.md) |
| S7 | VLA 训练导出与评估 | ACT/π0.5 sidecar、配对消融、效果报告 | Alpha，工具可用，真实 A/B 尚未完成 | [S7](systems/07-vla-training-evaluation.md) |

“代码可运行”与“模型效果经过验证”是两种状态。S4 只有在内参、手眼标定和 FK 验证通过后
才能产生可信三维标签；S7 只有完成固定 split、同预算配对训练和真机/回放评测后，才能声称
某类标注提高了 VLA 能力。

## 如何选择系统组合

| 目标 | 推荐 profile | 实际展开 |
| --- | --- | --- |
| 快速得到目标框和视频轨迹 | `target_tracking` | S1 |
| 制作带事件和语言的数据集 | `semantic_events` | S1 + S2 + S3 |
| 做 RGB-D 跨视角标签 | `rgbd_geometry` | S1 + S4 |
| 建立自动接收/人工复核闭环 | `quality_loop` | S1 + S2 + S5 + S6 |
| 验证二维标注对 VLA 的价值 | `training_2d` | S1 + S2 + S3 + S5 + S6 + S7 |
| 验证完整 RGB-D 标注价值 | `training_rgbd` | S1 至 S7 |

千万级数据不应默认运行最昂贵组合。推荐先对全部数据运行轻量 S1/S2/S5，按风险分层后只对
困难样本运行 VLM，对需要三维监督的任务运行 S4，并将人工预算集中到 S6 选出的样本。

## 命令化规划

列出系统、输入能力和预设组合：

```bash
./scripts/auto-labeler-v3 list-systems \
  --output /ssd/hhw/annotations/system_catalog.json
```

根据当前数据能力生成拓扑排序后的实施计划：

```bash
./scripts/auto-labeler-v3 plan-systems \
  --profile training_rgbd \
  --available rgb,timestamps,target_description,task_instruction,robot_state \
  --available depth_metric,calibration_bundle,dataset_version,human_review \
  --available policy_config,split_manifest \
  --strict \
  --output /ssd/hhw/annotations/training_rgbd.plan.json
```

`--strict` 会在缺少能力时返回非零状态，适合 CI 或大规模任务提交前检查。也可以重复
`--system` 只规划指定系统；加 `--no-dependencies` 可检查是否遗漏上游系统。

## 统一输出规则

所有系统输出至少包含：

- `dataset_id`、`dataset_version`、`episode_id` 和帧区间。
- `producer`、模型/代码版本、参数摘要和父标注版本。
- `confidence_raw`、校准后的 `confidence` 与证据引用。
- `review_state`、人工修订者、修订时间、原因和原始值。
- 可重算的输入 URI/内容哈希，不在事件图中重复存放大图或点云。

框、mask、轨迹等使用了未来帧的信息时，只能作为训练监督或离线分析，默认不得作为策略推理
时的必需输入。否则离线指标会因为未来信息泄漏而虚高。

## 迭代顺序

1. 先冻结共享 schema、版本规则和 200 至 500 段分层金标，建立每个系统的基线指标。
2. 完成 S1 的同类实例和遮挡稳定性，再训练 S2 的多模态边界模型。
3. 用 S1/S2 的实体和事件约束 S3，禁止 VLM 自由生成未观测对象或结果。
4. 对有标定的数据启用 S4；未标定数据保留二维结果，不伪造三维真值。
5. 用 S5/S6 建立按置信度自动接受、低分审核、纠错回流的闭环。
6. 最后通过 S7 的 ACT/π0.5 配对消融决定哪些标签值得大规模生产。
