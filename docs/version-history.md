# Choose a version / 版本选择

| Version | Main characteristics | Speed and intended use |
| --- | --- | --- |
| [v1.2.1](https://github.com/QuiyqIitpq/fringe-counter/releases/tag/v1.2.1) | Editable regions, reversible processing, bilingual UI and reports | Historical interface baseline / 多框与双语基础版 |
| [v1.3.0](https://github.com/QuiyqIitpq/fringe-counter/releases/tag/v1.3.0) | Local phase-plane tracking, same-pair carrier refresh, explicit direct-reference measurement, gap diagnostics and qualified partial counts | Observation and diagnostics first; no dense spatial review / 原始观测与断点诊断优先 |
| [v1.6.0](https://github.com/QuiyqIitpq/fringe-counter/releases/tag/v1.6.0) | Full dense multiscale spatial review by default; separately preserved raw results, evidence and model estimates | **Slower, thorough-review reference version / 复核优先的慢速参考版** |
| [v1.7.0](https://github.com/QuiyqIitpq/fringe-counter/releases/tag/v1.7.0) | Balanced mode by default; optional full spatial review; cached calculations and parallel ROI tracking | **Recommended for everyday work / 日常使用推荐**; use full mode for additional spatial review |

## v1.6: review first, with a runtime cost

v1.6 adds a second dense spatial pass after tracking. It checks multiple grid scales, anchor sets and local-gradient connections, retains voting/failure evidence, and does not force curved fringes into one global plane. This extra work can be substantially slower than v1.7 balanced mode. Choose it when reproducing the v1.6 workflow or prioritizing detailed spatial diagnostics over turnaround time.

“Precision-oriented / review-first” describes the workflow, not a proven accuracy ranking. There is no independent ground truth establishing v1.6 as the most accurate release. v1.7 full mode retains the same class of dense review with computational optimizations; v1.6 should not be claimed inherently more accurate than v1.7 full mode. More checks can still leave ambiguous integer branches.

中文：v1.6 的定位是“复核优先、耗时较长”。它默认追加完整密集空间检查，适合有时间仔细检查结果、保留证据或复现旧流程的场景。不能仅因它更慢，就把结果标成已验证的“最精准”。v1.7 完整模式保留同类检查，均衡模式则侧重日常速度。空间复核仍可能留下整数歧义，模型总数仍需结合未解决区间读取。

## Intermediate changes / 中间版本

- v1.4 introduced optional joint integer-candidate diagnostics and model-based whole-video estimates.
- v1.5 introduced adaptive same-frame-pair filtering and locally verified fallback measurements at the fixed reference point.
- These changes are included in v1.6 and v1.7. They are documented rather than published as separate downloads.

Compare versions or modes only with the same video, regions, reference point and processing configuration. Runtime depends on video size, region count and hardware. Display precision, review depth and independently measured accuracy are different quantities.
