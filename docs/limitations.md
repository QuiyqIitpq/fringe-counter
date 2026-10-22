# Interpretation and validation limits

- A full 2π phase cycle is one fringe. Signs describe image-phase direction until physically calibrated.
- Raw observations, conditional sums, estimated repairs and accepted continuous segments are distinct outputs.
- Motion above half a fringe between usable frames can produce undetectable aliasing. Processing every frame does not remove this sampling limit.
- Missing phase and shared integer-branch ambiguity cannot always be uniquely recovered from the recording.
- Trend stitching assumes continuation of a neighboring slow trend and can remove a real permanent optical-path change.
- In v1.7, a model-based primary estimate can differ from the strict raw summary. Read unresolved-interval and sensitivity diagnostics alongside the number.
- Dense grids share image pixels. Agreement is not independent probability evidence. Window-sensitivity ranges are not confidence intervals and need not contain the truth.
- Comparisons across versions or modes require the same video, regions, reference point and processing configuration.
- Displaying three decimal places does not establish 0.001-fringe experimental accuracy. Fringe motion includes apparatus and air-path effects and is not a calibrated material-expansion measurement by itself.

中文：原始观测、条件和、估计修复与通过检查的连续片段应分别理解。密集空间复核、参数一致性和版本间接近不能代替独立实验真值；显示的小数位数也不是实际准确度。拼接和联合估计依赖明确的模型假设，请同时检查未解决区间。
