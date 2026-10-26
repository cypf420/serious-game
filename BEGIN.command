#!/bin/sh
set -u
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH
cd "$(dirname "$0")"
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="$(command -v python3 || true)"
fi
if [ -z "$PYTHON" ]; then
  echo "需要 Python 3.11 或更高版本。请先安装 Python。"
  exit 1
fi
"$PYTHON" launcher.py "$@"
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  printf '\n启动失败。按回车键关闭窗口…'
  read -r _
fi
exit "$STATUS"
