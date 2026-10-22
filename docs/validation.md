# v1.6.0 publication checks — 2026-10-22

The public package passes 61 Python numerical/integration/report tests, 8 DOM interaction tests and 5 chart/primary-output checks on macOS. Tests include controlled/generated inputs; private laboratory recordings are not bundled.

The local server is smoke-checked for blank personal defaults/history, language asset delivery and embedded standalone reports. Numerical source is retained from the local v1.6.0 version; only public packaging, personal defaults/history discovery, startup and documentation are adapted.

v1.6 is slower because it performs a second dense spatial pass. It is not independently proven to be the most accurate release. v1.7 full mode retains the same class of review with optimizations. Residual integer ambiguity and model assumptions remain visible; increased runtime does not establish calibrated accuracy.

No independent experimental ground-truth calibration or new visual browser review was performed for this publication. Windows/Linux are not verified. See README for reproduction commands and [version comparison](version-history.md) for the runtime/review trade-off.
