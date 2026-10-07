#!/bin/zsh
cd -- "${0:A:h}" || exit 1
task_python=""
if [[ -x "$PWD/.venv/bin/python3" ]]; then
  task_python="$PWD/.venv/bin/python3"
else
  task_python="$(command -v python3)"
fi
if [[ -z "$task_python" ]] || ! "$task_python" -c 'import numpy; import PIL' 2>/dev/null; then
  print '缺少 Python、NumPy 或 Pillow。请参考 README.md 安装依赖。'
  read '?按回车关闭窗口…'
  exit 1
fi
"$task_python" app.py
if [[ $? -ne 0 ]]; then
  read '?启动未完成，按回车关闭窗口…'
fi
