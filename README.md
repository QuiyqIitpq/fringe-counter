# 🔬 Fringe Counter

An offline tool for tracking signed interference-fringe changes in recorded videos.

**Current version: v1.1.1 · Experimental prototype · 中文 / English interface**

The tool extracts local Fourier phase from multiple regions, tracks frame-to-frame changes, and reports forward, reverse, and net fringe motion. Videos are processed on your computer.

## Features

- AVI, MP4, MOV, MKV, and M4V input, subject to FFmpeg decoder support
- Automatic ROI selection or a manually selected search area
- Signed forward/reverse motion and fractional fringe changes
- Interactive time-interval selection and sign reversal
- Quality flags and adjacent-frame inspection
- CSV, JSON, NPZ, PNG, and standalone HTML report export
- Command-line analysis and a local browser interface
- One-click Chinese / English switching in the application and newly generated offline reports

## Quick start

Requirements: Python 3.10+, FFmpeg/FFprobe available on PATH, and the Python packages in `requirements.txt`.

From the project directory, on macOS or Linux:

```sh
python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt
.venv/bin/python3 app.py
```

On Windows:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

The server opens a local browser page. Choose a video, preview a clear frame, select the analysis area if needed, and start analysis. Use **English / 中文** in the upper-right corner to switch the interface immediately. Chinese is the default; the browser remembers your choice for the same local address when storage is available. Switching preserves the video, selected interval, sign and analysis results. Stop the server with Ctrl+C. Windows instructions are provided but have not been tested in this release.

Newly generated `report.html` files include the same language button and work offline. Existing exported reports must be regenerated to gain the switch. Command-line messages and raw CSV/JSON contents retain their existing format.

On macOS, after installing the dependencies, you can also double-click `启动条纹计数.command`.

The public package does not contain laboratory recordings or precomputed laboratory reports. The original aluminium-example button is hidden when those reports are absent. Choose your own recording to use the application.

For the Chinese user guide, see [使用说明](docs/usage-zh.md).

## Command-line analysis

```sh
.venv/bin/python3 app.py --video '/path/to/video.avi' --out 'results/my-analysis' --preview 30
```

`--preview` selects the reference frame for ROI detection; it does not trim the analyzed video or define the heating start time.

## Reproduce the synthetic checks

Run these in order, using the Python environment where dependencies are installed:

```sh
.venv/bin/python3 -m unittest discover -s tests -p 'test_core.py' -v
.venv/bin/python3 tests/validate_video.py
.venv/bin/python3 tests/check_manual_roi.py
```

The second command generates a synthetic video with forward motion, reversal, and jitter. Its net ground-truth change is **+8.15 fringes**. The third command uses that generated video to check compressed-video decoding and manually selected regions. Test outputs are written under `results/` and excluded from version control.

See [validation notes](docs/validation.md) for the first-publication checks and their limits.

[View the synthetic test output plot](docs/demo-output.png) ([vector version](docs/demo-output.svg)). This separately formatted figure uses generated test data; it is not a screenshot of the application or a laboratory recording.

## Interpreting results

- One full 2π phase cycle is one fringe; a bright-to-dark transition alone is half a fringe.
- Forward and reverse motion add algebraically. Their absolute totals should not be added to obtain net motion.
- The sign is an image-phase convention until calibrated against physical displacement.
- A flagged interval gives a **conditional estimate**, not an established total.
- Continuous tracking assumes the true frame-to-frame motion is less than half a fringe. Temporal aliasing can escape the quality checks.
- Displaying 0.01 fringe does not establish 0.01-fringe experimental accuracy.
- Apparent optical phase motion includes apparatus and air-path changes. It is not, by itself, a calibrated thermal-expansion measurement.
- Drift-onset detection proposes a directional-motion candidate; it does not measure temperature or establish when heating began.

## Project files

| File | Purpose |
| --- | --- |
| `core.py` | Video decoding, Fourier phase tracking, ROI fusion, and result export |
| `app.py` | Local web server and command-line runner |
| `index.html` | Browser interface |
| `i18n.js` | Chinese / English presentation translations, embedded into offline reports |
| `tests/` | Core checks and reproducible synthetic-video checks |
| `docs/` | User guide, validation notes, and synthetic output visualization |

## Method background

The method uses spatial-carrier Fourier phase extraction and temporal tracking. Background: [Takeda, Ina & Kobayashi (1982)](https://doi.org/10.1364/JOSA.72.000156). This implementation is not software supplied by the paper, and the paper does not validate this application's experimental accuracy.

## Publication notes

This is the first GitHub publication of the supplied v1.1 application. The numerical core and existing tests are preserved. Packaging changes remove a personal default video path, remove a Codex-specific launcher dependency, and make documentation suitable for sharing. No open-source license has been selected for this publication.

AI assistance was used in development and documentation. The checks described here support only the specific cases tested; they do not establish general accuracy on experimental recordings.
