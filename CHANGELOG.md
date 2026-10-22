# v1.6.0 — Public source release

- Full dense spatial review by default, with multiple grid scales, anchor sets and local-gradient connections.
- Retains adaptive same-pair filtering and locally verified fixed-reference measurements from v1.5.
- Stores spatial evidence, failed checks and remaining integer ambiguity separately.
- Uses consistent primary model estimates for cards, curves, forward/reverse totals and CSV while preserving strict raw results.
- Changing participating regions or the reference position invalidates old spatial evidence; visibility switches do not change statistics.
- **Runtime cost:** the extra spatial pass is slow. This is the review-first reference release; v1.7 balanced is preferable for faster everyday work.

v1.6 is slower because it performs a second dense spatial pass. It is not independently proven to be the most accurate release. v1.7 full mode retains the same class of review with optimizations. Residual integer ambiguity and model assumptions remain visible; increased runtime does not establish calibrated accuracy.

Published from the local implementation on 2026-10-22. Personal default videos, sibling history scans and runtime dependencies are removed from the shared package. Private recordings/results are excluded. Numerical implementation is unchanged. See [version selection](docs/version-history.md).
