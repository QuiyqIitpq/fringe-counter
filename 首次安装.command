#!/bin/zsh
cd -- "${0:A:h}" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/Current/bin:$PATH"
task_python="$(command -v python3)"
if [[ -z "$task_python" ]] || ! "$task_python" -c 'import sys; assert sys.version_info >= (3,10)' 2>/dev/null; then
  print '请先安装 Python 3.10+，再重新运行。 / Install Python 3.10+ first.'
  read '?按回车关闭 / Press Return to close…'
  exit 1
fi
print '为当前文件夹安装运行依赖（需要联网） / Installing dependencies for this folder (internet required)…'
if ! "$task_python" -m venv .venv || ! .venv/bin/python3 -m pip install -r requirements.txt; then
  print '安装未完成，请保留错误信息。 / Setup failed; retain the error message.'
  read '?按回车关闭 / Press Return to close…'
  exit 1
fi
if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  print 'Python 依赖已就绪；还需安装 FFmpeg / FFprobe。 / Python dependencies ready; install FFmpeg / FFprobe.'
else
  print '已就绪，可以双击 启动条纹计数.command。 / Ready: double-click 启动条纹计数.command.'
fi
read '?按回车关闭 / Press Return to close…'
