# Fringe Counter v1.3.0

[English](README.md) | [中文](README.zh-CN.md)

**Phase-tracking and gap-diagnostics milestone · Experimental prototype · Chinese / English UI**

## Characteristics

- Local phase-plane tracking and carrier refresh applied consistently to the same pair of frames.
- Explicit direct-reference measurement, enabled by default only when a valid region center coincides with the fixed reference point; it is labeled separately from multi-region support.
- Distinguishes complete accepted counts, qualified partial counts and conditional diagnostic sums.
- Exports gap causes and continuous readable intervals, with original-frame inspection.
- Does not contain the later joint integer-candidate / dense spatial review pipeline. Unresolved gaps remain explicit.

The direct-reference path is a local observation with reduced multi-region support. It cannot create missing phase, extrapolate an unsupported reference or establish a reliable complete count across unresolved gaps. Later releases contain further filtering and review improvements.

See [version selection and trade-offs](docs/version-history.md) for v1.2.1, v1.3, v1.6 and v1.7.

## Install and run

This is a source package requiring **Python 3.10+, FFmpeg / FFprobe, NumPy and Pillow**. On macOS, install Python and FFmpeg, run **首次安装.command** once, then run **启动条纹计数.command**. Keep the terminal open. Setup downloads Python dependencies; video analysis stays local.

Alternatively:

```sh
python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt
.venv/bin/python3 app.py
```

Windows can use `py -3 -m venv .venv` and `.venv\Scripts\python.exe`; Windows/Linux are not verified in this publication.

Choose a video, generate or draw regions, analyze, select an interval/sign, inspect diagnostics and export. The upper-right **English / 中文** button preserves current work. New self-contained HTML reports include the switch; editing/recalculation requires the running application.

The package has no personal default recording, bundled laboratory results or sibling-folder runtime dependency. Only this installation's `results/` is automatically listed.

## Interpretation and checks

Raw observations, partial sums, conditional totals and estimated repairs are distinct. Signs are image-phase directions; decimal digits are not calibrated accuracy. Read [limitations](docs/limitations.md), [validation](docs/validation.md) and the [Chinese guide](docs/usage-zh.md).

Publication checks: 37 Python tests, 7 DOM tests and 2 chart/primary-output checks passed. Developer commands:

```sh
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_chart.js
npm install
npm test
```

AI assistance was used in development and documentation. No license has been selected.
