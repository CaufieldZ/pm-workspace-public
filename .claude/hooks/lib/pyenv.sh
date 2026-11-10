#!/usr/bin/env bash
# 项目解释器解析 —— 把 .venv/bin 前置到 PATH，让本仓所有 python3 调用落到装了依赖的解释器。
#
# 为什么必须有：hook 由 Claude Code / git 直接启动，**不继承用户 shell 的 venv 激活**。项目依赖
# 装在 .venv（requirements.txt 自注「须装进本 venv」），裸 python3 会落到系统解释器。后果不是
# 报错而是**门静默失效**：缺 bs4 时 ui-annotation 门（check_ui_annotation.py → lib/ui_annotation.py）
# 顶层 import 直接炸，退出码非 0 被当成「检查未通过」；缺 ruff / mypy 时语法门静默降级成
# py_compile、audit §19 空跑；缺 pytest 时 pre-commit 的测试段会拦下每次提交。
#
# 为什么用 PATH 前置、不逐位点替换解释器：本仓 shell 侧 python 调用点 60+ 处，散在 hooks /
# lib/ / .githooks/ / audit.sh / 测试 harness 里。逐处替换既易漏，也挡不住未来新增的位点；
# 前置 PATH 一次覆盖全部，且连带覆盖 xargs python3、python3 -m ruff、python 子进程再 spawn
# 的场景——那些位置换成变量也覆盖不到。
#
# 被 source 时立即生效（幂等，可重复 source）。无 .venv 的环境（public 克隆 / CI）是空操作，
# PATH 与 PYTHON_BIN 一律不动。
#
# 逃生口：
#   PYTHON_BIN=<解释器>   显式指定，优先于 .venv（调用方沿用 ${PYTHON_BIN:-python3} 即可）
#   PMWS_NO_VENV=1        整体关掉本机制（排查「是不是 venv 引起的」用）
#   PMWS_ROOT=<路径>      显式指定仓库根（供可从任意 cwd 调起的入口，如 sync_public.sh）

pmws_use_project_python() {
  if [ -n "${PMWS_NO_VENV:-}" ]; then return 0; fi
  if [ -n "${_PMWS_PYENV_READY:-}" ]; then return 0; fi

  # cwd 不作首选：hook 在子项目目录里跑会指错。git hook / 根脚本的 cwd 本就是仓库根。
  # PMWS_ROOT 供「可被从任意 cwd 调起」的入口显式传入仓库根（如 sync_public.sh 按自身位置定位）。
  local root="${PMWS_ROOT:-${CLAUDE_PROJECT_DIR:-$(pwd)}}"

  if [ -n "$root" ] && [ -x "$root/.venv/bin/python" ]; then
    PATH="$root/.venv/bin:$PATH"
    export PATH
    if [ -z "${PYTHON_BIN:-}" ]; then
      PYTHON_BIN="$root/.venv/bin/python"
      export PYTHON_BIN
    fi
  fi

  _PMWS_PYENV_READY=1
  export _PMWS_PYENV_READY
  return 0
}

pmws_use_project_python
