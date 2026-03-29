# Paper 02 Evidence Index

本文档用于把第二篇中文工作稿中的核心主张，映射到已经存在的图、表、研究日志与拟定的正文图组结构。当前目标不是穷尽所有研究资产，而是锁定能够直接支撑正文主线的证据主干。

## A. 基线与论文定位

### A1. Paper I 提供统一 ACM 主干

- 角色：
  - 理论基线
  - 方法学基线
  - 统一常数族与 retained trunk 基线
- 来源：
  - `../01_galaxy_dynamics_anchor_collapse/main.tex`
- 题目：
  - `Anchor Collapse Model (ACM): Holographic Coherence and the First Principles of Galactic Rotation`

### A2. 第二篇的定位

- 角色：
  - 不重写 ACM trunk
  - 不提出新的替代函数
  - 以统一 ACM 基线对 MOND-favored 少数样本做客观残差审计
- 对应正文：
  - 摘要
  - 第 1 节引言
  - 第 2 节审计哲学与统一 ACM 基线

## B. 正文主图清单（锁定版）

### Figure 1. 全样本残差病理总图

- 文件：
  - `../../research_assets/derived_exports/full_sample_residual_pathology_map.png`
- 配套：
  - `../../research_assets/derived_exports/full_sample_residual_pathology_map_summary.csv`
  - `../../research_assets/research_data/full_sample_residual_pathology_audit.csv`
  - `../../research_assets/derived_exports/full_sample_residual_pathology_summary.csv`
  - `../../research_assets/derived_exports/full_sample_residual_pathology_group_counts.csv`
- 角色：
  - 给出 164 样本的总分布
  - 锁定 `102 / 22 / 9 / 31` 的全样本病理图谱
  - rigid-trunk audit 复跑后该分层保持完全不变
- 对应正文：
  - 第 3.1 节
  - 第 3.2 节

### Figure 2. 几何人质聚焦图

- 文件：
  - `../../research_assets/derived_exports/pathology_geometry_hostages_focus.png`
- 配套：
  - `../../research_assets/derived_exports/mond_resistant_distance_edge_response.csv`
  - `../../research_assets/derived_exports/mond_resistant_distance_edge_ranked.csv`
  - `../../research_assets/derived_exports/mond_resistant_distance_edge_summary.csv`
- 角色：
  - 支撑 `22` 个 geometry hostages
  - 强调 `D + e_D` 一侧翻盘与几何敏感性
- 对应正文：
  - 第 4.1 节

### Figure 3. 恒星人质聚焦图

- 文件：
  - `../../research_assets/derived_exports/pathology_stellar_hostages_focus.png`
- 配套：
  - `../../research_assets/derived_exports/holdout40_ml_sensitivity_ranked.csv`
  - `../../research_assets/derived_exports/holdout40_ml_sensitivity_summary.csv`
  - `../../research_assets/derived_exports/holdout40_gas_richness_summary.csv`
- 角色：
  - 支撑 `9` 个 stellar hostages
  - 强调保守 `M/L` 扫描下的回归向量与质量归一化敏感性
- 对应正文：
  - 第 4.2 节

### Figure 4. hard31 外盘结构聚焦图

- 文件：
  - `../../research_assets/derived_exports/pathology_hard31_focus.png`
- 配套：
  - `../../research_assets/derived_exports/hard31_gas_gradient_summary.csv`
  - `../../research_assets/derived_exports/hard31_gas_curvature_summary.csv`
- 角色：
  - 支撑 `31` 个 hard31 作为低结构、低曲率、长外盘系统
  - 强调其“空载运行”式的弱结构特征
- 对应正文：
  - 第 4.3 节

### Figure 5. hard31 来源与家族 topology

- 文件：
  - `../../research_assets/derived_exports/hard31_reference_topology.png`
- 配套：
  - `../../research_assets/derived_exports/hard31_reference_topology.csv`
  - `../../research_assets/derived_exports/hard31_geometry_distance_audit.csv`
- 角色：
  - 作为 hard31 进入正文的第二层证据
  - 说明它们不仅结构上极弱，而且来源上构成更软 regime 的来源孤岛
  - 支撑 `f_D = 5` 数量为 `0`
- 对应正文：
  - 第 4.3 节后半段
  - 第 5 节讨论

## C. 几何人质 22

### C1. 距离边缘翻盘

- 证据：
  - `../../research_assets/derived_exports/mond_resistant_distance_edge_response.csv`
  - `../../research_assets/derived_exports/mond_resistant_distance_edge_ranked.csv`
  - `../../research_assets/derived_exports/mond_resistant_distance_edge_summary.csv`
