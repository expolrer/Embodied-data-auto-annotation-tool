# S7 VLA 训练导出与标注价值评估系统

## 目标与边界

把事件图标签转换为 ACT、π0.5、InternVLA 或其他 VLA 可消费的训练监督，并用严格配对实验回答
“哪一种标签是否真的提高策略能力”。注意力热图和视觉观感只能作为诊断，不能替代策略评测。

## 导出契约

每个样本的 sidecar 可以包含目标框/mask、实体 ID、活动手、阶段、事件语言、3D 几何、质量与
成败标签，但必须显式区分：

- `policy_input_allowed=true`：部署时同样可获得的观测或在线预测。
- `policy_input_allowed=false`：由后续帧、全轨迹或人工结果得到，只能作监督/分析。
- `quality_only=true`：只用于过滤、采样或评测，不进入策略网络。

## 模型接入设计

ACT 推荐先保持 RGB-D/joint 主输入不变，依次增加 bbox/mask grounding、phase/progress 和 3D 辅助头。
这样可隔离深度处理和标签本身的贡献。需要 prompt 时另建 text encoder 融合实验，不与基础对比混合。

π0.5/语言 VLA 保持原始 prompt 输入，用实体/事件语言增强层级语义；框/mask/phase 作为辅助
grounding 或采样信号。不要在训练时直接裁剪成永远准确的 GT ROI，除非部署也运行同等检测器。

其他 VLA 通过统一 adapter 读取事件图，不为每个模型复制一份不可追踪的标签文件。

## 配对实验矩阵

最小实验包含：

1. Baseline：原始数据和原始训练配置。
2. Labels-only：相同策略输入，增加训练期辅助标签。
3. Filter/sample：只使用质量过滤或阶段平衡采样。
4. Online-predicted ROI：把可部署检测器输出作为输入，测量检测误差后的真实收益。
5. RGB-D geometry：在标定数据上增加深度/三维监督。

所有组固定初始化 checkpoint、数据 split、seed、优化器、训练步数、batch/token 预算和 GPU 数；
至少多 seed，按 episode 做 paired bootstrap。训练集的标注模型不能看 test episode。

## 指标

- 训练诊断：action loss/MAE、grounding IoU、phase F1、3D 误差。
- 离线策略：action chunk 误差、闭环回放偏差、OOD 分层指标。
- 真机/仿真：任务成功率、阶段成功率、干预率、碰撞/掉落和完成时间。
- 统计：均值、置信区间、paired improvement，而不是只比较单次最低 loss。

## 验收

只有在固定 untouched test、同预算多 seed 和策略级指标上出现稳定提升，才能将某类标注升级为
大规模生产必选项。若仅辅助头指标提升但动作/成功率不变，应保留其诊断价值而不扩大生产成本。

当前 sidecar、ACT/π0.5 配对 run bundle 和 bootstrap 工具已实现，尚未完成真实 A/B 训练，成熟度
为 `alpha_unvalidated`。
