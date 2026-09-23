#!/usr/bin/env bash
# 共享：Write|Edit 检查器批量运行（pc_* 的「合进程」层，配套 scripts/hook_py_batch.py）
#
# 被 post-writeedit-dispatch.sh source（经 lib/post-checks.sh 的 pc_* 调用方使用）。
# 动机：dispatcher 串行 19 检查器各自起 python3，冷启 ~30ms/次是写盘路径大头
# （decisions/2026-09-13-hotpath-fixed-cost.md 阶段 3）。机制 = bash 排队 + 单进程
# 按原 argv 跑各 checker 的 main()——跑同一份代码对象而非重写（先例
# 2026-09-13-user-prompt-warn-merge 的机制化）。
#
# 四条不变量（迁移新 checker 前先读，违反即回滚）：
# 1. _pc_flush 必须在 pc_cjk_punct 之后（cjk 是唯一写盘 hook：--strict-then-fix-spaces
#    补空格后，批量成员才读文件；共享 git diff 类取数必须在 flush 时惰性算）。
# 2. flush 位置 = 已迁移成员中最后一个的原调用位之后、下一个非批量 checker 之前
#    ——stderr 全局输出顺序与迁移前逐位一致。
# 3. gate 名 / SKIP env / log_event 调用形态零改动（gen_hooks_readme 从调用形态
#    提 gate 名；dashboard 聚合按 gate 名）。
# 4. batching ≠ dedup：block 类每次写盘仍全量跑（节流窗口内第二处违规会漏拦）。
#
# 崩溃语义：runner 起不来 / 槽文件缺失 → 该槽 rc=1 + 空 all（等价今天 checker 进程
# 崩溃：ne0 类照拦、eq2/JSON 类照放）。判定协议差异全在各 pc_* 的 report 段消费，
# 批量层只搬运 rc + 合并输出字节流。

# ── 排队（无返回值；slot 名必须是 ^[A-Za-z0-9_]+$ 的字面量）─────────────
# _pc_enqueue <slot> <argv...>：argv = 今天 bash 会传给 python3 的原始参数
# （argv[0] = checker 脚本绝对路径，后续为 flag / 文件路径）。
_pc_enqueue() {
  local slot="$1"
  shift
  case "$slot" in
    ''|*[!A-Za-z0-9_]*) echo "pybatch: 非法槽名 '$slot'" >&2; return 1 ;;
  esac
  if [ -z "${_PC_SPOOL:-}" ]; then
    _PC_SPOOL=$(mktemp)
    _PC_SLOTS=""
  fi
  printf '%s\n%s\n' "$slot" "$#" >> "$_PC_SPOOL"
  printf '%s\n' "$@" >> "$_PC_SPOOL"
  _PC_SLOTS="${_PC_SLOTS}${_PC_SLOTS:+ }${slot}"
}

# ── 冲刷（dispatcher 固定位置调用；空队列零成本直接返回）────────────────
# 结果变量（供各 report 段消费）：
#   _PC_RC_<slot>     退出码（int）
#   _PC_ALL_<slot>    stdout+stderr 合并输出文件路径（等价今天的 $TMPOUT）
#   _PC_DUR_MS_<slot> 耗时毫秒
_pc_flush() {
  [ -n "${_PC_SPOOL:-}" ] && [ -f "$_PC_SPOOL" ] || return 0
  local out_dir slot rc dur all
  out_dir=$(mktemp -d)
  _PC_OUT_DIRS="${_PC_OUT_DIRS:-}${_PC_OUT_DIRS:+ }$out_dir"
  if ! python3 "$PROJECT_DIR/scripts/hook_py_batch.py" "$out_dir" < "$_PC_SPOOL" >/dev/null 2>&1; then
    echo "pybatch: runner 失败，全部槽按 rc=1 处理（等价各 checker 进程崩溃）" >&2
  fi
  # slot 名经 _pc_enqueue 白名单校验（^[A-Za-z0-9_]+$），rc/dur 读入后再过整数校验，
  # eval 间接赋值无注入面（bash 3.2 无关联数组的等价写法）
  for slot in $_PC_SLOTS; do
    all="$out_dir/${slot}.all"
    rc=1
    dur=0
    if [ -f "$out_dir/${slot}.rc" ]; then
      read -r rc < "$out_dir/${slot}.rc"
      case "$rc" in ''|*[!0-9-]*) rc=1 ;; esac
    fi
    if [ -f "$out_dir/${slot}.dur" ]; then
      read -r dur < "$out_dir/${slot}.dur"
      case "$dur" in ''|*[!0-9]*) dur=0 ;; esac
    fi
    [ -f "$all" ] || : > "$all"
    eval "_PC_RC_${slot}=\"\$rc\""
    eval "_PC_DUR_MS_${slot}=\"\$dur\""
    eval "_PC_ALL_${slot}=\"\$all\""
  done
  rm -f "$_PC_SPOOL"
  _PC_SPOOL=""
  _PC_SLOTS=""
}

# ── 清扫（dispatcher 各出口调用；report 段消费完 .all 后各自 rm，这里兜底余项）──
_pc_cleanup() {
  [ -n "${_PC_ADDED_FILE:-}" ] && rm -f "$_PC_ADDED_FILE"
  _PC_ADDED_FILE=""
  local d
  for d in ${_PC_OUT_DIRS:-}; do
    [ -d "$d" ] && rm -rf "$d"
  done
  _PC_OUT_DIRS=""
}
