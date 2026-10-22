#!/bin/zsh
cd -- "${0:A:h}" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
task_python=""
if [[ -x "$PWD/.venv/bin/python3" ]]; then
  task_python="$PWD/.venv/bin/python3"
else
  task_python="$(command -v python3)"
fi
if [[ -z "$task_python" ]] || ! "$task_python" -c 'import sys; assert sys.version_info >= (3,10); import numpy; import PIL' 2>/dev/null; then
  print '缺少 Python 3.10+、NumPy 或 Pillow。请参考 docs/usage-zh.md 完成安装。'
  read '?按回车关闭窗口…'
  exit 1
fi
if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  print '缺少 FFmpeg / FFprobe。请先安装 FFmpeg 后再启动。'
  read '?按回车关闭窗口…'
  exit 1
fi
"$task_python" app.py "$@"
if [[ $? -ne 0 ]]; then
  read '?启动未完成，按回车关闭窗口…'
fi
