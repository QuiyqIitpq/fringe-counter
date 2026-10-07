# First-publication validation

Checked on 2026-10-07 on macOS with Python 3.12, NumPy 2.3.5, Pillow 12.3.0, and FFmpeg/FFprobe installed.

## Results

| Check | Result |
| --- | --- |
| Existing core test suite | 9 tests passed |
| Synthetic-video generation, decoding, automatic ROI selection, signed accumulation, and HTML export | Passed |
| Compressed YUV420 video and manual ROI selection | Passed |
| Exact adjacent-frame extraction in the manual ROI check | Passed |
| Local server initialization and HTML response | Passed |
| Command-line help and macOS launcher syntax | Passed |

The synthetic input has a ground-truth net change of **+8.15 fringes**, including forward motion, reversal, and jitter.

| Synthetic case | Reported net change | Absolute error | Flagged steps |
| --- | ---: | ---: | ---: |
| Lossless generated AVI, automatic selection | 8.1496523633 | 0.0003476367 | 0 |
| H.264/YUV420 compression, manual selection | 8.1447130588 | 0.0052869412 | 0 |

These errors apply to these configured synthetic cases only. They are not estimates of experimental uncertainty or guarantees for other videos.

## Scope and limits

- The numerical `core.py` and all three existing test scripts are identical to the supplied v1.1 source files.
- The published application's personal default-video path was removed. The macOS launcher uses the project's virtual environment or Python on PATH.
- Original laboratory recordings, generated laboratory reports, and internal handover notes are excluded.
- The public package starts with no default video and no bundled aluminium example.
- The local server's initialization and page response were checked; this release was not given a new full browser interaction review.
- Windows and Linux execution were not tested in this publication.
- No new independent calibration on real laboratory recordings was performed for this publication.
- Quality flags do not prove that all temporal aliasing or integer-fringe loss has been detected.
- Display precision, synthetic-case error, and experimental accuracy must be treated as separate quantities.

## Reproduction

Install the requirements and FFmpeg, then run the three commands listed under “Reproduce the synthetic checks” in the [README](../README.md). Run the video-generation check before the compressed-video/manual-ROI check.
