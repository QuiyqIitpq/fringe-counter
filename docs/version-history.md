# Version history / 版本区别

| Local version | Main change | Publication decision |
| --- | --- | --- |
| v1.1 / v1.1.1 | Initial signed local-phase tracking; v1.1.1 adds Chinese/English switching | Existing Git history retained |
| v1.2 / v1.2.1 | Editable multiple counting regions, independent include/show switches, revision history, undoable exclusion/cleaning/stitching; v1.2.1 adds bilingual UI/reports | Publish v1.2.1 as a historical milestone |
| v1.3 | Updated phase-plane tracking and an explicit direct-reference measurement path | Documented here; included in later code |
| v1.4 | Optional joint integer-candidate diagnosis and model-based whole-video estimates | Documented here; included in later code |
| v1.5 | Adaptive same-frame-pair filtering, local verification at the fixed reference point, stricter cache compatibility | Documented here; included in later code |
| v1.6 | Dense multiscale spatial branch review, separately preserved evidence, consistent primary cards/CSV/model summaries | Documented here; included in v1.7 full mode |
| v1.7.0 | Default balanced mode, optional full spatial review, cached computation, one decode and parallel region tracking | Current recommended download |

中文：选择 v1.2.1 与 v1.7.0 两个代表节点公开。v1.3～v1.6 是数值与复核方法逐步演进的阶段，功能合并在 v1.7.0 中，避免给下载者过多近似版本。v1.7.0 的“均衡”模式逐帧处理，保留相位提取、局部质量检查和联合诊断；“完整”模式额外进行密集空间复核。

The 2026-10-22 publication packages are prepared from the local versions. Local development folders and laboratory results are preserved separately. This table describes implementation changes; it does not establish accuracy improvements on arbitrary experimental recordings.
