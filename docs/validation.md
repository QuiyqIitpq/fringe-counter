# Publication checks — v1.7.0

Rechecked on macOS, 2026-10-22, using the public source package:

| Check | Result |
| --- | --- |
| Python numerical, video integration and report tests | 65 passed; no skips |
| DOM language/state/mode tests | 9 passed |
| Chart and primary-output checks | 5 passed |

Tests use generated signals/videos and controlled fixtures. They cover the cases implemented in the supplied suite, not every recording or failure mode. Private experimental videos and results are not included.

Application-server initialization, bilingual asset delivery, report embedding and the public package's blank default/history are smoke-checked for publication. No new browser screenshot or visual browser acceptance is claimed. Windows/Linux execution and a new independent calibration on laboratory footage were not performed.

The numerical source is retained from the selected local version. Packaging changes are limited to personal defaults/history discovery, startup guidance, documentation and test portability. The exact v1.6 tracking regression baseline is bundled under `tests/baselines/`; the suite no longer needs a sibling v1.6 folder.

Runtime dependencies: Python 3.10+, NumPy, Pillow and FFmpeg/FFprobe. Optional DOM tests use Node.js and jsdom 26.0.0. See README for reproduction commands and [limitations](limitations.md) for scientific interpretation.