- 关键数字：
  - `n_flipped_at_distance_edge = 22`
  - 翻盘几乎全部发生在 `D + e_D`
- 对应正文：
  - 第 4.1 节

### C2. surrender 子集来源与家族

- 证据：
  - `../../research_assets/derived_exports/distance_edge_surrender_numeric_summary.csv`
  - `../../research_assets/derived_exports/distance_edge_surrender_fd_counts.csv`
  - `../../research_assets/derived_exports/distance_edge_surrender_ref_token_summary.csv`
- 对应正文：
  - 第 4.1 节
  - 第 5 节讨论

## D. 恒星人质 9

### D1. M/L 合理扫描翻盘

- 证据：
  - `../../research_assets/derived_exports/holdout40_ml_sensitivity_ranked.csv`
  - `../../research_assets/derived_exports/holdout40_ml_sensitivity_summary.csv`
- 关键数字：
  - `n_flipped_to_acm = 9`
- 对应正文：
  - 第 4.2 节

### D2. gas-rich 背景

- 证据：
  - `../../research_assets/derived_exports/holdout40_gas_richness_summary.csv`
- 对应正文：
  - 第 4.2 节
  - 第 5 节讨论

## E. hard31 判官组

### E1. 外盘气体梯度与持续占比

- 证据：
  - `../../research_assets/derived_exports/hard31_gas_gradient_summary.csv`
- 关键数字：
  - `mean outer gas slope ≈ 1.12`
  - `mean outer_to_inner_gas_ratio ≈ 5.95`
- 对应正文：
  - 第 4.3 节

### E2. 外盘气体曲率

- 证据：
  - `../../research_assets/derived_exports/hard31_gas_curvature_summary.csv`
- 关键数字：
  - `mean outer gas curvature ≈ 3.96`
- 对应正文：
  - 第 4.3 节

### E3. 来源与硬几何锚点缺失

- 证据：
  - `../../research_assets/derived_exports/hard31_reference_topology.csv`
  - `../../research_assets/derived_exports/hard31_reference_topology.png`
  - `../../research_assets/derived_exports/hard31_geometry_distance_audit.csv`
- 关键结论：
  - `f_D = 5` 数量为 `0`
- 对应正文：
  - 第 4.3 节
  - 第 5 节讨论

### E4. 原始 Vgas 频谱检查

- 证据：
  - `../../research_assets/derived_exports/vgas_spectrum_hard31_vs_acm102.png`
  - `../../research_assets/derived_exports/vgas_spectrum_hard31_vs_acm102_summary.csv`
- 角色：
  - 排除性证据
  - 说明 hard31 的问题不是简单的“原始频谱假信号”或“过度平滑”
- 对应正文：
  - 补充材料优先
  - 正文第 4.3 节可文字引用

## F. 失败算子封档

这些结果不作为正文主图，但应在讨论或补充材料中保留为方法学诚实度证据：

- `../../research_assets/derived_exports/hard31_holographic_diffusion_summary.csv`
- `../../research_assets/derived_exports/hard31_self_shielding_leff_summary.csv`
- `../../research_assets/derived_exports/hard31_holographic_impedance_summary.csv`
- `../../research_assets/derived_exports/impedance_operator_generalization_summary.csv`

对应正文：

- 第 4.3 节
- 第 5 节讨论
- 附录 A

## G. 研究日志回链

第二篇正文的关键叙事节点，均已在研究日志中留痕：

- `18.4.11`
  - `MOND-favored regime as a distance-mass trap`
- `18.4.12`
  - `Full-sample residual pathology audit`
- `18.4.13`
  - `Full-sample pathology map figure`
- `18.4.14`
  - `Four-quadrant verdict from the full pathology map`
- `18.4.15`
  - `Generalization audit of the holographic impedance operator`
- `18.4.16`
  - `Archive verdict for the holographic impedance operator`

## H. 当前图表策略结论

正文主图锁定为：

1. `full_sample_residual_pathology_map.png`
2. `pathology_geometry_hostages_focus.png`
3. `pathology_stellar_hostages_focus.png`
4. `pathology_hard31_focus.png`
5. `hard31_reference_topology.png`

补充材料优先图为：

1. `vgas_spectrum_hard31_vs_acm102.png`
2. 距离边缘响应的完整表与 ranked 输出
3. `M/L` 灵敏度 ranked 与 summary
4. 失败算子归档图表
