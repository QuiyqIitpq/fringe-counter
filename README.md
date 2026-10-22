# Fringe Counter v1.6.0

[English](README.md) | [中文](README.zh-CN.md)

**Thorough-review reference release — slower · Experimental prototype · Chinese / English UI**

## Characteristics

- Full dense spatial review by default, with multiple grid scales, anchor sets and local-gradient connections.
- Retains adaptive same-pair filtering and locally verified fixed-reference measurements from v1.5.
- Stores spatial evidence, failed checks and remaining integer ambiguity separately.
- Uses consistent primary model estimates for cards, curves, forward/reverse totals and CSV while preserving strict raw results.
- Changing participating regions or the reference position invalidates old spatial evidence; visibility switches do not change statistics.
- **Runtime cost:** the extra spatial pass is slow. This is the review-first reference release; v1.7 balanced is preferable for faster everyday work.

v1.6 is slower because it performs a second dense spatial pass. It is not independently proven to be the most accurate release. v1.7 full mode retains the same class of review with optimizations. Residual integer ambiguity and model assumptions remain visible; increased runtime does not establish calibrated accuracy.

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

Publication checks: 61 Python tests, 8 DOM tests and 5 chart/primary-output checks passed. Developer commands:

```sh
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_chart.js
npm install
npm test
```

AI assistance was used in development and documentation. No license has been selected.
