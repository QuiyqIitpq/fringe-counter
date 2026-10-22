# Fringe Counter

[English](README.md) | [中文](README.zh-CN.md)

**v1.7.0 · Experimental research prototype · 中文 / English · Local video processing**

Balanced all-frame tracking with optional full spatial review. Load a recorded interferogram, select clear regions, and inspect signed forward/reverse and fractional fringe changes. Videos are processed on your computer.

This is the current recommended source release. [Downloads and release notes](https://github.com/QuiyqIitpq/fringe-counter/releases).

## First run

This download contains source code. It requires **Python 3.10+, FFmpeg/FFprobe, NumPy and Pillow**. It is not a standalone application binary.

On macOS, install Python and FFmpeg from their official channels, then double-click **首次安装.command** once to create the project environment and install the Python dependencies. Next double-click **启动条纹计数.command**. Keep its terminal window open during use. The Python setup step uses the internet; video analysis stays local.

Alternatively, from the extracted folder on macOS or Linux:

```sh
python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt
.venv/bin/python3 app.py
```

On Windows, create the environment with `py -3 -m venv .venv`, then use `.venv\Scripts\python.exe` for installation and running `app.py`. Windows and Linux are not verified in this publication.

## Workflow

1. Choose a video and preview a clear time.
2. Generate candidate regions or add/move/resize rectangular regions manually.
3. Analyze. Region geometry changes require retracking; processing switches operate on saved tracks.
4. Choose an interval and sign. Including a region changes statistics; showing a curve only changes visibility.
5. Inspect quality flags and original adjacent frames. Preview model-based changes before applying them.
6. Save the current revision and export CSV, JSON, data arrays and a self-contained HTML snapshot.

Use **English / 中文** in the upper-right corner to switch immediately without resetting work. New HTML snapshots also include the language button. A snapshot freezes statistics; reopen the saved analysis in the running app to edit or recalculate.

The public package starts without a personal default video or bundled laboratory results. Saved analyses created in this installation appear under its own `results/` folder.

## Analysis modes

**Balanced** is the default: all frames are processed, with adaptive pair filtering, local quality checks, robust fusion and joint diagnostics. It avoids the additional dense full-frame spatial review.

**Full spatial review** adds the dense multiscale checks introduced in v1.6. Reanalyzing unchanged regions can reuse their tracks. It can take substantially longer.

Parallel tracking uses temporary disk maps (up to five workers). Disk use scales with frame count, region count and processed region size. The application checks available space; normal completion/error cleanup removes `.tracking_tmp`. Interrupted or forcibly killed runs can leave temporary files.

## Command line

```sh
.venv/bin/python3 app.py --video '/path/to/video.mp4' --out 'results/my-analysis' --mode balanced
```

`--rois-json` supplies region geometry and `--preview` selects the reference time for candidate detection. It does not define heating onset.

## Results and limitations

Counts are image-phase changes. Conditional or model-based totals can contain unresolved integer branches and are not calibrated displacement or thermal expansion. Display precision is not measurement accuracy. Read [interpretation limits](docs/limitations.md) and [publication validation](docs/validation.md).

## Versions and checks

See [version comparison](docs/version-history.md), [CHANGELOG](CHANGELOG.md), and [Chinese guide](docs/usage-zh.md). Numerical tests require only the runtime dependencies and FFmpeg. Optional DOM tests require Node.js 18+ and jsdom:

```sh
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_chart.js
npm install
npm test
```

AI assistance was used in development and documentation. No open-source license has been selected; this publication does not add one.
