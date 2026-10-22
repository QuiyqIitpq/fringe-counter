# v1.3.0 — Public source release

- Local phase-plane tracking and carrier refresh applied consistently to the same pair of frames.
- Explicit direct-reference measurement, enabled by default only when a valid region center coincides with the fixed reference point; it is labeled separately from multi-region support.
- Distinguishes complete accepted counts, qualified partial counts and conditional diagnostic sums.
- Exports gap causes and continuous readable intervals, with original-frame inspection.
- Does not contain the later joint integer-candidate / dense spatial review pipeline. Unresolved gaps remain explicit.

The direct-reference path is a local observation with reduced multi-region support. It cannot create missing phase, extrapolate an unsupported reference or establish a reliable complete count across unresolved gaps. Later releases contain further filtering and review improvements.

Published from the local implementation on 2026-10-22. Personal default videos, sibling history scans and runtime dependencies are removed from the shared package. Private recordings/results are excluded. Numerical implementation is unchanged. See [version selection](docs/version-history.md).
